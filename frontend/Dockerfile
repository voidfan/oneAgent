# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies and fix ajv version issue
RUN npm cache clean --force && \
    rm -rf node_modules package-lock.json && \
    npm install --legacy-peer-deps && \
    npm install ajv@8.12.0 ajv-keywords@5.1.0 --legacy-peer-deps

# Copy source code
COPY . .

# Set environment to skip source map generation for faster build
ENV GENERATE_SOURCEMAP=false
ENV CI=false

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
