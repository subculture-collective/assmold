FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_AUTH_ENABLED=true
ENV VITE_API_BASE=/api VITE_AUTH_ENABLED=${VITE_AUTH_ENABLED}
RUN npm run build

FROM nginx:1.31.7-alpine@sha256:892bb2152464f0c5d8972593a5f5afaf8054552580b699d95f8ff4af08c2d33d
ARG ASSMOLD_COMMIT=unknown
LABEL org.opencontainers.image.source="https://git.subcult.tv/subculture-collective/assmold" \
      org.opencontainers.image.revision=${ASSMOLD_COMMIT}

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
