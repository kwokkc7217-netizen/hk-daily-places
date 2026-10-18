package com.hkdaily.places.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * React CMS 係 SPA：/admin 底下任何「最後一段冇點」嘅路徑
 * （/admin、/admin/new、/admin/edit/123…）都 forward 去
 * /admin/index.html，由 React Router 接手。
 * <p>
 * 有點嘅（/admin/assets/index-*.js）唔會 match，照行 static resource handler。
 * /api/admin/** 唔同 prefix，唔會畀呢度食咗。
 */
@Controller
public class AdminForwardController {

    @GetMapping(value = {"/admin", "/admin/{p:[^.]*}", "/admin/**/{p:[^.]*}"})
    public String admin() {
        return "forward:/admin/index.html";
    }
}
