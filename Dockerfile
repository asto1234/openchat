FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user for security
RUN useradd -m openchat && chown -R openchat:openchat /app
USER openchat

# Expose port
EXPOSE 12345

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 12345), timeout=5)" || exit 1

# Run server
CMD ["python", "secure_server.py", "--host", "0.0.0.0", "--port", "12345"]
