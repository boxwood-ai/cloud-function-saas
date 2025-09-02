# 📋 Writing Specifications

Cloud Function SaaS uses a simple, intuitive markdown format that Claude AI can understand and transform into code.

## Basic Spec Structure

```markdown
# Service Name: Your API Name

Description: What your service does
Runtime: Node.js 20

## Endpoints

### GET /resource

- Description: What this endpoint does
- Output: { expected: "response format" }

### POST /resource

- Description: Create new resource
- Input: { required: "input format" }
- Output: { created: "resource" }

## Models

### ResourceModel

- field1: string (required)
- field2: number (optional)
- createdAt: timestamp
```

## Detailed Specification Format

For more complex services, you can use these additional sections:

### Service Overview

```markdown
# Service Name: Advanced User Management API

Description: Comprehensive user management with authentication and authorization
Runtime: Node.js 20
Port: 8080 (optional)
Memory: 512Mi (optional)
CPU: 1000m (optional)
```

### Endpoint Specifications

````markdown
## Endpoints

### GET /users

- Description: Retrieve all users with pagination
- Authentication: Bearer token required
- Parameters:
  - page: number (optional, default: 1)
  - limit: number (optional, default: 10)
  - sort: string (optional, default: "createdAt")
- Output:
  ```json
  {
    "users": [User],
    "pagination": {
      "page": number,
      "limit": number,
      "total": number,
      "pages": number
    }
  }
  ```
````

- Errors:
  - 401: Unauthorized
  - 400: Invalid parameters

### POST /users

- Description: Create a new user account
- Authentication: Admin token required
- Input:
  ```json
  {
    "name": "string (required, min 2, max 100)",
    "email": "string (required, email format)",
    "role": "string (optional, enum: [user, admin], default: user)",
    "password": "string (required, min 8)"
  }
  ```
- Output:
  ```json
  {
    "user": User,
    "message": "User created successfully"
  }
  ```
- Validation:
  - Email must be unique
  - Password must contain uppercase, lowercase, number
- Errors:
  - 400: Validation failed
  - 409: Email already exists

````

### Data Models
```markdown
## Models

### User
- id: string (uuid, auto-generated)
- name: string (required, min 2, max 100)
- email: string (required, unique, email format)
- role: string (enum: [user, admin], default: user)
- password: string (required, hashed, min 8)
- emailVerified: boolean (default: false)
- createdAt: timestamp (auto-generated)
- updatedAt: timestamp (auto-generated)

### AuthToken
- token: string (jwt)
- userId: string (references User.id)
- expiresAt: timestamp
- type: string (enum: [access, refresh])
````

### Business Rules

```markdown
## Business Logic

### Authentication Rules

- All endpoints except `/health` require authentication
- Admin endpoints require admin role
- Tokens expire after 24 hours
- Email verification required for sensitive operations

### Validation Rules

- Passwords must meet complexity requirements
- Email addresses must be unique across the system
- User names are case-insensitive for uniqueness
- Rate limiting: 100 requests per minute per IP

### Data Processing

- Passwords are hashed using bcrypt
- User data is sanitized before storage
- Soft delete for user accounts (mark as deleted)
- Audit log for all user modifications
```

### Database Configuration

```markdown
## Database

### Type

Firestore (NoSQL document database)

### Collections

- users: User documents
- tokens: AuthToken documents
- audit_logs: Activity tracking

### Indexes

- users.email (unique)
- users.role
- tokens.userId
- audit_logs.timestamp

### Backup

- Daily automated backups
- 30-day retention policy
```

### Environment Configuration

```markdown
## Environment

### Required Variables

- JWT_SECRET: string (for token signing)
- ADMIN_EMAIL: string (initial admin user)
- SMTP_HOST: string (for email verification)
- SMTP_PORT: number
- SMTP_USER: string
- SMTP_PASS: string

### Optional Variables

- LOG_LEVEL: string (default: info)
- RATE_LIMIT_MAX: number (default: 100)
- TOKEN_EXPIRY: string (default: 24h)
```

## Example Specifications

### Simple User API

```markdown
# Service Name: Simple User API

Description: Basic CRUD operations for user management
Runtime: Node.js 20

## Endpoints

### GET /users

- Description: Get all users
- Output: { users: [User] }

### POST /users

- Description: Create new user
- Input: { name: string, email: string }
- Output: { user: User }

### GET /users/:id

- Description: Get user by ID
- Output: { user: User }

### PUT /users/:id

- Description: Update user
- Input: { name?: string, email?: string }
- Output: { user: User }

### DELETE /users/:id

- Description: Delete user
- Output: { message: string }

## Models

### User

