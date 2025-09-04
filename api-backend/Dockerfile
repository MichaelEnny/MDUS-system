FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including libmagic for file type detection
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/processed /app/temp /app/archive /app/logs && \
    chmod 755 /app/uploads /app/processed /app/temp /app/archive /app/logs

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1000 mdus && \
    chown -R mdus:mdus /app
USER mdus

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command - use the system runner for full functionality
CMD ["python", "run_system.py", "api"]