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

### GET /users/:id
- Description: Get user by ID
- Input: User ID in path
- Output: User object

## Models
### User
- id: string (UUID)
- name: string (required)
- email: string (required, unique)
- createdAt: timestamp