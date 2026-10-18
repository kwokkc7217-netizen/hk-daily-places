package com.hkdaily.places.repository;

import com.hkdaily.places.model.Place;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface PlaceRepository extends JpaRepository<Place, Long> {

    List<Place> findByStatusOrderByPublishedAtDesc(Place.Status status);

    Page<Place> findByStatus(Place.Status status, Pageable pageable);

    Page<Place> findByCategoryAndStatus(Place.Category category, Place.Status status, Pageable pageable);

    Optional<Place> findBySlug(String slug);

    Optional<Place> findBySlugAndStatus(String slug, Place.Status status);

    List<Place> findByCategoryAndStatusOrderByPublishedAtDesc(Place.Category category, Place.Status status);

    @Modifying
    @Query("UPDATE Place p SET p.viewCount = p.viewCount + 1 WHERE p.id = :id")
    void incrementViewCount(@Param("id") Long id);
}
