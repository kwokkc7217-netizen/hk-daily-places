package com.hkdaily.places.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

/**
 * 公開頁 analytics：由 Render 環境變數 GA4_MEASUREMENT_ID 讀 GA4 ID，
 * 未設定就傳空字串，layout.html 唔會輸出 gtag snippet（零副作用）。
 */
@ControllerAdvice(assignableTypes = SiteController.class)
public class AnalyticsAdvice {

    private final String ga4Id;

    public AnalyticsAdvice(@Value("${GA4_MEASUREMENT_ID:}") String ga4Id) {
        this.ga4Id = ga4Id == null ? "" : ga4Id.trim();
    }

    @ModelAttribute("ga4Id")
    public String ga4Id() {
        return ga4Id;
    }
}
