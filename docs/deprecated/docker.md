# 🐳 Docker Usage Guide

## Overview

Docker provides the easiest way to use Cloud Function SaaS without installing Python dependencies or configuring your local environment. The Docker setup includes all required dependencies and provides consistent behavior across different platforms.

## Quick Start

### Basic Usage

```bash
# Clone the repository
git clone https://github.com/boxwood-ai/cloud-function-saas.git
cd cloud-function-saas

# Set up environment variables
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
echo "GOOGLE_CLOUD_PROJECT=your-gcp-project-id" >> .env

# Deploy a specification
docker-compose run --rm cloud-function-saas examples/example-spec.md --verbose
```

## Authentication Methods

### Method 1: Service Account Key (Recommended for Docker)

This is the most reliable method for Docker deployments:

1. **Create a service account key**:
   ```bash
   # Create service account
   gcloud iam service-accounts create cloud-function-saas \
     --display-name="Cloud Function SaaS"
   
   # Grant necessary permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:cloud-function-saas@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:cloud-function-saas@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/cloudbuild.builds.editor"
   
   # Create and download key
   gcloud iam service-accounts keys create ./service-account-key.json \
     --iam-account=cloud-function-saas@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Add to your `.env` file**:
   ```bash
   echo "GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json" >> .env
   ```

3. **Deploy with Docker**:
   ```bash
   docker-compose run --rm \
     -v $(pwd)/service-account-key.json:/app/service-account-key.json \
     cloud-function-saas examples/example-spec.md --verbose
   ```

### Method 2: gcloud CLI Authentication

If you have gcloud installed locally:

```bash
# Authenticate with gcloud
gcloud auth login
gcloud config set project your-gcp-project-id

# Mount gcloud config to Docker container
docker-compose run --rm \
  -v ~/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md --verbose
```

### Method 3: Authenticate Inside Container

```bash
# Run interactive container
docker-compose run --rm cloud-function-saas bash

# Inside container, authenticate
gcloud auth login
gcloud config set project your-gcp-project-id

# Deploy specification
python prototype.py examples/example-spec.md --verbose
```

## Docker Compose Configuration

### Basic docker-compose.yml

```yaml
version: '3.8'

services:
  cloud-function-saas:
    build: .
    volumes:
      - .:/app
      - ./generated:/app/generated
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}
    working_dir: /app
    entrypoint: ["python", "prototype.py"]
```

### Development docker-compose.yml

For development with mounted volumes:

```yaml
version: '3.8'

services:
  cloud-function-saas:
    build: .
    volumes:
      - .:/app
      - ./specs:/app/specs
      - ./generated:/app/generated
      - ~/.config/gcloud:/root/.config/gcloud  # For gcloud auth
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
    working_dir: /app
    entrypoint: ["python", "prototype.py"]

  dev-shell:
    build: .
    volumes:
      - .:/app
      - ~/.config/gcloud:/root/.config/gcloud
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
    working_dir: /app
    entrypoint: ["bash"]
```

## Common Commands

### Deploy Specifications

```bash
# Basic deployment
docker-compose run --rm cloud-function-saas examples/example-spec.md

# With verbose output
docker-compose run --rm cloud-function-saas examples/example-spec.md --verbose

# Validate without deploying
docker-compose run --rm cloud-function-saas examples/example-spec.md --validate-only

# Keep generated files locally
docker-compose run --rm cloud-function-saas examples/example-spec.md --output-dir /app/generated

# Use specific project and region
docker-compose run --rm cloud-function-saas examples/example-spec.md \
  --project my-project --region europe-west1
```

### Multi-Agent System

```bash
# Force multi-agent mode (default)
docker-compose run --rm cloud-function-saas examples/example-spec.md --multi-agent

# Use single-agent mode
docker-compose run --rm cloud-function-saas examples/example-spec.md --single-agent

# Multi-agent with debug output
docker-compose run --rm cloud-function-saas examples/example-spec.md --debug --verbose
```

### Development Commands

```bash
# Interactive shell in container
docker-compose run --rm cloud-function-saas bash

# Development shell with mounted volumes
docker-compose run --rm dev-shell

# Run tests inside container
docker-compose run --rm cloud-function-saas bash -c "python test_multi_agent.py"

# Check authentication status
docker-compose run --rm cloud-function-saas bash -c "gcloud auth list"
```

## Custom Spec Files

### Create Specs Directory

```bash
# Create specs directory for your custom specifications
mkdir specs

# Copy and edit example specs
cp examples/example-spec.md specs/my-api.spec.md
# Edit specs/my-api.spec.md with your requirements

# Deploy your custom spec
docker-compose run --rm cloud-function-saas specs/my-api.spec.md --verbose
```

### Mount Custom Directories

```bash
# Mount custom specs directory
docker-compose run --rm \
  -v $(pwd)/my-specs:/app/my-specs \
  cloud-function-saas my-specs/custom-api.spec.md

