package com.hkdaily.places.seed;

import com.hkdaily.places.model.AdminUser;
import com.hkdaily.places.repository.AdminUserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * 一次性 bootstrap：admin_users 表空嘅時候，用環境變數
 * ADMIN_USERNAME / ADMIN_PASSWORD 建立第一位管理員（密碼即刻 BCrypt 加密）。
 * <p>
 * 之後喺 CMS「管理員」頁管理帳號，呢兩個 env 可以刪走。
 * 冇 admin 又冇 env 嘅話，只係記個 WARN 唔炒機——
 * CMS login 暫時用唔到，直至有人 set 返 env 重新 deploy。
 */
@Component
@Order(1)
public class AdminUserSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(AdminUserSeeder.class);

    private final AdminUserRepository adminUserRepository;
    private final PasswordEncoder passwordEncoder;
    private final String bootstrapUsername;
    private final String bootstrapPassword;

    public AdminUserSeeder(AdminUserRepository adminUserRepository,
                           PasswordEncoder passwordEncoder,
                           @Value("${ADMIN_USERNAME:}") String bootstrapUsername,
                           @Value("${ADMIN_PASSWORD:}") String bootstrapPassword) {
        this.adminUserRepository = adminUserRepository;
        this.passwordEncoder = passwordEncoder;
        this.bootstrapUsername = bootstrapUsername;
        this.bootstrapPassword = bootstrapPassword;
    }

    @Override
    public void run(String... args) {
        if (adminUserRepository.count() > 0) {
            return;
        }
        if (bootstrapUsername == null || bootstrapUsername.isBlank()
                || bootstrapPassword == null || bootstrapPassword.isBlank()) {
            log.warn("No admin users exist and ADMIN_USERNAME/ADMIN_PASSWORD not set — "
                    + "CMS login unavailable until bootstrap env vars are set");
            return;
        }
        AdminUser admin = new AdminUser();
        admin.setUsername(bootstrapUsername.strip());
        admin.setPasswordHash(passwordEncoder.encode(bootstrapPassword));
        admin.setRole("ADMIN");
        adminUserRepository.save(admin);
        log.info("Bootstrapped initial admin user '{}'", bootstrapUsername.strip());
    }
}
