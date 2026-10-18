package com.hkdaily.places.repository;

import com.hkdaily.places.model.Place;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PlaceRepository extends JpaRepository<Place, Long> {

    List<Place> findByStatusOrderByPublishedAtDesc(Place.Status status);

    Optional<Place> findBySlug(String slug);

    Optional<Place> findBySlugAndStatus(String slug, Place.Status status);

    List<Place> findByCategoryAndStatusOrderByPublishedAtDesc(Place.Category category, Place.Status status);
}
