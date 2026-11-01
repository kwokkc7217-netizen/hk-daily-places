package com.hkdaily.places.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

/**
 * 一間好去處嘅分店（主要畀 FOOD 食肆用，其他分類都用得）。
 * 地址用 Google Maps query URL 開，唔使 API key；有多個分店嗰陣，
 * detail 頁會用 Maps JavaScript API（GOOGLE_MAPS_API_KEY）一次過 show 晒所有 marker。
 */
@Entity
@Table(name = "map_locations")
public class MapLocation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "place_id", nullable = false)
    private Place place;

    /** 分店名，例如 "尖沙咀店" */
    @Column(nullable = false)
    private String branchName;

    /** 地址，例如 "尖沙咀棉登徑8號地下" */
    @Column(length = 500)
    private String address;

    /** 經緯度（research 嗰陣 geocode 返嚟先寫入，唔靠估） */
    private Double latitude;

    private Double longitude;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Place getPlace() {
        return place;
    }

    public void setPlace(Place place) {
        this.place = place;
    }

    public String getBranchName() {
        return branchName;
    }

    public void setBranchName(String branchName) {
        this.branchName = branchName;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public Double getLatitude() {
        return latitude;
    }

    public void setLatitude(Double latitude) {
        this.latitude = latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public void setLongitude(Double longitude) {
        this.longitude = longitude;
    }
}
