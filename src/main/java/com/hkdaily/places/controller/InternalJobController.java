package com.hkdaily.places.controller;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * Phase 3：每日 cron 專用內部 API（唔經 admin session）。
 * <p>
 * 認證用 env DAILY_JOB_TOKEN：request header X-Job-Token 要對得上，否則 401；
 * 未設 DAILY_JOB_TOKEN 就成個 endpoint 停用（503）。
 * <p>
 * 成功會直接 PUBLISH（唔經草稿）——call 之前請自行 verify 圖片 URL 回 200。
 */
@RestController
@RequestMapping("/api/internal")
public class InternalJobController {

    private final PlaceRepository placeRepository;
    private final String jobToken;

    public InternalJobController(PlaceRepository placeRepository,
                                 @Value("${DAILY_JOB_TOKEN:}") String jobToken) {
        this.placeRepository = placeRepository;
        this.jobToken = jobToken;
    }

    @PostMapping("/places")
    public ResponseEntity<?> publish(
            @RequestHeader(value = "X-Job-Token", required = false) String token,
            @RequestBody Place input) {
        if (jobToken == null || jobToken.isBlank()) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of("error", "daily job not configured"));
        }
        if (token == null || !MessageDigest.isEqual(
                token.getBytes(StandardCharsets.UTF_8),
                jobToken.getBytes(StandardCharsets.UTF_8))) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "bad token"));
        }
        if (input.getSlug() == null || input.getSlug().isBlank()
                || input.getTitle() == null || input.getTitle().isBlank()
                || input.getDescription() == null || input.getDescription().isBlank()
                || input.getCategory() == null) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "slug/title/description/category required"));
        }
        String slug = input.getSlug().strip();
        if (placeRepository.findBySlug(slug).isPresent()) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "slug exists"));
        }
        Place place = new Place();
        place.setSlug(slug);
        place.setTitle(input.getTitle().strip());
        place.setDescription(input.getDescription());
        place.setCategory(input.getCategory());
        place.setStatus(Place.Status.PUBLISHED);
        place.setMapQuery(input.getMapQuery());
        place.setYoutubeId(input.getYoutubeId());
        place.setImageUrl(input.getImageUrl());
        place.setPublishedAt(LocalDateTime.now());
        return ResponseEntity.status(HttpStatus.CREATED).body(placeRepository.save(place));
    }
}
