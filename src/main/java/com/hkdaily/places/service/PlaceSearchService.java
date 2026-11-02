package com.hkdaily.places.service;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.model.PlaceSearchDoc;
import com.hkdaily.places.repository.PlaceRepository;
import com.mongodb.client.MongoCollection;
import java.util.ArrayList;
import java.util.List;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;

/**
 * NoSQL search sidecar。
 * 正選：MongoDB Atlas Search（$search aggregation，有 relevance 排序）。
 * Mongo 冇設／斷線：自動跌返 Postgres ILIKE，唔會影響網站。
 * 所有 Mongo 操作都 catch 咗 exception——search index 永遠唔可以拖累主流程。
 */
@Service
public class PlaceSearchService {

    private static final Logger log = LoggerFactory.getLogger(PlaceSearchService.class);
    private static final String COLLECTION = "place_search";
    private static final int LIMIT = 50;

    private final PlaceRepository placeRepository;
    private final ObjectProvider<MongoTemplate> mongoTemplateProvider;

    public PlaceSearchService(PlaceRepository placeRepository,
                              ObjectProvider<MongoTemplate> mongoTemplateProvider) {
        this.placeRepository = placeRepository;
        this.mongoTemplateProvider = mongoTemplateProvider;
    }

    /** Mongo 有冇啟動（俾 backfill 同 health check 用）。 */
    public boolean isMongoEnabled() {
        return mongoTemplateProvider.getIfAvailable() != null;
    }

    /**
     * Publish／CMS save 之後 call：upsert 一份去 Mongo。
     * 失敗都唔 throw——寧願 search index 舊，都唔好整炒個 publish。
     */
    public void indexPlace(Place place) {
        MongoTemplate mt = mongoTemplateProvider.getIfAvailable();
        if (mt == null || place == null || place.getSlug() == null) {
            return;
        }
        try {
            PlaceSearchDoc doc = new PlaceSearchDoc();
            doc.setSlug(place.getSlug());
            doc.setTitle(place.getTitle());
            doc.setDescription(place.getDescription());
            doc.setCategory(place.getCategory() == null ? null : place.getCategory().name());
            doc.setPublishedAt(place.getPublishedAt());
            mt.save(doc);
        } catch (Exception e) {
            log.warn("Mongo index upsert failed, slug={}", place.getSlug(), e);
        }
    }

    /** CMS 刪除文章之後 call：順手清埋 search index。 */
    public void removeFromIndex(String slug) {
        MongoTemplate mt = mongoTemplateProvider.getIfAvailable();
        if (mt == null || slug == null) {
            return;
        }
        try {
            mt.remove(Query.query(Criteria.where("_id").is(slug)), PlaceSearchDoc.class);
        } catch (Exception e) {
            log.warn("Mongo index delete failed, slug={}", slug, e);
        }
    }

    public record SearchHit(String slug, String title, String description,
                              String category, String categoryDisplay) {
    }

    private static String displayName(String categoryName) {
        if (categoryName == null) {
            return "";
        }
        try {
            return Place.Category.valueOf(categoryName).getDisplayName();
        } catch (IllegalArgumentException e) {
            return categoryName;
        }
    }

    /** 對外唯一入口：Atlas Search 正選，失敗跌返 Postgres。 */
    public List<SearchHit> search(String q) {
        MongoTemplate mt = mongoTemplateProvider.getIfAvailable();
        if (mt != null) {
            try {
                return mongoSearch(mt, q);
            } catch (Exception e) {
                log.warn("Atlas Search failed, falling back to Postgres", e);
            }
        }
        return postgresSearch(q);
    }

    private List<SearchHit> mongoSearch(MongoTemplate mt, String q) {
        MongoCollection<Document> coll = mt.getCollection(COLLECTION);
        List<Document> pipeline = List.of(
                new Document("$search", new Document("index", "default")
                        .append("text", new Document("query", q)
                                .append("path", List.of("title", "description")))),
                new Document("$limit", LIMIT));
        List<SearchHit> hits = new ArrayList<>();
        for (Document d : coll.aggregate(pipeline)) {
            String slug = d.getString("_id");
            if (slug == null) {
                continue;
            }
            String category = d.getString("category");
            hits.add(new SearchHit(
                    slug,
                    d.getString("title"),
                    d.getString("description"),
                    category,
                    displayName(category)));
        }
        return hits;
    }

    private List<SearchHit> postgresSearch(String q) {
        return placeRepository
                .searchPublished(Place.Status.PUBLISHED, q, PageRequest.of(0, LIMIT))
                .stream()
                .map(p -> {
                    String category = p.getCategory() == null ? null : p.getCategory().name();
                    return new SearchHit(
                            p.getSlug(), p.getTitle(), p.getDescription(),
                            category, displayName(category));
                })
                .toList();
    }
}
