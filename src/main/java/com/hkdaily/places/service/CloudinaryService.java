package com.hkdaily.places.service;

import com.cloudinary.Cloudinary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Cloudinary 圖片上傳。
 * <p>
 * CLOUDINARY_URL 格式：cloudinary://API_KEY:API_SECRET@CLOUD_NAME
 * （去 cloudinary.com console → Dashboard 攞）。
 * 冇設嘅話 isConfigured() 係 false，upload 會掟 IllegalStateException，
 * AdminApiController 會將佢轉做 503——CMS 照用得，改為人手貼圖片 URL。
 */
@Service
public class CloudinaryService {

    private final Cloudinary cloudinary;

    public CloudinaryService(@Value("${CLOUDINARY_URL:}") String url) {
        this.cloudinary = (url == null || url.isBlank()) ? null : new Cloudinary(url);
    }

    public boolean isConfigured() {
        return cloudinary != null;
    }

    /**
     * @return 圖片嘅 secure_url（CDN 連結）
     */
    public String upload(byte[] bytes) throws Exception {
        if (cloudinary == null) {
            throw new IllegalStateException("CLOUDINARY_URL not configured");
        }
        Map<?, ?> result = cloudinary.uploader().upload(bytes, Map.of("folder", "hk-daily-places"));
        Object secureUrl = result.get("secure_url");
        return secureUrl == null ? null : secureUrl.toString();
    }
}
