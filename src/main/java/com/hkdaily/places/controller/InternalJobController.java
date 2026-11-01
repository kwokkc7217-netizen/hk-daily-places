package com.hkdaily.places.controller;

import com.hkdaily.places.model.MapLocation;
import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.MapLocationRepository;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * Phase 3：每日 cron 專用內部 API（唔經 admin session）。
 * <p>
 * 認證用 env DAILY_JOB_TOKEN：request header X-Job-Token 要對得上，否則 401；
 * 未設 DAILY_JOB_TOKEN 就成個 endpoint 停用（503）。
 * <p>
 * 成功會直接 PUBLISH（唔經草稿）——call 之前請自行 verify 圖片 URL 回 200。
 * <p>
 * FOOD 食肆可以帶 branches（每間分店：branchName＋latitude＋longitude 必填，address 選填），
 * 會同個 place 同一個 transaction 入 map_locations。
 */
@RestController
@RequestMapping("/api/internal")
public class InternalJobController {

    private final PlaceRepository placeRepository;
    private final MapLocationRepository mapLocationRepository;
    private final String jobToken;

    public InternalJobController(PlaceRepository placeRepository,
                                 MapLocationRepository mapLocationRepository,
                                 @Value("${DAILY_JOB_TOKEN:}") String jobToken) {
        this.placeRepository = placeRepository;
        this.mapLocationRepository = mapLocationRepository;
        this.jobToken = jobToken;
    }

    /** 一間分店（FOOD 用）。經緯度必填——geocode 唔到就唔好 publish，寧缺勿錯。 */
    public static class BranchDto {
        public String branchName;
        public String address;
        public Double latitude;
        public Double longitude;
    }

    /** 發佈請求：同以前一樣 flat field，加多個選填嘅 branches。 */
    public static class PublishRequest {
        public String slug;
        public String title;
        public String description;
        public Place.Category category;
        public String mapQuery;
        public String youtubeId;
        public String imageUrl;
        public List<BranchDto> branches;
    }

    @PostMapping("/places")
    @Transactional
    public ResponseEntity<?> publish(
            @RequestHeader(value = "X-Job-Token", required = false) String token,
            @RequestBody PublishRequest input) {
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
        if (input == null
                || input.slug == null || input.slug.isBlank()
                || input.title == null || input.title.isBlank()
                || input.description == null || input.description.isBlank()
                || input.category == null) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "slug/title/description/category required"));
        }
        if (input.branches != null) {
            for (BranchDto b : input.branches) {
                if (b == null || b.branchName == null || b.branchName.isBlank()
                        || b.latitude == null || b.longitude == null) {
                    return ResponseEntity.badRequest()
                            .body(Map.of("error", "each branch needs branchName + latitude + longitude"));
                }
            }
        }
        String slug = input.slug.strip();
        if (placeRepository.findBySlug(slug).isPresent()) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "slug exists"));
        }
        Place place = new Place();
        place.setSlug(slug);
        place.setTitle(input.title.strip());
        place.setDescription(input.description);
        place.setCategory(input.category);
        place.setStatus(Place.Status.PUBLISHED);
        place.setMapQuery(input.mapQuery);
        place.setYoutubeId(input.youtubeId);
        place.setImageUrl(input.imageUrl);
        place.setPublishedAt(LocalDateTime.now());
        Place saved = placeRepository.save(place);
        if (input.branches != null) {
            for (BranchDto b : input.branches) {
                MapLocation loc = new MapLocation();
                loc.setPlace(saved);
                loc.setBranchName(b.branchName.strip());
                loc.setAddress(b.address);
                loc.setLatitude(b.latitude);
                loc.setLongitude(b.longitude);
                mapLocationRepository.save(loc);
            }
        }
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }
}
