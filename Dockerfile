# ---- web: build React CMS ----
FROM node:20-alpine AS web
WORKDIR /web
COPY admin/package*.json ./
RUN npm install
COPY admin/ ./
RUN npm run build

# ---- build: Spring Boot ----
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
# React build 產物擺入 Spring static，CMS 會喺 /admin 提供服務
COPY --from=web /web/dist ./src/main/resources/static/admin/
RUN mvn -B package -DskipTests

# ---- run ----
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
