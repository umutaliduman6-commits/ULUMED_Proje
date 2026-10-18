FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-video.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-video.txt

# Copy application files
COPY video_server.py .
COPY index.html ./static/index.html

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/oda/test')" || exit 1

# Run the application
CMD ["python", "video_server.py"]
