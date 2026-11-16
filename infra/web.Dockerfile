FROM node:24-slim AS build
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci --no-fund --no-audit
COPY apps/web ./
RUN npm run build
FROM caddy:2-alpine
COPY --from=build /web/dist /srv
COPY infra/Caddy.web /etc/caddy/Caddyfile
