package com.hkdaily.places.repository;

import com.hkdaily.places.model.MapLocation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

public interface MapLocationRepository extends JpaRepository<MapLocation, Long> {
    List<MapLocation> findByPlaceIdOrderById(Long placeId);

    /** 刪 post 嗰陣一齊清分店（FK 唔俾剩低孤兒 row）。 */
    @Modifying
    @Transactional
    void deleteByPlaceId(Long placeId);
}