# Mount multiple directories
docker-compose run --rm \
  -v $(pwd)/specs:/app/specs \
  -v $(pwd)/output:/app/output \
  cloud-function-saas specs/api.spec.md --output-dir /app/output
```

## Manual Docker Usage

### Build Image

```bash
# Build the image manually
docker build -t cloud-function-saas .

# Build with specific tag
docker build -t cloud-function-saas:latest .
```

### Run Container

```bash
# Basic run
docker run --rm -it \
  -v $(pwd)/examples:/app/examples \
  -v $(pwd)/generated:/app/generated \
  -e ANTHROPIC_API_KEY=your_key \
  -e GOOGLE_CLOUD_PROJECT=your_project \
  cloud-function-saas examples/example-spec.md --verbose

# With service account key
docker run --rm -it \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  -v $(pwd)/examples:/app/examples \
  -e ANTHROPIC_API_KEY=your_key \
  -e GOOGLE_CLOUD_PROJECT=your_project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  cloud-function-saas examples/example-spec.md --verbose

# Interactive bash session
docker run --rm -it \
  -v $(pwd):/app \
  -e ANTHROPIC_API_KEY=your_key \
  -e GOOGLE_CLOUD_PROJECT=your_project \
  cloud-function-saas bash
```

## Troubleshooting

### Common Issues

#### Permission Denied: 'gcloud' Error

If you see permission errors:

```bash
# Rebuild the Docker image
docker-compose build --no-cache cloud-function-saas

# Or build manually
docker build --no-cache -t cloud-function-saas .
```

#### Authentication Issues

**For gcloud CLI authentication:**
```bash
# Verify your authentication works
docker-compose run --rm cloud-function-saas bash
# Inside container:
gcloud auth list
gcloud config list
```

**For Service Account Key authentication:**
```bash
# Verify the key file is accessible
docker-compose run --rm cloud-function-saas bash
# Inside container:
ls -la /app/service-account-key.json
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
python -c "from google.auth import default; print(default())"
```

**Check which authentication method is being used:**
```bash
# Run with verbose logging
docker-compose run --rm cloud-function-saas examples/example-spec.md --validate-only --verbose
```

#### Volume Mount Issues on Windows

```bash
# Use forward slashes and full paths
docker-compose run --rm \
  -v C:/Users/YourName/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md

# Alternative: use WSL2 paths
docker-compose run --rm \
  -v /mnt/c/Users/YourName/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md
```

#### Container Build Issues

```bash
# Clear Docker cache and rebuild
docker system prune -f
docker-compose build --no-cache cloud-function-saas

# Check Dockerfile syntax
docker build --no-cache -t test-build .
```

### Debug Information

Enable detailed logging:
```bash
# Run with debug and verbose flags
docker-compose run --rm cloud-function-saas examples/example-spec.md --debug --verbose
```

### Check Container Environment

```bash
# Inspect container environment
docker-compose run --rm cloud-function-saas bash -c "env | grep -E '(ANTHROPIC|GOOGLE)'"

# Check mounted volumes
docker-compose run --rm cloud-function-saas bash -c "ls -la /app && ls -la /root/.config/gcloud"

# Test Python dependencies
docker-compose run --rm cloud-function-saas bash -c "python -c 'import anthropic, google.cloud.run_v2; print(\"Dependencies OK\")'"
```

## Performance Optimization

### Build Optimization

```dockerfile
# Multi-stage build for smaller images
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim
COPY --from=builder /root/.local /root/.local
# ... rest of Dockerfile
```

### Cache Optimization

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t cloud-function-saas .

# Pre-pull base images
docker pull python:3.9-slim
docker pull google/cloud-sdk:slim
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy with Cloud Function SaaS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Cloud Run
        run: |
          echo "${{ secrets.GOOGLE_SERVICE_ACCOUNT_KEY }}" > service-account-key.json
          docker-compose run --rm \
            -v $(pwd)/service-account-key.json:/app/service-account-key.json \
            -e ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }} \
            -e GOOGLE_CLOUD_PROJECT=${{ secrets.GOOGLE_CLOUD_PROJECT }} \
            -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
            cloud-function-saas specs/production.spec.md --verbose
```

### Docker Hub

```bash
# Tag and push to Docker Hub
docker tag cloud-function-saas yourusername/cloud-function-saas:latest
docker push yourusername/cloud-function-saas:latest

# Use from Docker Hub
docker run --rm -it yourusername/cloud-function-saas:latest --help
```

This Docker guide provides comprehensive instructions for using Cloud Function SaaS in containerized environments, ensuring consistent behavior across different platforms and deployment scenarios.