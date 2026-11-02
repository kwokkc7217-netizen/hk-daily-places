package com.hkdaily.places.config;

import com.mongodb.client.MongoClients;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.core.MongoTemplate;

/**
 * MongoDB Atlas 連線：得 MONGODB_URI 先起 bean。
 * 冇設嘅話成個 search 功能跌返 Postgres，網站照行唔會炒。
 */
@Configuration
public class MongoConfig {

    @Bean
    @ConditionalOnExpression("'${app.mongo.uri:}' != ''")
    public MongoTemplate mongoTemplate(
            @Value("${app.mongo.uri}") String uri,
            @Value("${app.mongo.database:hkplaces}") String database) {
        return new MongoTemplate(MongoClients.create(uri), database);
    }
}
