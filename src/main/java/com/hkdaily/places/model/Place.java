package com.hkdaily.places.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

/**
 * 一個好去處（行山 / 購物 / 睇戲）。
 * Public 頁只會顯示 status = PUBLISHED 的記錄。
 */
@Entity
@Table(name = "places")
public class Place {

    public enum Category {
        HIKING("行山"),
        SHOPPING("購物"),
        MOVIE("睇戲"),
        FOOD("食乜嘢？");

        private final String displayName;

        Category(String displayName) {
            this.displayName = displayName;
        }

        public String getDisplayName() {
            return displayName;
        }
    }

    public enum Status {
        DRAFT,
        PUBLISHED
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String slug;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Category category;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status = Status.DRAFT;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    /** Google Map 搜尋字串，例如 "龍脊, 香港" */
    private String mapQuery;

    /** YouTube 影片 ID（可空），例如 "dQw4w9WgXcQ" */
    private String youtubeId;

    /** 圖片 URL（Wikimedia 那種 percent-encoded 長 URL 可以成 500+ 字元，所以用 TEXT） */
    @Column(columnDefinition = "TEXT")
    private String imageUrl;

    /**
     * 「你可能都鍾意」：Python recommender（tools/related/related.py，GitHub Action 每週跑）
     * 寫入嘅 related slugs JSON array，例如 ["slug-a","slug-b"]。可空，未計到就冇。
     */
    @Column(columnDefinition = "TEXT")
    private String relatedSlugs;

    private LocalDateTime publishedAt;

    private LocalDateTime createdAt;

    /** 瀏覽次數（detail 頁每次載入 +1） */
    // 注意：primitive long 會令 Hibernate 出 NOT NULL column，Postgres 唔俾喺有資料嘅表加 NOT NULL 又冇 default 嘅 column
    // （試過，開機炒 "contains null values"）。所以要俾個 DB default，等舊 row 自動補 0。
    @Column(nullable = false, columnDefinition = "bigint default 0")
    private long viewCount = 0;

    /** Content audit：最新一次 deterministic audit 嘅總分（0–100）。可空，未評分就係 NULL。 */
    // 注意：要用 wrapper Integer（可 null）——primitive int/long 會令 Hibernate 出 NOT NULL column，
    // Postgres 唔俾喺有資料嘅表加 NOT NULL 又冇 default 嘅 column（見上面 viewCount 嘅教訓）。
    private Integer auditScore;

    /** Content audit 狀態：PASS / NEEDS_IMPROVEMENT / FAIL / REVIEW_REQUIRED。可空，未評分就係 NULL。 */
    private String auditStatus;

    /** Content audit：呢個分數係幾時寫入嘅。可空，未評分就係 NULL。 */
    private LocalDateTime auditedAt;

    /** LLM qualitative audit：最新一次 LLM 評分嘅總分（0–100）。可空，未評分就係 NULL。 */
    // 注意：要用 wrapper Integer（可 null），理由同上面 auditScore 一樣。
    private Integer auditLlmScore;

    /** LLM qualitative audit：呢個分數係幾時寫入嘅。可空，未評分就係 NULL。
     * 唔可以用 auditedAt 嚟揀 LLM 要重評邊篇，因為 auditedAt 屬於 deterministic audit，
     * 每 30 日就會被重寫 — 冇自己嘅 timestamp，LLM selector 永遠分唔清邊篇幾時 LLM 評過。 */
    private LocalDateTime auditLlmAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSlug() {
        return slug;
    }

    public void setSlug(String slug) {
        this.slug = slug;
    }

    public Category getCategory() {
        return category;
    }

    public void setCategory(Category category) {
        this.category = category;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
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

    public String getMapQuery() {
        return mapQuery;
    }

    public void setMapQuery(String mapQuery) {
        this.mapQuery = mapQuery;
    }

    public String getYoutubeId() {
        return youtubeId;
    }

    public void setYoutubeId(String youtubeId) {
        this.youtubeId = youtubeId;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    public String getRelatedSlugs() {
        return relatedSlugs;
    }

    public void setRelatedSlugs(String relatedSlugs) {
        this.relatedSlugs = relatedSlugs;
    }

    public LocalDateTime getPublishedAt() {
        return publishedAt;
    }

    public void setPublishedAt(LocalDateTime publishedAt) {
        this.publishedAt = publishedAt;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public long getViewCount() {
        return viewCount;
    }

    public void setViewCount(long viewCount) {
        this.viewCount = viewCount;
    }

    public Integer getAuditScore() {
        return auditScore;
    }

    public void setAuditScore(Integer auditScore) {
        this.auditScore = auditScore;
    }

    public String getAuditStatus() {
        return auditStatus;
    }

    public void setAuditStatus(String auditStatus) {
        this.auditStatus = auditStatus;
    }

    public LocalDateTime getAuditedAt() {
        return auditedAt;
    }

    public void setAuditedAt(LocalDateTime auditedAt) {
        this.auditedAt = auditedAt;
    }

    public Integer getAuditLlmScore() {
        return auditLlmScore;
    }

    public void setAuditLlmScore(Integer auditLlmScore) {
        this.auditLlmScore = auditLlmScore;
    }

    public LocalDateTime getAuditLlmAt() {
        return auditLlmAt;
    }

    public void setAuditLlmAt(LocalDateTime auditLlmAt) {
        this.auditLlmAt = auditLlmAt;
    }
}
