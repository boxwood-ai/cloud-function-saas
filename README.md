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

### 1. Setup
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and GCP project
```

### 2. Create a Spec
```bash
# Use the example or create your own
cp example-spec.md my-service-spec.md
# Edit my-service-spec.md with your requirements
```

### 3. Generate & Deploy
```bash
# Deploy to Cloud Run
python prototype.py my-service-spec.md

# Or specify project explicitly
python prototype.py my-service-spec.md --project my-gcp-project
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

## Requirements

- Python 3.8+
- Google Cloud SDK (`gcloud` CLI)
- Anthropic API key
- Google Cloud project with Cloud Run enabled

## Generated Output

The prototype currently generates:
- `index.js` - Express.js Cloud Run function
- `package.json` - Node.js dependencies and configuration

Future versions will generate the full microservice structure outlined in [goals.md](goals.md).