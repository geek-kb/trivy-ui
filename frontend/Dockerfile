
# frontend/Dockerfile

# Step 1: Build the React frontend
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies with clean cache
RUN npm ci && npm cache clean --force

# Copy source files
COPY . .

# Build the production bundle
RUN npm run build

# Step 2: Serve it using a lightweight web server (nginx)
FROM nginx:stable-alpine

# Set working directory for nginx
WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy built frontend from previous stage
COPY --from=builder /app/dist .

# Copy custom nginx config if available (optional)
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
