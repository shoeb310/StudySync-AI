FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies only when needed
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

# Build Next.js
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Expose Next.js port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "run", "start"]
