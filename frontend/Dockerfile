
# ------------------------
# Build Stage
# ------------------------
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ------------------------
# Serve Stage
# ------------------------
FROM nginx:stable-alpine

RUN rm -rf /usr/share/nginx/html/*

# Copy build
COPY --from=builder /app/dist /usr/share/nginx/html

# Critical: copy both nginx.conf and default.conf
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
