# Imagen para publicar el backend (Render). Compila con Maven y ejecuta con Java 21.
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/coffeeexport-backend-*.jar app.jar
ENV JAVA_OPTS="-Xmx350m -XX:+UseSerialGC"
EXPOSE 8080
CMD ["sh","-c","java $JAVA_OPTS -jar app.jar"]
