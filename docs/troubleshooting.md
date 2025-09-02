# 🚨 Troubleshooting Guide

## Common Issues and Solutions

### Authentication Problems

#### `ANTHROPIC_API_KEY not set`
**Symptoms**: Error message about missing API key
**Solution**:
```bash
# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env
echo "GOOGLE_CLOUD_PROJECT=your-gcp-project-id" >> .env

# Verify the file was created correctly
cat .env
```

#### `Cloud Run API not enabled`
**Symptoms**: Error about Cloud Run API not being enabled
**Solution**:
```bash
# Enable the Cloud Run API
gcloud services enable run.googleapis.com

# Verify it's enabled
gcloud services list --enabled | grep run
```

#### `Permission denied` or `Access denied`
**Symptoms**: Authentication errors during deployment
**Solution**:
```bash
# Check current authentication
gcloud auth list

# Re-authenticate if needed
gcloud auth login

# Set the correct project
gcloud config set project your-gcp-project-id

# Verify permissions
gcloud projects get-iam-policy your-gcp-project-id
```

#### Service Account Issues
**Symptoms**: Errors when using service account keys
**Solution**:
```bash
# Verify service account key file exists
ls -la /path/to/service-account-key.json

# Test the service account
gcloud auth activate-service-account --key-file=/path/to/service-account-key.json

# Check if service account has required roles
gcloud projects get-iam-policy your-project-id \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:your-service-account@your-project.iam.gserviceaccount.com"
```

Required IAM roles for service accounts:
- `roles/run.admin` - Deploy and manage Cloud Run services
- `roles/cloudbuild.builds.editor` - Create and manage Cloud Build builds
- `roles/storage.admin` - Access Cloud Storage for build artifacts
- `roles/iam.serviceAccountUser` - Act as service accounts

### Multi-Agent System Issues

#### `Multi-agent generation failed`
**Symptoms**: Multi-agent system fails to generate code
**Solution**:
```bash
# Use single-agent fallback
python prototype.py spec.md --single-agent

# Enable debug mode to see what failed
python prototype.py spec.md --debug --verbose

# Check API rate limits
python prototype.py spec.md --validate-only --verbose
```

#### Low Quality Scores
**Symptoms**: Generated code has validation scores below 0.8
**Solution**:
```bash
# Enable debug to see specific issues
python prototype.py spec.md --debug --verbose

# Review and improve your specification
python prototype.py spec.md --validate-only

# Try with different quality threshold
# Edit your .env file:
echo "MULTI_AGENT_QUALITY_THRESHOLD=0.6" >> .env
```

#### API Rate Limit Exceeded
**Symptoms**: "Rate limit exceeded" errors from Anthropic
**Solution**:
```bash
# Use single-agent mode (fewer API calls)
python prototype.py spec.md --single-agent

# Wait and retry (rate limits reset every minute)
sleep 60
python prototype.py spec.md

# Check your API key usage at console.anthropic.com
```

### Docker Issues

#### Permission denied: 'gcloud' Error
**Symptoms**: Docker container can't execute gcloud commands
**Solution**:
```bash
# Rebuild the Docker image
docker-compose build --no-cache cloud-function-saas

# Or build manually with no cache
docker build --no-cache -t cloud-function-saas .
```

#### Authentication Issues in Docker

**For gcloud CLI authentication:**
```bash
# Verify your authentication works
docker-compose run --rm cloud-function-saas bash
# Then inside the container:
gcloud auth list
gcloud config list

# If not authenticated, mount gcloud config:
docker-compose run --rm \
  -v ~/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md
```

**For Service Account Key authentication:**
```bash
# Verify your service account key is accessible
docker-compose run --rm cloud-function-saas bash
# Then inside the container:
ls -la /app/service-account-key.json
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
python -c "from google.auth import default; print(default())"
```

#### Volume Mount Issues on Windows
**Symptoms**: Files not accessible inside container on Windows
**Solution**:
```bash
# Use forward slashes and full paths
docker-compose run --rm \
  -v C:/Users/YourName/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md

# Or use WSL2 paths
docker-compose run --rm \
  -v /mnt/c/Users/YourName/.config/gcloud:/root/.config/gcloud \
  cloud-function-saas examples/example-spec.md
```

### Deployment Issues

#### Service deployment fails
**Symptoms**: Cloud Run deployment errors
**Solution**:
```bash
# Check Cloud Build logs
gcloud builds list --limit=5

# Get detailed build logs
gcloud builds log [BUILD_ID]

# Verify Cloud Run quotas
gcloud compute project-info describe --project=your-project-id

# Check service status
gcloud run services list --platform=managed
```

#### Service not responding after deployment
**Symptoms**: Service URL returns 500 or timeout errors
**Solution**:
```bash
# Check service logs
gcloud run services logs read your-service-name --platform=managed

# Verify service configuration
gcloud run services describe your-service-name --platform=managed

# Test locally first
python prototype.py spec.md --validate-only --output-dir ./test
cd test
npm install
npm start
```

#### Build timeout or memory issues
**Symptoms**: Cloud Build fails with timeout or out-of-memory errors
**Solution**:
```bash
# Use shorter timeout for testing
gcloud config set builds/timeout 600

# Check Cloud Build quotas and usage
gcloud builds list --filter="status=TIMEOUT"

# Simplify your specification to reduce generated code complexity
```

### Specification Issues

