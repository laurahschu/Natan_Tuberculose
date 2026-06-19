# ---------- Stage 1: build do bundle estático ----------
FROM node:20-alpine AS build

WORKDIR /app

# Instala dependências (camada cacheável)
COPY package.json package-lock.json ./
RUN npm ci

# Build de produção (tsc + vite build -> /app/dist)
COPY . .
RUN npm run build

# ---------- Stage 2: serve estático com nginx ----------
FROM nginx:alpine

# Bundle gerado
COPY --from=build /app/dist /usr/share/nginx/html

# Config do nginx como TEMPLATE: o entrypoint oficial roda envsubst e
# substitui ${NGINX_PORT} no boot (SPA fallback + no-cache no config.js).
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Script roda no boot do container (entrypoint oficial do nginx executa
# *.sh em /docker-entrypoint.d/) e injeta a URL da API a partir da env.
COPY docker-entrypoint.d/40-app-config.sh /docker-entrypoint.d/40-app-config.sh
RUN chmod +x /docker-entrypoint.d/40-app-config.sh

# Porta em que o nginx escuta — ALINHE com a porta do domínio no EasyPanel.
ENV NGINX_PORT=80
# URL pública da API de predição (browser -> backend). Sobrescreva no EasyPanel.
ENV VITE_API_URL=http://localhost:5001/predict

EXPOSE 80

# Forma shell para expandir ${NGINX_PORT} em runtime.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:${NGINX_PORT}/ >/dev/null 2>&1 || exit 1
