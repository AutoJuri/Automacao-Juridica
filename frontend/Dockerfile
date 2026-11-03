# Build da SPA (Vite) e servir por nginx com fallback de rotas do router.
FROM oven/bun:1 AS build
WORKDIR /app
ARG VITE_API_URL=https://automacao-juridica.abneraijiner.com.br
ENV VITE_API_URL=$VITE_API_URL
COPY bun.lock package.json tsconfig.json vite.config.ts ./
COPY src ./src
COPY public ./public
COPY index.html ./
RUN bun install --frozen-lockfile
RUN bun run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
