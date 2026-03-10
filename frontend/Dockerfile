FROM node:22-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json ./
COPY frontend/package.json frontend/tsconfig.json frontend/vite.config.ts ./frontend/

RUN npm ci --workspace frontend

COPY frontend ./frontend

RUN npm run build --workspace frontend

FROM nginx:1.27-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
