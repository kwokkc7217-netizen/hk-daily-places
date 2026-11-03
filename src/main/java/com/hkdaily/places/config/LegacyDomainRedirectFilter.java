package com.hkdaily.places.config;

import java.io.IOException;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * 301 redirect from the legacy Render domain to the owned domain.
 *
 * hk-daily-places.onrender.com (Render free tier) sleeps after ~15 min idle and
 * takes ~2 min to cold-start — too slow as a public entry point. Redirect every
 * human-facing page to https://hkdailyplaces.win (EC2, always on).
 *
 * /api/** is excluded: the daily publisher cron POSTs to /api/internal/places
 * on this host, and API clients must not be redirected.
 *
 * Only triggers on the onrender host, so the EC2 / duckdns deployments are
 * unaffected.
 */
@Component
public class LegacyDomainRedirectFilter extends OncePerRequestFilter {

    private static final String LEGACY_HOST = "hk-daily-places.onrender.com";
    private static final String PRIMARY_BASE = "https://hkdailyplaces.win";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String host = request.getServerName();
        String path = request.getRequestURI();
        if (LEGACY_HOST.equalsIgnoreCase(host) && !path.startsWith("/api/")) {
            String query = request.getQueryString();
            String target = PRIMARY_BASE + path + (query != null ? "?" + query : "");
            response.setStatus(HttpStatus.MOVED_PERMANENTLY.value());
            response.setHeader("Location", target);
            return;
        }
        chain.doFilter(request, response);
    }
}
