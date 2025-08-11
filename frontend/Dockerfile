# Frontend Dockerfile - Multi-stage build for React app with Nginx
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files first (for better layer caching)
COPY package*.json ./

# Install dependencies with clean slate (avoid platform-specific binaries)
RUN npm ci && npm cache clean --force

# Copy source code (excluding node_modules)
COPY src ./src
COPY public ./public  
COPY index.html ./
COPY vite.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine AS production

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Add labels for metadata
LABEL org.opencontainers.image.title="SecureDevOps Frontend"
LABEL org.opencontainers.image.description="React frontend for SecureDevOps AI Platform"
LABEL org.opencontainers.image.version="1.0.0"

# Create nginx cache directory and setup permissions
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    touch /tmp/nginx.pid && \
    chown nginx:nginx /tmp/nginx.pid

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Use nginx user for security
USER nginx

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
