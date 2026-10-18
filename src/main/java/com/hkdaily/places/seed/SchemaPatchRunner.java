package com.hkdaily.places.seed;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.Order;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;

/**
 * 一次性 schema 補丁：Hibernate ddl-auto=update 唔會改已存在 column 嘅 type，
 * 所以 image_url 由 varchar(255) 轉 TEXT 要用人手 DDL。
 * <p>
 * Idempotent：column 已經係 TEXT 的話，ALTER 係 no-op。
 * 跑喺所有 seeder 之前（@Order(-1)）。
 */
@Component
@Order(-1)
public class SchemaPatchRunner implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(SchemaPatchRunner.class);

    private final DataSource dataSource;

    public SchemaPatchRunner(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public void run(String... args) {
        try (Connection conn = dataSource.getConnection();
             Statement st = conn.createStatement()) {
            st.execute("ALTER TABLE places ALTER COLUMN image_url TYPE TEXT");
            log.info("SchemaPatch: places.image_url -> TEXT (ok)");
        } catch (Exception e) {
            log.warn("SchemaPatch: image_url alter skipped/failed: {}", e.getMessage());
        }
    }
}
