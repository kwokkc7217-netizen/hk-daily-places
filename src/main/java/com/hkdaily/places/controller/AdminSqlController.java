package com.hkdaily.places.controller;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * CMS 數據庫 console（phpMyAdmin 式）：直接執行 SQL。
 * <p>
 * 已經係 ADMIN 先入到（見 SecurityConfig）；再加三重保險：
 * 一次只准一句（唔俾分號串多句）、SELECT 限 500 列、錯誤只回訊息唔回 stack trace。
 * <p>
 * 注意：呢度打嘅每一句都會即時喺 production DB 執行，冇 undo。
 */
@RestController
@RequestMapping("/api/admin")
public class AdminSqlController {

    private final JdbcTemplate jdbcTemplate;

    public AdminSqlController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostMapping("/sql")
    public ResponseEntity<Map<String, Object>> run(@RequestBody Map<String, String> body) {
        String sql = body == null ? null : body.get("sql");
        if (sql == null || sql.isBlank()) {
            return badRequest("SQL 不可為空");
        }
        sql = sql.strip();
        // 容許句尾一個分號，之後仲有分號就當係想串多句，拒絕
        if (sql.endsWith(";")) {
            sql = sql.substring(0, sql.length() - 1).strip();
        }
        if (sql.contains(";")) {
            return badRequest("一次只可執行一句 SQL");
        }
        if (sql.isEmpty()) {
            return badRequest("SQL 不可為空");
        }

        String head = sql.substring(0, Math.min(6, sql.length())).toLowerCase();
        try {
            if (head.startsWith("select") || head.startsWith("with")) {
                jdbcTemplate.setMaxRows(500);
                List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql);
                List<String> columns = rows.isEmpty()
                        ? List.of()
                        : new ArrayList<>(rows.get(0).keySet());
                return ResponseEntity.ok(Map.of(
                        "type", "select",
                        "columns", columns,
                        "rows", rows,
                        "rowCount", rows.size()));
            }
            int n = jdbcTemplate.update(sql);
            return ResponseEntity.ok(Map.of(
                    "type", "update",
                    "updated", n));
        } catch (DataAccessException e) {
            Throwable cause = e.getMostSpecificCause();
            String msg = cause != null && cause.getMessage() != null
                    ? cause.getMessage()
                    : (e.getMessage() != null ? e.getMessage() : "SQL 執行失敗");
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", msg));
        }
    }

    private static ResponseEntity<Map<String, Object>> badRequest(String msg) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", msg));
    }
}
