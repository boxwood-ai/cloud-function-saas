# Cloud Function Microservice Generator

> **📋 See [goals.md](goals.md) for the complete project vision and planned features**

A Python prototype that transforms specification documents into deployed Google Cloud Run microservices using Claude AI.

## Current Status

🚧 **Prototype Phase** - Basic spec-to-deployment pipeline working

**What works now:**
- Spec parsing from markdown files
- Claude AI code generation 
- Automatic Cloud Run deployment
- Environment-based configuration

## Quick Start

### 1. Prerequisites
```bash
# Install Google Cloud SDK
brew install google-cloud-sdk  # macOS
# Or follow: https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project your-gcp-project-id
```

### 2. Setup
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Anthropic API key and GCP project
```

### 3. Validate Configuration
```bash
# Check if everything is set up correctly
python prototype.py example-spec.md --validate-only
```

### 4. Create a Spec
```bash
# Use the example or create your own
cp example-spec.md my-service-spec.md
# Edit my-service-spec.md with your requirements
```

### 5. Generate & Deploy
```bash
# Deploy to Cloud Run (with detailed output)
python prototype.py my-service-spec.md --verbose

# Or use basic output
python prototype.py my-service-spec.md
```

That's it! Your microservice is now deployed and running on Cloud Run.

## Configuration

### Environment Variables (.env)
```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Optional (with defaults)
CLAUDE_MODEL=                    # Auto-detects latest Sonnet
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.1
GOOGLE_CLOUD_REGION=us-central1
```

## Spec Format

Simple markdown format that Claude understands:

```markdown
# Service Name: User API
Description: Simple user management microservice
Runtime: Node.js 20

## Endpoints
### GET /users
- Description: Get all users
- Output: { users: array }

### POST /users
- Description: Create a new user
- Input: { name: string, email: string }
- Output: { user: User, id: string }

## Models
### User
- id: string (UUID)
- name: string (required)
- email: string (required, unique)
- createdAt: timestamp
```

See [example-spec.md](example-spec.md) for a working example.

## How It Works

1. **Parse** the spec.md file into structured data
2. **Generate** Node.js Cloud Run function using Claude AI
3. **Deploy** directly to Google Cloud Run
4. **Return** the deployed service URL

## Command Options

```bash
python prototype.py <spec-file> [options]

Options:
  --project PROJECT     Override Google Cloud project ID
  --region REGION       Override deployment region  
  --output-dir DIR      Keep generated files in directory
  --validate-only       Only validate configuration, don't deploy
  --verbose, -v         Show detailed output and next steps
```

**Examples:**
```bash
# Basic usage
python prototype.py my-spec.md

# With detailed output
python prototype.py my-spec.md --verbose

# Just validate setup
python prototype.py my-spec.md --validate-only

# Override project
python prototype.py my-spec.md --project my-other-project

# Keep generated files
python prototype.py my-spec.md --output-dir ./generated
```

## Error Handling

The prototype includes comprehensive validation:

- ✅ **API Key Check**: Validates Anthropic API key and permissions
- ✅ **Google Cloud Setup**: Checks gcloud installation and authentication  
- ✅ **Project Access**: Verifies Cloud Run is enabled in your project
- ✅ **Spec Validation**: Ensures your spec file is valid and readable

Run with `--validate-only` to check your setup without deploying.

## Requirements

- Python 3.8+
- Google Cloud SDK (`gcloud` CLI) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- Anthropic API key - [Get one here](https://console.anthropic.com/)
- Google Cloud project with Cloud Run enabled

## Generated Output

The prototype currently generates:
- `index.js` - Express.js Cloud Run function
- `package.json` - Node.js dependencies and configuration

Future versions will generate the full microservice structure outlined in [goals.md](goals.md).