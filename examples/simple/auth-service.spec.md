# Service Name: Auth Service
Description: JWT authentication service
Runtime: Go 1.21

## Endpoints

### POST /token
- Description: Generate JWT token
- Input: { apiKey: string }
- Output: { token: string, expiresIn: number }

### POST /validate
- Description: Validate JWT token
- Input: { token: string }
- Output: { valid: boolean, claims: object }

### GET /jwks
- Description: Public keys for token verification
- Output: JWKS format

## Models

### APIKey
- keyHash: string
- name: string
- active: boolean
- createdAt: timestamp

## Business Logic
- Generate signed JWT tokens
- Validate token signatures
- Support token expiration
- Rate limit requests