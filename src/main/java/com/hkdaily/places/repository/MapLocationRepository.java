package com.hkdaily.places.repository;

import com.hkdaily.places.model.MapLocation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface MapLocationRepository extends JpaRepository<MapLocation, Long> {
    List<MapLocation> findByPlaceIdOrderById(Long placeId);
}
