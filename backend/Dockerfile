FROM node:22-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json ./
COPY backend/package.json backend/tsconfig.json ./backend/

RUN npm ci --workspace backend

COPY backend/src ./backend/src

RUN npm run build --workspace backend

FROM node:22-bookworm-slim AS runtime

WORKDIR /app

COPY package.json package-lock.json ./
COPY backend/package.json ./backend/package.json

RUN npm ci --omit=dev --workspace backend \
  && mkdir -p /app/backend/data

WORKDIR /app/backend

COPY --from=build /app/backend/dist ./dist

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/index.js"]
