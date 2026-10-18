package com.hkdaily.places.controller;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@Controller
public class SiteController {

    private final PlaceRepository placeRepository;

    public SiteController(PlaceRepository placeRepository) {
        this.placeRepository = placeRepository;
    }

    @GetMapping("/")
    public String index(Model model) {
        List<Place> places = placeRepository.findByStatusOrderByPublishedAtDesc(Place.Status.PUBLISHED);
        model.addAttribute("places", places.stream().limit(12).toList());
        model.addAttribute("pageTitle", "首頁");
        model.addAttribute("pageDesc", "每日香港好去處：精選香港行山徑、購物熱點同電影推介，每日更新。");
        return "index";
    }

    @GetMapping("/place/{slug}")
    public String detail(@PathVariable String slug, Model model) {
        Place place = placeRepository.findBySlugAndStatus(slug, Place.Status.PUBLISHED)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        model.addAttribute("place", place);
        model.addAttribute("pageTitle", place.getTitle());
        model.addAttribute("pageDesc", excerpt(place.getDescription(), 150));
        return "detail";
    }

    @GetMapping("/category/{name}")
    public String category(@PathVariable String name, Model model) {
        final Place.Category category;
        try {
            category = Place.Category.valueOf(name.toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        List<Place> places = placeRepository
                .findByCategoryAndStatusOrderByPublishedAtDesc(category, Place.Status.PUBLISHED);
        model.addAttribute("category", category);
        model.addAttribute("places", places);
        model.addAttribute("pageTitle", category.getDisplayName());
        model.addAttribute("pageDesc", "香港" + category.getDisplayName() + "好去處精選，一文睇晒推介。");
        return "category";
    }

    @GetMapping("/api/hello")
    @ResponseBody
    public Map<String, String> hello() {
        return Map.of("message", "Hello from hk-daily-places", "service", "java");
    }

    private static String excerpt(String text, int max) {
        if (text == null) {
            return "";
        }
        String oneLine = text.replaceAll("\\s+", " ").trim();
        return oneLine.length() <= max ? oneLine : oneLine.substring(0, max) + "…";
    }
}
