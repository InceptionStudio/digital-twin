FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-docker.txt requirements.txt ./

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python dependencies (use docker-specific requirements if available)
RUN if [ -f requirements-docker.txt ]; then \
        pip install --no-cache-dir -r requirements-docker.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Install debugpy for debugging support
RUN pip install --no-cache-dir debugpy watchdog

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp output personas/prompts

# Expose ports for web API and debugger
EXPOSE 8000 

# Default command with hot reload enabled
CMD ["python", "-Xfrozen_modules=off", "-m", "uvicorn", "web_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app", "--workers", "4"]