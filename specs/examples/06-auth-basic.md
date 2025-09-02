# Service Name: Basic Auth Service
Description: Simple authentication with JWT tokens
Runtime: Node.js 20

## Endpoints

### POST /register
- Description: Create new account
- Input: { email: string, password: string }
- Output: { user: User, token: string }

### POST /login
- Description: Sign in user
- Input: { email: string, password: string }
- Output: { token: string, expiresIn: number }

### GET /verify
- Description: Verify token validity
- Auth: Bearer token required
- Output: { valid: boolean, user: User }

## Models

### User
- id: string (UUID)
- email: string (unique)
- password: string (hashed)
- createdAt: timestamp