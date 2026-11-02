package com.hkdaily.places.model;

import java.time.LocalDateTime;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

/**
 * MongoDB Atlas 嘅 search index 文件。
 * Postgres 先係 source of truth；呢度淨係 search 用嘅 denormalized 副本。
 * _id 直接用 Place.slug，所以 save() 即係 upsert。
 */
@Document(collection = "place_search")
public class PlaceSearchDoc {

    @Id
    private String slug;

    private String title;

    private String description;

    /** Place.Category.name()，例如 "FOOD" */
    private String category;

    private LocalDateTime publishedAt;

    public String getSlug() {
        return slug;
    }

    public void setSlug(String slug) {
        this.slug = slug;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public LocalDateTime getPublishedAt() {
        return publishedAt;
    }

    public void setPublishedAt(LocalDateTime publishedAt) {
        this.publishedAt = publishedAt;
    }
}
