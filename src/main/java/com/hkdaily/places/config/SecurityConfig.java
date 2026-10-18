package com.hkdaily.places.config;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.autoconfigure.security.servlet.PathRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;

/**
 * Phase 2：CMS 登入保護。
 * <p>
 * 公開頁（首頁、詳情、分類）同 React CMS 個殼（/admin/**）唔使登入；
 * 真正嘅資料 API（/api/admin/**）要 ADMIN 先用到。
 * 登入/登出/401 全部行 JSON（唔 redirect），方便 React fetch。
 */
@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(PathRequest.toStaticResources().atCommonLocations()).permitAll()
                .requestMatchers("/", "/place/**", "/category/**", "/api/hello", "/ads.txt", "/error").permitAll()
                .requestMatchers("/admin/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().denyAll()
            )
            .formLogin(form -> form
                .loginProcessingUrl("/api/admin/login")
                .successHandler((req, res, authentication) -> {
                    res.setStatus(HttpServletResponse.SC_OK);
                    res.setContentType("application/json;charset=UTF-8");
                    res.getWriter().write("{\"ok\":true}");
                })
                .failureHandler((req, res, exception) -> {
                    res.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                    res.setContentType("application/json;charset=UTF-8");
                    res.getWriter().write("{\"ok\":false}");
                })
            )
            .logout(logout -> logout
                .logoutUrl("/api/admin/logout")
                .logoutSuccessHandler((req, res, authentication) -> {
                    res.setStatus(HttpServletResponse.SC_OK);
                    res.setContentType("application/json;charset=UTF-8");
                    res.getWriter().write("{\"ok\":true}");
                })
            )
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint((req, res, exception) ->
                    res.sendError(HttpServletResponse.SC_UNAUTHORIZED))
            )
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            );
        return http.build();
    }
}
