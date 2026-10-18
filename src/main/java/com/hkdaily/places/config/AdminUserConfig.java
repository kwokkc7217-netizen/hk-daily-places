package com.hkdaily.places.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;

/**
 * CMS 管理員帳號：由環境變數 ADMIN_USERNAME / ADMIN_PASSWORD 讀入。
 * <p>
 * 兩個變數缺一不可——冇設就開機即炒（fail loudly），
 * 唔好靜靜哋用個預設密碼，嗰個先係真・保安漏洞。
 */
@Configuration
public class AdminUserConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public UserDetailsService userDetailsService(
            PasswordEncoder passwordEncoder,
            @Value("${ADMIN_USERNAME:}") String username,
            @Value("${ADMIN_PASSWORD:}") String password) {
        if (username == null || username.isBlank() || password == null || password.isBlank()) {
            throw new IllegalStateException("Set ADMIN_USERNAME and ADMIN_PASSWORD env vars");
        }
        UserDetails admin = User.withUsername(username)
                .password(passwordEncoder.encode(password))
                .roles("ADMIN")
                .build();
        return new InMemoryUserDetailsManager(admin);
    }
}
