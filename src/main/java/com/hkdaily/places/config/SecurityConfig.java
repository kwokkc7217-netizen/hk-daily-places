package com.hkdaily.places.config;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.autoconfigure.security.servlet.PathRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfTokenRequestHandler;

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
                // Phase 3：每日 cron 內部 API（controller 入面再用 DAILY_JOB_TOKEN 驗）
                .requestMatchers("/api/internal/**").permitAll()
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
            .csrf(csrf -> {
                CsrfTokenRequestHandler spaHandler = (request, response, csrfToken) ->
                        csrfToken.get(); // 即時 resolve，CookieCsrfTokenRepository 就會寫 Set-Cookie
                csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                        // 每個 response 都即時派 XSRF-TOKEN cookie
                        // （唔加呢行，純 API 嘅 401 回應係唔會 set cookie，React 拎唔到 token 去 login）
                        .csrfTokenRequestHandler(spaHandler)
                        // /api/internal 係 machine-to-machine（X-Job-Token 認證，唔靠 browser cookie），
                        // 豁免 CSRF——唔豁免嘅話 cron 冇 CSRF token 會食 403，連 controller 都入唔到
                        .ignoringRequestMatchers("/api/internal/**");
            });
        return http.build();
    }
}
