package com.hkdaily.places.service;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.model.PlaceSearchDoc;
import com.hkdaily.places.repository.PlaceRepository;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;

/**
 * 開機 reconcile：將 Postgres 全部 PUBLISHED 同 Mongo search index 對齊。
 * - 新 place → upsert（save by _id，idempotent）
 * - Postgres 冇咗嘅 slug → 由 index 刪除
 * 每日 cron／CMS 嘅 dual-write 會 keep 住之後嘅同步，呢度淨係補歷史數同埋執漏。
 */
@Component
public class SearchIndexBackfill implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(SearchIndexBackfill.class);

    private final PlaceRepository placeRepository;
    private final PlaceSearchService searchService;
    private final org.springframework.beans.factory.ObjectProvider<MongoTemplate> mongoTemplateProvider;

    public SearchIndexBackfill(PlaceRepository placeRepository,
                               PlaceSearchService searchService,
                               org.springframework.beans.factory.ObjectProvider<MongoTemplate> mongoTemplateProvider) {
        this.placeRepository = placeRepository;
        this.searchService = searchService;
        this.mongoTemplateProvider = mongoTemplateProvider;
    }

    @Override
    public void run(ApplicationArguments args) {
        MongoTemplate mt = mongoTemplateProvider.getIfAvailable();
        if (mt == null) {
            return;
        }
        try {
            List<Place> published = placeRepository.findByStatusOrderByPublishedAtDesc(Place.Status.PUBLISHED);
            for (Place p : published) {
                searchService.indexPlace(p);
            }
            Set<String> slugs = published.stream()
                    .map(Place::getSlug)
                    .collect(Collectors.toSet());
            mt.remove(Query.query(Criteria.where("_id").nin(slugs)), PlaceSearchDoc.class);
            log.info("Search index reconciled: {} places", published.size());
        } catch (Exception e) {
            log.warn("Search index backfill skipped", e);
        }
    }
}
