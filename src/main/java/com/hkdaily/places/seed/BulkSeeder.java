package com.hkdaily.places.seed;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 200 篇 bulk seed（src/main/resources/seed/bulk-places.json）。
 * 用 slug 做 idempotent upsert：已存在就 skip，淨係補返未有嘅。
 * 第一次 deploy 會一次過入 200 篇，之後再跑唔會重複。
 */
@Component
@Order(3)
public class BulkSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(BulkSeeder.class);

    private final PlaceRepository placeRepository;
    private final ObjectMapper objectMapper;

    public BulkSeeder(PlaceRepository placeRepository, ObjectMapper objectMapper) {
        this.placeRepository = placeRepository;
        this.objectMapper = objectMapper;
    }

    @Override
    public void run(String... args) throws Exception {
        List<Map<String, Object>> entries;
        try (InputStream in = getClass().getResourceAsStream("/seed/bulk-places.json")) {
            if (in == null) {
                log.warn("bulk-places.json not found, skipping bulk seed");
                return;
            }
            entries = objectMapper.readValue(in, new TypeReference<>() {});
        }
        int inserted = 0;
        for (Map<String, Object> e : entries) {
            String slug = str(e.get("slug"));
            if (slug.isEmpty() || placeRepository.findBySlug(slug).isPresent()) {
                continue;
            }
            try {
                Place p = new Place();
                p.setSlug(slug);
                p.setTitle(str(e.get("title")));
                p.setDescription(str(e.get("description")));
                p.setCategory(Place.Category.valueOf(str(e.get("category"))));
                p.setStatus(Place.Status.PUBLISHED);
                p.setMapQuery(strOrNull(e.get("mapQuery")));
                p.setYoutubeId(strOrNull(e.get("youtubeId")));
                p.setImageUrl(strOrNull(e.get("imageUrl")));
                p.setPublishedAt(LocalDateTime.parse(str(e.get("publishedAt"))));
                Object vc = e.get("viewCount");
                p.setViewCount(vc instanceof Number n ? n.longValue() : 0L);
                placeRepository.save(p);
                inserted++;
            } catch (Exception ex) {
                // 單篇壞唔好拖累成個 boot：記低，繼續下一篇
                log.warn("BulkSeeder: skipped slug '{}': {}", slug, ex.getMessage());
            }
        }
        log.info("BulkSeeder: inserted {} new places ({} total in file)", inserted, entries.size());
    }

    private static String str(Object o) {
        return o == null ? "" : o.toString().strip();
    }

    private static String strOrNull(Object o) {
        if (o == null) {
            return null;
        }
        String s = o.toString().strip();
        return s.isEmpty() ? null : s;
    }
}
