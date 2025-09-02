# Service Name: User Management API
Description: A simple REST API for managing user accounts with CRUD operations
Runtime: Node.js 20

## Endpoints

### GET /users
- Description: Retrieve all users
- Output: Array of user objects
- Auth: None

### GET /users/:id
- Description: Retrieve a specific user by ID
- Input: User ID in path parameter
- Output: User object or 404 error
- Auth: None

### POST /users
- Description: Create a new user account
- Input: { name: string, email: string }
- Output: Created user object with generated ID
- Auth: None

### PUT /users/:id
- Description: Update an existing user
- Input: User ID in path, { name?: string, email?: string } in body
- Output: Updated user object or 404 error
- Auth: None

### DELETE /users/:id
- Description: Delete a user account
- Input: User ID in path parameter
- Output: Success message or 404 error
- Auth: None

## Models

### User
- id: string (UUID v4)
- name: string (required, min 2 chars, max 100 chars)
- email: string (required, valid email format, unique)
- createdAt: timestamp (ISO 8601 format)
- updatedAt: timestamp (ISO 8601 format)

## Business Logic
- Email addresses must be unique across all users
- User names must be at least 2 characters long
- All endpoints should return JSON responses
- Include proper HTTP status codes (200, 201, 400, 404, 409, 500)
- Implement basic input validation and sanitization
- Use in-memory storage for simplicity (replace with database in production)

## Database
- Type: In-memory (development only)
- Note: Production deployments should use Cloud SQL or similar managed database

## Deployment
- Platform: Google Cloud Run
- Auto-scaling: Enabled
- CPU: 1 vCPU
- Memory: 512Mi
- Max instances: 10
- Allow unauthenticated requests: Yes (for demo purposes)