- id: string (auto-generated)
- name: string (required)
- email: string (required, unique)
- createdAt: timestamp
- updatedAt: timestamp
```

### Authentication Service

```markdown
# Service Name: JWT Authentication Service

Description: Secure authentication service with JWT tokens
Runtime: Node.js 20

## Endpoints

### POST /auth/register

- Description: Register new user account
- Input: { email: string, password: string, name: string }
- Output: { user: User, token: string }

### POST /auth/login

- Description: Login with email and password
- Input: { email: string, password: string }
- Output: { user: User, token: string }

### POST /auth/refresh

- Description: Refresh authentication token
- Authentication: Bearer token required
- Output: { token: string }

### GET /auth/me

- Description: Get current user profile
- Authentication: Bearer token required
- Output: { user: User }

## Models

### User

- id: string (uuid)
- email: string (unique, email format)
- password: string (hashed, min 8)
- name: string (required)
- role: string (enum: [user, admin])
- createdAt: timestamp
- updatedAt: timestamp

## Business Logic

### Security Rules

- Passwords hashed with bcrypt
- JWT tokens expire in 24 hours
- Rate limiting: 5 login attempts per minute
- Email verification required for new accounts
```

### Data Processing Pipeline

````markdown
# Service Name: Data Processing Pipeline

Description: Asynchronous data processing with queue management
Runtime: Python 3.9

## Endpoints

### POST /jobs

- Description: Submit new processing job
- Input:
  ```json
  {
    "type": "string (required, enum: [image_resize, data_transform, report_generate])",
    "data": "object (required, varies by job type)",
    "priority": "string (optional, enum: [low, normal, high], default: normal)",
    "callback_url": "string (optional, webhook URL)"
  }
  ```
````

- Output: { jobId: string, status: string }

### GET /jobs/:id

- Description: Get job status and results
- Output:
  ```json
  {
    "job": {
      "id": "string",
      "type": "string",
      "status": "string (enum: [queued, processing, completed, failed])",
      "progress": "number (0-100)",
      "result": "object (if completed)",
      "error": "string (if failed)",
      "createdAt": "timestamp",
      "completedAt": "timestamp (if completed)"
    }
  }
  ```

### GET /jobs

- Description: List jobs with filtering
- Parameters:
  - status: string (optional)
  - type: string (optional)
  - limit: number (optional, default: 20)
  - offset: number (optional, default: 0)
- Output: { jobs: [Job], total: number }

## Models

### Job

- id: string (uuid)
- type: string (enum: [image_resize, data_transform, report_generate])
- status: string (enum: [queued, processing, completed, failed])
- data: object (varies by job type)
- result: object (processing output)
- error: string (error message if failed)
- priority: string (enum: [low, normal, high])
- progress: number (0-100)
- callback_url: string (optional)
- createdAt: timestamp
- updatedAt: timestamp
- completedAt: timestamp

## Business Logic

### Processing Rules

- High priority jobs processed first
- Maximum 10 concurrent jobs
- Jobs timeout after 30 minutes
- Failed jobs retry up to 3 times
- Callback webhooks sent on completion/failure

````

## Best Practices

### 1. Clear Descriptions
- Use descriptive service names
- Explain what each endpoint does
- Document expected behavior

### 2. Detailed Data Models
- Specify field types and constraints
- Include validation rules
- Document relationships between models

### 3. Authentication & Security
- Specify authentication requirements per endpoint
- Include authorization rules
- Document rate limiting and security measures

### 4. Error Handling
- List possible error responses
- Include HTTP status codes
- Provide meaningful error messages

### 5. Validation Rules
- Specify input validation requirements
- Include business logic constraints
- Document data processing rules

### 6. Environment Configuration
- List required environment variables
- Include optional configuration
- Provide sensible defaults

## Common Patterns

### REST API Patterns
```markdown
# RESTful Resource Management
GET    /resources      # List all
POST   /resources      # Create new
GET    /resources/:id  # Get by ID
PUT    /resources/:id  # Update by ID
DELETE /resources/:id  # Delete by ID
````

### Authentication Patterns

```markdown
# JWT Authentication

POST /auth/register # Register new user
POST /auth/login # Login user
POST /auth/refresh # Refresh token
GET /auth/me # Get current user
POST /auth/logout # Logout user
```

### Health Check Patterns

```markdown
# Service Health

GET /health # Basic health check
GET /health/detailed # Detailed system status
```

## Validation Tips

Use `--validate-only` to check your specification before deploying:

```bash
python prototype.py my-spec.md --validate-only
```

This will verify:

- Specification format is correct
- Required sections are present
- Data models are well-defined
- Endpoints are properly structured
- Authentication setup is valid
