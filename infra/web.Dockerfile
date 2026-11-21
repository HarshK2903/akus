FROM node:24-slim AS build
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci --no-fund --no-audit
COPY apps/web ./
RUN npm run build
FROM golang:1.27.4-alpine@sha256:70bd7ddea8b6cbe5d6943cde279d6b67feb10cc924fb9100d1d8757c1575b280 AS caddybuild
WORKDIR /src
ENV GOMAXPROCS=2
COPY infra/caddy-build.sh /src/build.sh
RUN sh /src/build.sh && go clean -cache -modcache

FROM caddy:2-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0 AS proxy
COPY --from=caddybuild /out/caddy /usr/bin/caddy
RUN apk add --no-cache --upgrade libcrypto3 libssl3 zlib

FROM proxy AS web
COPY --from=build /web/dist /srv
COPY infra/Caddy.web /etc/caddy/Caddyfile
