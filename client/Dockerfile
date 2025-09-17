# Multi-stage build to handle rollup issues
FROM node:20.19.0-alpine AS builder

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./
COPY .npmrc ./

# Clean install to avoid rollup issues
RUN rm -rf node_modules package-lock.json && \
    npm install --legacy-peer-deps --no-optional && \
    npm install rollup@^4.0.0 --save-dev --legacy-peer-deps || echo "Rollup install failed, continuing..."

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 5173

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]