#### Spec parsing errors
**Symptoms**: "Invalid specification format" errors
**Solution**:
```bash
# Validate specification syntax
python prototype.py spec.md --validate-only

# Check for common markdown issues:
# - Missing required sections (Service Name, Endpoints, Models)
# - Invalid YAML syntax in code blocks
# - Inconsistent indentation
# - Special characters in headers

# Use a simple spec as template
cp examples/example-spec.md my-spec.md
# Edit my-spec.md with your requirements
```

#### Generated code doesn't match specification
**Symptoms**: Deployed service behaves differently than expected
**Solution**:
```bash
# Use multi-agent system for better spec compliance
python prototype.py spec.md --multi-agent --verbose

# Review validation report
python prototype.py spec.md --debug --verbose

# Make your specification more detailed and explicit
# Add validation rules and business logic sections
```

### Network and Connectivity Issues

#### DNS resolution errors
**Symptoms**: Cannot reach deployed service URLs
**Solution**:
```bash
# Check service URL
gcloud run services list --platform=managed

# Test with curl
curl -I https://your-service-url.run.app/

# Check DNS resolution
nslookup your-service-url.run.app

# Verify firewall settings
gcloud compute firewall-rules list
```

#### Timeout during deployment
**Symptoms**: Commands hang or timeout
**Solution**:
```bash
# Check network connectivity
ping google.com

# Verify gcloud connectivity
gcloud config list
gcloud auth list

# Use shorter timeout
timeout 300 python prototype.py spec.md

# Check proxy settings if behind corporate firewall
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

## Debug Commands

### General Debugging
```bash
# Enable maximum verbosity
python prototype.py spec.md --debug --verbose

# Validate setup without deploying
python prototype.py spec.md --validate-only --verbose

# Keep generated files for inspection
python prototype.py spec.md --output-dir ./debug-output

# Check environment variables
env | grep -E '(ANTHROPIC|GOOGLE)'
```

### Authentication Debugging
```bash
# Check gcloud authentication
gcloud auth list
gcloud config list

# Test API access
gcloud projects list

# Verify service account (if using)
gcloud auth activate-service-account --key-file=/path/to/key.json
gcloud projects list
```

### Multi-Agent System Debugging
```bash
# Test multi-agent system
python test_multi_agent.py

# Compare single vs multi-agent
python prototype.py spec.md --single-agent --verbose > single.log
python prototype.py spec.md --multi-agent --verbose > multi.log
diff single.log multi.log
```

### Docker Debugging
```bash
# Check container environment
docker-compose run --rm cloud-function-saas bash -c "env"

# Test dependencies
docker-compose run --rm cloud-function-saas bash -c "python -c 'import anthropic, google.cloud.run_v2; print(\"OK\")'"

# Check mounted volumes
docker-compose run --rm cloud-function-saas bash -c "ls -la /app && ls -la /root/.config"
```

## Getting Additional Help

### Log Collection
When reporting issues, include:

```bash
# System information
python --version
gcloud version
docker --version

# Environment variables (sanitized)
env | grep -E '(ANTHROPIC|GOOGLE)' | sed 's/=.*/=***/'

# Error logs
python prototype.py spec.md --debug --verbose 2>&1 | tee debug.log

# Service logs (if deployed)
gcloud run services logs read your-service --limit=50
```

### Issue Reporting
1. Check if your issue is already reported in [GitHub Issues](https://github.com/boxwood-ai/cloud-function-saas/issues)
2. Include the full error message and context
3. Provide your OS, Python version, and gcloud version
4. Share your specification file (with sensitive data removed)
5. Include debug logs from the commands above

### Community Support
- 📖 **Documentation**: [docs/](../docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/boxwood-ai/cloud-function-saas/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/boxwood-ai/cloud-function-saas/discussions)

### Quick Health Check
Run this comprehensive health check:

```bash
#!/bin/bash
echo "=== Cloud Function SaaS Health Check ==="

echo "1. Python version:"
python --version

echo "2. Required Python packages:"
python -c "import anthropic; print('✅ anthropic')" 2>/dev/null || echo "❌ anthropic missing"
python -c "import google.cloud.run_v2; print('✅ google-cloud-run')" 2>/dev/null || echo "❌ google-cloud-run missing"

echo "3. Google Cloud SDK:"
gcloud version 2>/dev/null || echo "❌ gcloud not installed"

echo "4. Authentication:"
gcloud auth list 2>/dev/null | grep -q "ACTIVE" && echo "✅ Authenticated" || echo "❌ Not authenticated"

echo "5. Environment variables:"
[ -n "$ANTHROPIC_API_KEY" ] && echo "✅ ANTHROPIC_API_KEY set" || echo "❌ ANTHROPIC_API_KEY missing"
[ -n "$GOOGLE_CLOUD_PROJECT" ] && echo "✅ GOOGLE_CLOUD_PROJECT set" || echo "❌ GOOGLE_CLOUD_PROJECT missing"

echo "6. API access:"
python -c "
import os
from anthropic import Anthropic
try:
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    print('✅ Anthropic API accessible')
except:
    print('❌ Anthropic API not accessible')
" 2>/dev/null

echo "7. Google Cloud APIs:"
gcloud services list --enabled --filter="name:run.googleapis.com" --quiet 2>/dev/null | grep -q "run.googleapis.com" && echo "✅ Cloud Run API enabled" || echo "❌ Cloud Run API not enabled"

echo "=== Health Check Complete ==="
```

Save this as `health-check.sh`, make it executable (`chmod +x health-check.sh`), and run it (`./health-check.sh`) to quickly diagnose common issues.