# syntax=docker/dockerfile:1
# Bouwt een Spring Boot-component (Kotlin, Gradle) uit de broncode, voor componenten
# zonder bereikbaar image (ghcr.io is hier niet bereikbaar, NL Portal heeft geen
# publiek backend-image). Gebruikt door stacks/g4/bouw.sh, met twee benoemde contexten:
#   bron      de git-checkout van het component op de vaste tag
#   extra-ca  map met extra CA-certificaten (*.crt), leeg op een normale machine
ARG JDK_IMAGE=eclipse-temurin:21.0.12_8-jdk-alpine-3.23
ARG JRE_IMAGE=eclipse-temurin:21.0.12_8-jre-alpine-3.23

FROM ${JDK_IMAGE} AS build
COPY --from=extra-ca . /tmp/extra-ca/
# Extra CA's (proxy met TLS-inspectie) in de truststore van de JDK, alleen in de bouwfase
RUN set -e; n=0; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] || continue; \
      awk -v pre="/tmp/extra-ca/deel-" 'BEGIN{c=0} /BEGIN CERT/{c++} {print > (pre c ".pem")}' "$f"; \
    done; for p in /tmp/extra-ca/deel-*.pem; do [ -f "$p" ] || continue; n=$((n+1)); \
      keytool -importcert -noprompt -cacerts -storepass changeit -alias "extra-$n" -file "$p" >/dev/null 2>&1 || true; \
    done; echo "extra CA's: $n"
WORKDIR /src
COPY --from=bron . .
ARG GRADLE_TAAK
ARG JAR_PAD
ENV GRADLE_OPTS="-Dorg.gradle.daemon=false -Dorg.gradle.jvmargs=-Xmx2g -Dorg.gradle.workers.max=2 -Dkotlin.daemon.jvmargs=-Xmx1536m"
RUN --mount=type=cache,id=demogemeente-gradle,target=/root/.gradle \
    chmod +x gradlew && ./gradlew --no-daemon --console=plain $GRADLE_TAAK -x test \
 && cp $JAR_PAD /tmp/app.jar

FROM ${JRE_IMAGE}
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=build /tmp/app.jar /app/app.jar
USER app
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75"
EXPOSE 8080
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
