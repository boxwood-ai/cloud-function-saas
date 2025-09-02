# Service Name: Test API Service
Description: A simple test API service
Runtime: Node.js 20

## Endpoints

### GET /health
- Description: Health check endpoint
- Input: None
- Output: JSON status object
- Auth: None

### POST /users
- Description: Create a new user
- Input: JSON user object
- Output: Created user with ID
- Auth: Bearer token

## Models

### User
- id: string (required)
- name: string (required)
- email: string (required)
- created_at: datetime (auto-generated)

## Business Logic

Simple user management API with health checks.

## Database

Uses in-memory storage for demo purposes.

## Deployment

Deploy to Google Cloud Run with automatic scaling.