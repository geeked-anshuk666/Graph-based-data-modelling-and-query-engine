# Stage 1: Build the Next.js frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
# Requirements are expected in src/frontend 
COPY src/frontend/package*.json ./
RUN npm install
COPY src/frontend/ ./
# Build the static export
RUN npm run build

# Stage 2: Build the final image with Python backend + Static frontend
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (from src/backend to /app/backend)
COPY src/backend/ ./backend/
# Copy the dataset (from src/dataset to /app/src/dataset)
COPY src/dataset/ ./src/dataset/

# Copy the built frontend static files to the backend/static directory
COPY --from=frontend-builder /app/frontend/out /app/backend/static

# Expose the single port
EXPOSE 8000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Default command: run uvicorn from the /app context, looking into the backend folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
