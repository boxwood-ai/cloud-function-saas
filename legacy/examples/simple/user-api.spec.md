# Service Name: User API
Description: Simple user management API
Runtime: Node.js 20

## Endpoints

### POST /register
- Description: Register new user
- Input: { email: string, password: string, name: string }
- Output: { user: object, token: string }

### POST /login
- Description: User login
- Input: { email: string, password: string }
- Output: { user: object, token: string }

### GET /profile
- Description: Get user profile
- Auth: Bearer token required
- Output: { user: object }

### PUT /profile
- Description: Update user profile
- Auth: Bearer token required
- Input: { name?: string, email?: string }
- Output: { user: object }

## Models

### User
- email: string (unique, required)
- password: string (hashed)
- name: string (required)
- createdAt: timestamp