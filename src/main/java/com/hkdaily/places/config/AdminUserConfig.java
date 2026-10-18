package com.hkdaily.places.config;

import com.hkdaily.places.repository.AdminUserRepository;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * CMS 管理員帳號：DB-backed（admin_users 表），密碼用 BCrypt hash 儲存。
 * <p>
 * 第一位管理員由 AdminUserSeeder 用 ADMIN_USERNAME / ADMIN_PASSWORD
 * 環境變數一次性建立；之後喺 CMS「管理員」頁新增／刪除／改密碼，
 * env 變數可以刪走。
 */
@Configuration
public class AdminUserConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public UserDetailsService userDetailsService(AdminUserRepository adminUserRepository) {
        return username -> adminUserRepository.findByUsername(username)
                .map(u -> User.withUsername(u.getUsername())
                        .password(u.getPasswordHash())
                        .roles(u.getRole())
                        .build())
                .orElseThrow(() -> new UsernameNotFoundException("Admin not found: " + username));
    }
}
