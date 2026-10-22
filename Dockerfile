# ==============================================================================
# CLAUSENT - Fullstack Production Container for Render
# Multi-stage build: React Frontend (Vite) + FastAPI Python Backend
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build the React (Vite) Frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Install dependencies with lockfile caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source files
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src

# Compile production bundle into /app/dist
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install essential system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Optimize Python execution and configure defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production \
    DEBUG=False \
    ENABLE_LEGAL_BERT=False \
    SLM_PROVIDER=mock_local \
    LLM_PROVIDER=mock_local

# Install Python backend dependencies (CPU-optimized PyTorch)
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source code
COPY backend ./backend

# Copy compiled frontend assets from Stage 1 into /app/dist
COPY --from=frontend-builder /app/dist ./dist

# Create necessary runtime directories
RUN mkdir -p backend/data/uploads backend/data/reports backend/data/models

# Expose port (Render overrides with $PORT at runtime)
EXPOSE 8000

# Start application server bound to 0.0.0.0 on Render's assigned PORT
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
