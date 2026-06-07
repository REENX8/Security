# Stage 1: build React/Vite app
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --frozen-lockfile

COPY . .

# VITE_API_URL must be baked in at build time (Vite replaces it in the bundle).
# Set this as a Railway Build Argument:
#   Dashboard Service → Settings → Build → Add Build Argument
#   VITE_API_URL = https://your-backend.up.railway.app
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: serve the static build
FROM node:20-alpine
RUN npm install -g serve

COPY --from=builder /app/dist /dist

EXPOSE 3000
# 'serve -s' enables SPA mode: unknown paths serve index.html (required for React Router)
CMD ["sh", "-c", "serve -s /dist -l ${PORT:-3000}"]
