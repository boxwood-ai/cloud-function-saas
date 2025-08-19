# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (before installing gcloud)
RUN useradd -m -u 1000 clouduser

# Install Google Cloud SDK for clouduser
USER clouduser
RUN curl https://sdk.cloud.google.com | bash
ENV PATH /home/clouduser/google-cloud-sdk/bin:$PATH

# Switch back to root for remaining setup
USER root

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for generated files and set ownership
RUN mkdir -p /app/generated && \
    chown -R clouduser:clouduser /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user for runtime
USER clouduser

# Expose port (if needed for future web interface)
EXPOSE 8080

# Default command
ENTRYPOINT ["python", "prototype.py"]
CMD ["--help"]