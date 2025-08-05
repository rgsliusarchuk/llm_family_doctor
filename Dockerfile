# Production Dockerfile for LLM Family Doctor
FROM python:3.11-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install system dependencies (minimal set for runtime)
RUN apt-get update && apt-get install -y \
    curl \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["python", "start_api_server.py"] 