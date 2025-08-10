# Cloud Function Microservice Generator

A command-line tool that transforms specification documents into fully functional Google Cloud Run microservices using AI-driven code generation.

## Overview

This generator reads a `spec.md` file containing microservice specifications and automatically generates a complete Google Cloud Run function with all necessary components including HTTP handlers, data validation, authentication, and deployment configurations.

## How It Works

### 1. Specification Input
- **Input**: `spec.md` file containing service requirements
- **Format**: Structured markdown with specific sections for different aspects
- **Content**: API endpoints, data models, business logic, deployment requirements

### 2. AI Processing Pipeline

```text
spec.md → Parser → AI Analyzer → Code Generator → Validator → Deploy
```

1. **Parser**: Extracts structured data from the markdown specification
2. **AI Analyzer**: Uses LLM to understand requirements and generate implementation plan
3. **Code Generator**: Creates Cloud Run function with HTTP handlers and business logic
4. **Validator**: Checks generated code for consistency and best practices
5. **Deploy**: Automatically deploys to Google Cloud Run (optional)

### 3. Generated Output Structure

```text
my-microservice/
├── src/
│   ├── index.js           # Main Cloud Run function entry point
│   ├── handlers/          # HTTP route handlers
│   ├── models/            # Data validation schemas
│   ├── services/          # Business logic
│   └── utils/             # Helper functions
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # HTTP endpoint tests
├── deployment/
│   ├── cloudbuild.yaml    # Google Cloud Build config
│   ├── service.yaml       # Cloud Run service config
│   └── env.yaml           # Environment variables
├── docs/
│   ├── api.md             # API documentation
│   └── deployment.md      # Deployment guide
├── package.json           # Dependencies and scripts
├── .gcloudignore          # Files to ignore during deployment
├── Dockerfile             # Container build (optional)
└── README.md              # Microservice documentation
```

## Spec.md Format

The specification file supports two complexity levels:

### 📝 Simple Specification Format
Minimal requirements with AI-generated best practices:

```markdown
# Service Name: My API
Description: Brief description of what the service does
Runtime: Node.js 20

## Endpoints
### GET /users
- Description: Get all users
- Output: { users: array }

## Models
### User
- name: string
- email: string

## Business Logic (optional)
- Basic requirements and constraints
```

### 🔧 Comprehensive Specification Format
Detailed control over all implementation aspects:

#### Required Sections

#### Service Overview

```markdown
# Service Name: User Management Microservice
Description: Handles user authentication, profiles, and permissions
Version: 1.0.0
Runtime: Node.js 20
```

#### API Endpoints
```markdown
## Endpoints

### POST /auth/login
- Description: User authentication
- Input: { email: string, password: string }
- Output: { token: string, user: User }
- Auth: None required

### GET /users/:id
- Description: Get user profile
- Input: User ID in path
- Output: User object
- Auth: Bearer token required
```

#### Data Models
```markdown
## Models

### User
- id: UUID (primary key)
- email: string (unique, required)
- password: string (hashed, required)
- name: string (required)
- role: enum [admin, user] (default: user)
- createdAt: timestamp
- updatedAt: timestamp
```

#### Business Rules
```markdown
## Business Logic

### Authentication
- Passwords must be hashed using bcrypt
- JWT tokens expire after 24 hours
- Failed login attempts are rate limited

### Authorization
- Admins can access all user data
- Users can only access their own data
```

### Optional Sections

#### Database Configuration

```markdown
## Database
- Type: Firestore / Cloud SQL PostgreSQL
- Connection: Cloud SQL Connector
- Environment: separate instances for dev/prod
```

#### Deployment Requirements

```markdown
## Deployment
- Platform: Google Cloud Run
- Scaling: 0-100 instances
- Environment: development, staging, production
- Resources: 512MB RAM, 1 CPU
- Region: us-central1
- Authentication: Cloud IAM
```

## Core Features

### 🚀 **Intelligent Code Generation**

- Context-aware HTTP handler generation for Cloud Run
- Request/response validation middleware
- Error handling and standardized API responses
- Automatic route registration and method handling

### 🔧 **Cloud-Native Integration**

- Google Cloud Run optimized structure
- Cloud Build deployment pipelines
- Environment-based configuration
- Cloud Logging and Monitoring setup

### 📊 **Database Integration**

- Firestore document models and queries
- Cloud SQL connection management
- Input validation with Joi/Zod schemas
- Transaction handling and error recovery

