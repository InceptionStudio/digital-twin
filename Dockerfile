FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp output personas/prompts

# Expose port for web API
EXPOSE 8000

# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "web_api:app", "--host", "0.0.0.0", "--port", "8000"]