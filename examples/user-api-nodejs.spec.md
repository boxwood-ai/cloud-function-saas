# Service Name: User Management API
Description: RESTful API for user registration, authentication, and profile management
Version: 1.0.0
Runtime: Node.js 20

## Endpoints

### POST /auth/register
- Description: Register a new user account
- Input: { email: string, password: string, name: string }
- Output: { success: boolean, user: { id: string, email: string, name: string }, token: string }
- Auth: None required
- Validation: Email format, password min 8 chars, name required

### POST /auth/login
- Description: Authenticate user and return JWT token
- Input: { email: string, password: string }
- Output: { success: boolean, user: User, token: string, expiresIn: number }
- Auth: None required
- Validation: Email format, password required

### GET /users/profile
- Description: Get current user's profile information
- Input: None (user from JWT token)
- Output: { id: string, email: string, name: string, createdAt: string, updatedAt: string }
- Auth: Bearer token required

### PUT /users/profile
- Description: Update current user's profile
- Input: { name?: string, email?: string }
- Output: { success: boolean, user: User }
- Auth: Bearer token required
- Validation: Email format if provided, name min 2 chars if provided

### DELETE /users/account
- Description: Delete current user's account
- Input: { confirmPassword: string }
- Output: { success: boolean, message: string }
- Auth: Bearer token required
- Validation: Password confirmation required

## Models

### User
- id: UUID (primary key, auto-generated)
- email: string (unique, required, indexed)
- password: string (hashed with bcrypt, required)
- name: string (required, min 2 chars, max 100 chars)
- role: enum [user, admin] (default: user)
- emailVerified: boolean (default: false)
- createdAt: timestamp (auto-generated)
- updatedAt: timestamp (auto-updated)

### LoginAttempt
- id: UUID (primary key)
- email: string (indexed)
- success: boolean
- ipAddress: string
- userAgent: string
- attemptedAt: timestamp

## Business Logic

### Authentication
- Passwords must be hashed using bcrypt with salt rounds of 12
- JWT tokens expire after 24 hours
- Include user ID and role in JWT payload
- Failed login attempts are rate limited (5 attempts per 15 minutes per IP)

### Authorization
- Only authenticated users can access profile endpoints
- Users can only access and modify their own profile data
- Admin role reserved for future admin functionality

### Validation
- Email addresses must be valid format and unique
- Passwords must be at least 8 characters with at least one number
- Names must be 2-100 characters, no special characters except spaces, hyphens, apostrophes
- Rate limiting: 100 requests per minute per IP for auth endpoints

### Error Handling
- Return consistent error format: { success: false, error: string, code: string }
- Log all authentication failures with IP and timestamp
- Sanitize all error messages (no sensitive data exposure)

## Database
- Type: Firestore
- Collections: users, loginAttempts
- Indexes: users.email, loginAttempts.email, loginAttempts.attemptedAt
- Environment: separate instances for dev/staging/prod

## Deployment
- Platform: Google Cloud Run
- Scaling: 0-10 instances
- Environment: development, staging, production
- Resources: 512MB RAM, 1 CPU
- Region: us-central1
- Authentication: Allow unauthenticated (handles auth internally)
- Environment Variables:
  - JWT_SECRET (from Secret Manager)
  - FIRESTORE_PROJECT_ID
  - NODE_ENV

## Dependencies
- express: Web framework
- bcryptjs: Password hashing
- jsonwebtoken: JWT token handling
- joi: Request validation
- @google-cloud/firestore: Database client
- helmet: Security headers
- cors: Cross-origin requests
- express-rate-limit: Rate limiting