### 🔐 **Security Implementation**

- Google Cloud IAM integration
- JWT token validation middleware
- Request sanitization and rate limiting
- CORS configuration for web clients

### 🚢 **One-Command Deployment**

- Automatic `gcloud` CLI integration
- Environment-specific deployments
- Rollback and version management
- Traffic splitting for canary releases

### 📚 **Documentation Generation**

- OpenAPI 3.0 specification
- Deployment guides with `gcloud` commands
- Environment setup instructions
- API testing examples with curl/Postman

## Usage Workflow

1. **Install CLI Tool**

   ```bash
   npm install -g cloud-function-generator
   # or run directly with npx
   ```

2. **Create Specification**

   ```bash
   # Option 1: Start with a simple spec (AI fills in the details)
   cp examples/simple/user-api.spec.md ./spec.md
   
   # Option 2: Use comprehensive spec (full control)
   cp examples/user-api-nodejs.spec.md ./spec.md
   
   # Option 3: Create from scratch
   touch spec.md
   # Edit with your requirements (see format above)
   ```

3. **Generate Microservice**

   ```bash
   # Generate with automatic best practices (simple specs)
   npx cloud-function-generator generate --mode=smart
   
   # Generate exactly as specified (comprehensive specs)  
   npx cloud-function-generator generate --mode=strict
   
   # Auto-detect spec complexity
   npx cloud-function-generator generate
   ```

4. **Deploy to Cloud Run**

   ```bash
   # Deploy directly (requires gcloud CLI)
   npx cloud-function-generator deploy --env production
   
   # Or deploy manually
   cd my-service
   gcloud run deploy my-service --source .
   ```

## Architecture Components

### Generator Core

- **Spec Parser**: Markdown → JSON structure
- **Template Engine**: Dynamic Cloud Run function generation
- **Validation Engine**: Code quality and Cloud Run compatibility checks
- **CLI Interface**: Command-line tool with options and flags

### AI Integration

- **Context Builder**: Prepares prompts with spec data and Cloud Run patterns
- **Code Generator**: LLM-powered Cloud Function implementation
- **Quality Checker**: Reviews generated code for best practices
- **Cloud Optimizer**: Optimizes for Cloud Run performance and cost

### Google Cloud Integration

- **gcloud CLI Integration**: Automatic deployment commands
- **Cloud Build Templates**: CI/CD pipeline generation
- **IAM Configuration**: Service account and permission setup
- **Monitoring Setup**: Cloud Logging and Error Reporting

## Extension Points

### Custom Templates

- Organization-specific Cloud Run patterns
- Custom middleware and authentication flows
- Industry-specific business logic templates

### Plugin System

- Google Cloud service integrations (Pub/Sub, Storage, BigQuery)
- Third-party API connectors (Stripe, SendGrid, Twilio)
- Monitoring and alerting extensions

### CLI Extensions

- Custom deployment strategies
- Multi-environment management
- Integration with existing CI/CD pipelines

## CLI Commands

### Generate

```bash
npx cloud-function-generator generate [options]

Options:
  --spec, -s      Path to spec.md file (default: ./spec.md)
  --output, -o    Output directory (default: ./generated)
  --mode, -m      Generation mode: smart, strict, auto (default: auto)
  --runtime, -r   Runtime (nodejs20, python311, go121)
  --region        Deployment region (default: us-central1)  
  --dry-run       Show what would be generated without creating files

Generation Modes:
  smart           AI adds best practices to simple specs
  strict          Generate exactly as specified (comprehensive specs)
  auto            Auto-detect spec complexity and choose mode
```

### Deploy

```bash
npx cloud-function-generator deploy [options]

Options:
  --env, -e       Environment (development, staging, production)
  --project, -p   Google Cloud project ID
  --region        Deployment region
  --traffic       Traffic percentage for new revision (default: 100)
```

### Validate

```bash
npx cloud-function-generator validate [options]

Options:
  --spec, -s      Path to spec.md file to validate
  --strict        Enable strict validation rules
```

## Next Steps

1. Implement CLI tool with Commander.js
2. Create specification parser and validator
3. Build Cloud Run function templates
4. Integrate with AI models for code generation
5. Add Google Cloud deployment automation
6. Create comprehensive test suite
7. Add support for multiple runtimes (Node.js, Python, Go)

This tool will dramatically reduce the time from concept to deployed Cloud Run microservice while maintaining high code quality and Google Cloud best practices.