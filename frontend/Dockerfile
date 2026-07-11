# Stage 1: Build Next.js Application
FROM node:22-alpine AS builder
WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy configuration and source files
COPY . .

# Set environment variable for API connection during build time if necessary
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}

# Build production bundles
RUN npm run build

# Stage 2: Serve Next.js Application
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copy configurations and public resources
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Expose Next.js port
EXPOSE 3000

# Run Next.js server
CMD ["npm", "run", "start"]
