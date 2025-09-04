# Multi-stage build for React app
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies for node-gyp
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Development stage
FROM base as development
# Install all dependencies
RUN npm install && npm cache clean --force
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# Build stage
FROM base as build
# Install all dependencies for build
RUN npm install && npm cache clean --force
COPY . .
# Set build environment
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
RUN npm run build

# Production stage
FROM nginx:alpine as production
# Copy build files
COPY --from=build /app/build /usr/share/nginx/html
# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]