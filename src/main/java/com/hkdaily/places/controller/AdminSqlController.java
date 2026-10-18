package com.hkdaily.places.controller;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * CMS 數據庫 console（phpMyAdmin 式）：直接執行 SQL。
 * <p>
 * 已經係 ADMIN 先入到（見 SecurityConfig）；再加幾重保險：
 * SELECT 限 500 列、錯誤只回訊息唔回 stack trace。
 * <p>
 * 支援一次貼多句（例如成份 INSERT dump）：會按分號切開、逐句執行，
 * 全部包喺同一個 transaction——任何一句失敗就 rollback 晒，唔會有 import 一半嘅狀態。
 * <p>
 * 注意：呢度打嘅每一句都會即時喺 production DB 執行，冇 undo。
 */
@RestController
@RequestMapping("/api/admin")
public class AdminSqlController {

    private final JdbcTemplate jdbcTemplate;
    private final TransactionTemplate transactionTemplate;

    public AdminSqlController(JdbcTemplate jdbcTemplate,
                              PlatformTransactionManager transactionManager) {
        this.jdbcTemplate = jdbcTemplate;
        this.transactionTemplate = new TransactionTemplate(transactionManager);
    }

    @PostMapping("/sql")
    public ResponseEntity<Map<String, Object>> run(@RequestBody Map<String, String> body) {
        String sql = body == null ? null : body.get("sql");
        if (sql == null || sql.isBlank()) {
            return badRequest("SQL 不可為空", -1);
        }
        final List<String> statements;
        try {
            statements = splitStatements(sql);
        } catch (IllegalArgumentException e) {
            return badRequest(e.getMessage(), -1);
        }
        if (statements.isEmpty()) {
            return badRequest("SQL 不可為空", -1);
        }

        final List<Map<String, Object>> results = new ArrayList<>();
        try {
            transactionTemplate.executeWithoutResult(status -> {
                for (int i = 0; i < statements.size(); i++) {
                    results.add(executeOne(statements.get(i), i));
                }
            });
        } catch (DataAccessException e) {
            // transaction 已 rollback；results 入面係失敗前成功嗰啲（實際冇寫入）
            return badRequest(specificMessage(e), results.size());
        }

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("statements", statements.size());
        resp.put("results", results);
        return ResponseEntity.ok(resp);
    }

    private Map<String, Object> executeOne(String st, int index) {
        String head = st.substring(0, Math.min(6, st.length())).toLowerCase();
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("index", index);
        if (head.startsWith("select") || head.startsWith("with")) {
            jdbcTemplate.setMaxRows(500);
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(st);
            List<String> columns = rows.isEmpty()
                    ? List.of()
                    : new ArrayList<>(rows.get(0).keySet());
            r.put("type", "select");
            r.put("columns", columns);
            r.put("rows", rows);
            r.put("rowCount", rows.size());
        } else {
            int n = jdbcTemplate.update(st);
            r.put("type", "update");
            r.put("updated", n);
        }
        return r;
    }

    /**
     * 將多句 SQL 按分號切開，但唔會切斷：
     * 單引號字串入面（'a;b'，含 '' escape）、雙引號 identifier 入面（"a;b"）、
     * -- 行 comment 同 /* 塊 comment 入面嘅分號。
     * 注意：唔識處理 PostgreSQL dollar-quoting（$$ ... $$），function body 請分開執行。
     */
    static List<String> splitStatements(String sql) {
        List<String> out = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        int i = 0;
        int n = sql.length();
        char quote = 0; // 0 = 唔喺字串入面，否則係 ' 或 "
        while (i < n) {
            char c = sql.charAt(i);
            if (quote != 0) {
                cur.append(c);
                if (c == quote) {
                    if (i + 1 < n && sql.charAt(i + 1) == quote) {
                        cur.append(quote); // '' escape，唔算閂咗
                        i += 2;
                        continue;
                    }
                    quote = 0;
                }
                i++;
                continue;
            }
            if (c == '\'' || c == '"') {
                quote = c;
                cur.append(c);
                i++;
                continue;
            }
            if (c == '-' && i + 1 < n && sql.charAt(i + 1) == '-') {
                while (i < n && sql.charAt(i) != '\n') {
                    cur.append(sql.charAt(i));
                    i++;
                }
                continue;
            }
            if (c == '/' && i + 1 < n && sql.charAt(i + 1) == '*') {
                cur.append("/*");
                i += 2;
                while (i < n && !(sql.charAt(i) == '*' && i + 1 < n && sql.charAt(i + 1) == '/')) {
                    cur.append(sql.charAt(i));
                    i++;
                }
                if (i < n) {
                    cur.append("*/");
                    i += 2;
                }
                continue;
            }
            if (c == ';') {
                String stmt = cur.toString().strip();
                if (!stmt.isEmpty()) {
                    out.add(stmt);
                }
                cur.setLength(0);
                i++;
                continue;
            }
            cur.append(c);
            i++;
        }
        if (quote != 0) {
            throw new IllegalArgumentException("SQL 引號未閉合：有個 ' 或 \" 未閂");
        }
        String tail = cur.toString().strip();
        if (!tail.isEmpty()) {
            out.add(tail);
        }
        return out;
    }

    private static String specificMessage(DataAccessException e) {
        Throwable cause = e.getMostSpecificCause();
        if (cause != null && cause.getMessage() != null) {
            return cause.getMessage();
        }
        return e.getMessage() != null ? e.getMessage() : "SQL 執行失敗";
    }

    private static ResponseEntity<Map<String, Object>> badRequest(String msg, int failedAt) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("error", msg);
        body.put("failedAt", failedAt); // 0-based；-1 = 未開始執行
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }
}
