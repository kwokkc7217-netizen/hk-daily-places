package com.hkdaily.places.seed;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * Seed 內容用 slug 做 upsert：DB 空就插入；已存在就更新圖片 URL。
 * 咁樣之後換真圖、改 seed 內容，deploy 就會自動修正線上資料。
 */
@Component
public class DataSeeder implements CommandLineRunner {

    private final PlaceRepository placeRepository;

    public DataSeeder(PlaceRepository placeRepository) {
        this.placeRepository = placeRepository;
    }

    @Override
    public void run(String... args) {
        upsert(seedDragonBack());
        upsert(seedK11());
    }

    private void upsert(Place seed) {
        Place existing = placeRepository.findBySlug(seed.getSlug()).orElse(null);
        if (existing == null) {
            placeRepository.save(seed);
            return;
        }
        // 已存在：更新圖片（同埋補返冇嘅欄），唔郁其他內容
        boolean changed = false;
        if (!seed.getImageUrl().equals(existing.getImageUrl())) {
            existing.setImageUrl(seed.getImageUrl());
            changed = true;
        }
        if (changed) {
            placeRepository.save(existing);
        }
    }

    private Place seedDragonBack() {
        Place p = new Place();
        p.setSlug("dragon-back");
        p.setCategory(Place.Category.HIKING);
        p.setStatus(Place.Status.PUBLISHED);
        p.setTitle("龍脊：香港最美行山徑");
        p.setDescription(
                "龍脊係港島東著名行山徑，曾被《時代》雜誌選為「亞洲最佳市區遠足徑」，係新手都行到嘅經典路線。\n\n"
                        + "路線由土地灣出發，沿山脊上行，經龍脊觀景台、打爛埕頂山，一路飽覽石澳、大浪灣同南中國海嘅無敵海景。晴天時仲可以遠眺赤柱同大潭。全程約 8.5 公里，需時約 4 小時，難度中等，有基本體能就應付到。\n\n"
                        + "交通：喺港鐵筲箕灣站轉乘 9 號巴士，土地灣下車即係起點；終點大浪灣有小巴同巴士返筲箕灣。秋冬係最佳季節，天清氣朗；夏天記得帶夠水、做足防曬，避開正午出發。\n\n"
                        + "裝備建議：行山鞋、至少 1.5 公升水、帽、毛巾。山上無補給，垃圾自己帶走，做個負責任嘅山友。");
        p.setMapQuery("龍脊, 香港");
        p.setImageUrl("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Dragon%27s_Back_-_Trail_Start%2C_Hong_Kong_%28Unsplash%29.jpg/960px-Dragon%27s_Back_-_Trail_Start%2C_Hong_Kong_%28Unsplash%29.jpg");
        p.setPublishedAt(LocalDateTime.now());
        return p;
    }

    private Place seedK11() {
        Place p = new Place();
        p.setSlug("k11-musea");
        p.setCategory(Place.Category.SHOPPING);
        p.setStatus(Place.Status.PUBLISHED);
        p.setTitle("K11 MUSEA：尖沙咀文化購物地標");
        p.setDescription(
                "K11 MUSEA 位於尖沙咀 Victoria Dockside，係香港近年最有話題性嘅文化購物地標，成棟建築本身就係一件藝術品。\n\n"
                        + "場內 10 層匯聚國際品牌、本地設計小店同多間概念餐廳，仲有 MoMA Design Store 進駐。建築亮點包括 Bohemian Garden 露天花園、Gold Ball 金球同埋成棟樓嘅流線型外牆，點打卡都靚。\n\n"
                        + "除咗 shopping，佢成日搞藝術展覽、工作坊同期間限定 pop-up，行一次有一次新發現。附近仲可以順路去星光大道海旁散步，黃昏睇日落一流。\n\n"
                        + "交通：港鐵尖沙咀站或尖東站步行約 10 分鐘；多條巴士線經梳士巴利道。建議預留半日，慢慢行、慢慢睇。");
        p.setMapQuery("K11 MUSEA, 尖沙咀");
        p.setImageUrl("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/K11_MUSEA_inside_11-09-2021.jpg/960px-K11_MUSEA_inside_11-09-2021.jpg");
        p.setPublishedAt(LocalDateTime.now());
        return p;
    }
}
