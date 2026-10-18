package com.hkdaily.places.seed;

import com.hkdaily.places.model.Place;
import com.hkdaily.places.repository.PlaceRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * DB 空嘅時候插入兩篇 sample 內容，方便第一次 deploy 即刻有嘢睇。
 * 有資料之後唔會再跑（count() &gt; 0 即跳過）。
 */
@Component
public class DataSeeder implements CommandLineRunner {

    private final PlaceRepository placeRepository;

    public DataSeeder(PlaceRepository placeRepository) {
        this.placeRepository = placeRepository;
    }

    @Override
    public void run(String... args) {
        if (placeRepository.count() > 0) {
            return;
        }

        Place dragonBack = new Place();
        dragonBack.setSlug("dragon-back");
        dragonBack.setCategory(Place.Category.HIKING);
        dragonBack.setStatus(Place.Status.PUBLISHED);
        dragonBack.setTitle("龍脊：香港最美行山徑");
        dragonBack.setDescription(
                "龍脊係港島東著名行山徑，曾被《時代》雜誌選為「亞洲最佳市區遠足徑」，係新手都行到嘅經典路線。\n\n"
                        + "路線由土地灣出發，沿山脊上行，經龍脊觀景台、打爛埕頂山，一路飽覽石澳、大浪灣同南中國海嘅無敵海景。晴天時仲可以遠眺赤柱同大潭。全程約 8.5 公里，需時約 4 小時，難度中等，有基本體能就應付到。\n\n"
                        + "交通：喺港鐵筲箕灣站轉乘 9 號巴士，土地灣下車即係起點；終點大浪灣有小巴同巴士返筲箕灣。秋冬係最佳季節，天清氣朗；夏天記得帶夠水、做足防曬，避開正午出發。\n\n"
                        + "裝備建議：行山鞋、至少 1.5 公升水、帽、毛巾。山上無補給，垃圾自己帶走，做個負責任嘅山友。");
        dragonBack.setMapQuery("龍脊, 香港");
        dragonBack.setImageUrl("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Dragon%27s_Back_Trail%2C_Hong_Kong.jpg/640px-Dragon%27s_Back_Trail%2C_Hong_Kong.jpg");
        dragonBack.setPublishedAt(LocalDateTime.now());
        placeRepository.save(dragonBack);

        Place k11 = new Place();
        k11.setSlug("k11-musea");
        k11.setCategory(Place.Category.SHOPPING);
        k11.setStatus(Place.Status.PUBLISHED);
        k11.setTitle("K11 MUSEA：尖沙咀文化購物地標");
        k11.setDescription(
                "K11 MUSEA 位於尖沙咀 Victoria Dockside，係香港近年最有話題性嘅文化購物地標，成棟建築本身就係一件藝術品。\n\n"
                        + "場內 10 層匯聚國際品牌、本地設計小店同多間概念餐廳，仲有 MoMA Design Store 進駐。建築亮點包括 Bohemian Garden 露天花園、Gold Ball 金球同埋成棟樓嘅流線型外牆，點打卡都靚。\n\n"
                        + "除咗 shopping，佢成日搞藝術展覽、工作坊同期間限定 pop-up，行一次有一次新發現。附近仲可以順路去星光大道海旁散步，黃昏睇日落一流。\n\n"
                        + "交通：港鐵尖沙咀站或尖東站步行約 10 分鐘；多條巴士線經梳士巴利道。建議預留半日，慢慢行、慢慢睇。");
        k11.setMapQuery("K11 MUSEA, 尖沙咀");
        k11.setImageUrl("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/K11_MUSEA_2020.jpg/640px-K11_MUSEA_2020.jpg");
        k11.setPublishedAt(LocalDateTime.now());
        placeRepository.save(k11);
    }
}
