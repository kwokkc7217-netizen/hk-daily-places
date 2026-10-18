package com.hkdaily.places.controller;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;
import java.util.Set;

/**
 * 公開頁：首頁 / 分類 / 詳情。
 * 列表支援分頁（每頁 12 篇）同排序（最新 / 最早 / 最多人睇）。
 * 詳情頁每次載入會將 viewCount +1（影響「最多人睇」排序）。
 */
@Controller
public class SiteController {

    private static final int PAGE_SIZE = 12;
    private static final Set<String> SORT_KEYS = Set.of("newest", "oldest", "popular");

    private final PlaceRepository placeRepository;

    public SiteController(PlaceRepository placeRepository) {
        this.placeRepository = placeRepository;
    }

    @GetMapping("/")
    public String index(@RequestParam(defaultValue = "0") int page,
                        @RequestParam(defaultValue = "newest") String sort,
                        Model model) {
        Page<Place> places = findPlaces(null, page, sort);
        model.addAttribute("places", places);
        model.addAttribute("currentPage", places.getNumber());
        model.addAttribute("sort", sortKey(sort));
        model.addAttribute("baseUrl", "/");
        model.addAttribute("pageTitle", "首頁");
        model.addAttribute("pageDesc", "每日香港好去處：精選香港行山徑、購物熱點同電影推介，每日更新。");
        return "index";
    }

    @GetMapping("/category/{name}")
    public String category(@PathVariable String name,
                           @RequestParam(defaultValue = "0") int page,
                           @RequestParam(defaultValue = "newest") String sort,
                           Model model) {
        final Place.Category category;
        try {
            category = Place.Category.valueOf(name.toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        Page<Place> places = findPlaces(category, page, sort);
        model.addAttribute("category", category);
        model.addAttribute("places", places);
        model.addAttribute("currentPage", places.getNumber());
        model.addAttribute("sort", sortKey(sort));
        model.addAttribute("baseUrl", "/category/" + name.toLowerCase());
        model.addAttribute("pageTitle", category.getDisplayName());
        model.addAttribute("pageDesc", "香港" + category.getDisplayName() + "好去處精選，一文睇晒推介。");
        return "category";
    }

    @GetMapping("/place/{slug}")
    @Transactional
    public String detail(@PathVariable String slug, Model model) {
        Place place = placeRepository.findBySlugAndStatus(slug, Place.Status.PUBLISHED)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        placeRepository.incrementViewCount(place.getId());
        model.addAttribute("place", place);
        model.addAttribute("pageTitle", place.getTitle());
        model.addAttribute("pageDesc", excerpt(place.getDescription(), 150));
        return "detail";
    }

    @GetMapping("/api/hello")
    @ResponseBody
    public Map<String, String> hello() {
        return Map.of("message", "Hello from hk-daily-places", "service", "java");
    }

    /** 分頁查詢：sort 非法就用 newest；page 超出範圍就 clamp 去最後一頁。 */
    private Page<Place> findPlaces(Place.Category category, int page, String sort) {
        String key = sortKey(sort);
        Sort sortObj = sortOf(key);
        int p = Math.max(page, 0);
        Page<Place> result = query(category, PageRequest.of(p, PAGE_SIZE, sortObj));
        int totalPages = result.getTotalPages();
        if (totalPages > 0 && p >= totalPages) {
            result = query(category, PageRequest.of(totalPages - 1, PAGE_SIZE, sortObj));
        }
        return result;
    }

    private Page<Place> query(Place.Category category, Pageable pageable) {
        if (category == null) {
            return placeRepository.findByStatus(Place.Status.PUBLISHED, pageable);
        }
        return placeRepository.findByCategoryAndStatus(category, Place.Status.PUBLISHED, pageable);
    }

    private static String sortKey(String sort) {
        return SORT_KEYS.contains(sort) ? sort : "newest";
    }

    private static Sort sortOf(String key) {
        return switch (key) {
            case "oldest" -> Sort.by(Sort.Direction.ASC, "publishedAt");
            case "popular" -> Sort.by(Sort.Direction.DESC, "viewCount");
            default -> Sort.by(Sort.Direction.DESC, "publishedAt");
        };
    }

    private static String excerpt(String text, int max) {
        if (text == null) {
            return "";
        }
        String oneLine = text.replaceAll("\\s+", " ").trim();
        return oneLine.length() <= max ? oneLine : oneLine.substring(0, max) + "…";
    }
}
