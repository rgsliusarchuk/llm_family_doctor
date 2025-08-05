# Multi-stage Dockerfile for LLM Family Doctor
ARG TARGET=all
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    fonts-dejavu \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Expose ports
EXPOSE 8501 8000

# Set default command based on target
FROM base AS api
CMD ["python", "start_api_server.py"]

FROM base AS streamlit
CMD ["python", "start_streamlit.py"]

FROM base AS all
CMD ["bash", "-c", "python start_api_server.py & python start_streamlit.py"]

# Default target
FROM all 