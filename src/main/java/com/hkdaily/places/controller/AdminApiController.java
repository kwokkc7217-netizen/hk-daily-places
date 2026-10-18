package com.hkdaily.places.controller;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import com.hkdaily.places.service.CloudinaryService;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * CMS 專用 REST API（全部要 ADMIN，見 SecurityConfig）。
 * Public 頁唔用呢度——佢哋行 Thymeleaf server-render。
 */
@RestController
@RequestMapping("/api/admin")
public class AdminApiController {

    private final PlaceRepository placeRepository;
    private final CloudinaryService cloudinaryService;

    public AdminApiController(PlaceRepository placeRepository, CloudinaryService cloudinaryService) {
        this.placeRepository = placeRepository;
        this.cloudinaryService = cloudinaryService;
    }

    /** 證明個 session work（React 一開波就 call 呢個） */
    @GetMapping("/me")
    public Map<String, String> me(Authentication auth) {
        return Map.of("username", auth.getName());
    }

    /** CMS 睇晒：草稿都出 */
    @GetMapping("/places")
    public List<Place> list() {
        return placeRepository.findAll(Sort.by(Sort.Direction.DESC, "id"));
    }

    @GetMapping("/places/{id}")
    public Place get(@PathVariable Long id) {
        return placeRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    @PostMapping("/places")
    public Place create(@RequestBody Place input) {
        Place place = copyInto(new Place(), input);
        stampPublishedAt(place);
        return placeRepository.save(place);
    }

    @PutMapping("/places/{id}")
    public Place update(@PathVariable Long id, @RequestBody Place input) {
        Place place = placeRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        copyInto(place, input);
        stampPublishedAt(place);
        return placeRepository.save(place);
    }

    @DeleteMapping("/places/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        Place place = placeRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        placeRepository.delete(place);
        return ResponseEntity.noContent().build();
    }

    /** 圖片上傳去 Cloudinary；冇設 CLOUDINARY_URL 就回 503 */
    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> upload(@RequestParam("file") MultipartFile file) {
        try {
            if (file.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of("error", "empty file"));
            }
            String url = cloudinaryService.upload(file.getBytes());
            if (url == null) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("error", "upload failed"));
            }
            return ResponseEntity.ok(Map.of("url", url));
        } catch (IllegalStateException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of("error", "image upload not configured"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "upload failed"));
        }
    }

    private Place copyInto(Place target, Place input) {
        target.setSlug(input.getSlug());
        target.setTitle(input.getTitle());
        target.setDescription(input.getDescription());
        if (input.getCategory() != null) {
            target.setCategory(input.getCategory());
        }
        if (input.getStatus() != null) {
            target.setStatus(input.getStatus());
        }
        target.setMapQuery(input.getMapQuery());
        target.setYoutubeId(input.getYoutubeId());
        target.setImageUrl(input.getImageUrl());
        if (input.getPublishedAt() != null) {
            target.setPublishedAt(input.getPublishedAt());
        }
        return target;
    }

    private void stampPublishedAt(Place place) {
        if (place.getStatus() == Place.Status.PUBLISHED && place.getPublishedAt() == null) {
            place.setPublishedAt(LocalDateTime.now());
        }
    }
}
