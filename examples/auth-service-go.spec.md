# Service Name: Authentication Service
Description: High-performance JWT authentication and authorization service
Version: 1.0.0
Runtime: Go 1.21

## Endpoints

### POST /auth/token
- Description: Generate JWT token from API key or user credentials
- Input: { apiKey?: string, username?: string, password?: string, scope?: string }
- Output: { access_token: string, token_type: string, expires_in: number, scope: string }
- Auth: None required (validates API key or credentials)
- Validation: Either apiKey OR (username + password) required

### POST /auth/refresh
- Description: Refresh an expired JWT token using refresh token
- Input: { refresh_token: string }
- Output: { access_token: string, token_type: string, expires_in: number }
- Auth: None required (validates refresh token)
- Validation: Valid refresh token format

### POST /auth/validate
- Description: Validate JWT token and return claims
- Input: { token: string }
- Output: { valid: boolean, claims?: object, expires_at?: number }
- Auth: None required
- Validation: Valid JWT format

### POST /auth/revoke
- Description: Revoke a JWT token (add to blacklist)
- Input: { token: string }
- Output: { success: boolean, message: string }
- Auth: Bearer token required (admin scope)
- Validation: Valid JWT format

### GET /auth/jwks
- Description: JSON Web Key Set for token verification
- Input: None
- Output: JWKS format with public keys
- Auth: None required
- Caching: 1 hour cache headers

## Models

### APIKey
- id: UUID (primary key)
- keyHash: string (SHA-256 hashed API key)
- name: string (human-readable name)
- scope: string (space-separated permissions)
- clientId: string (associated client/service)
- active: boolean
- lastUsed: timestamp (nullable)
- expiresAt: timestamp (nullable)
- createdAt: timestamp

### RefreshToken
- id: UUID (primary key)
- tokenHash: string (SHA-256 hashed token)
- userId: string (associated user ID)
- clientId: string (associated client)
- scope: string
- active: boolean
- expiresAt: timestamp
- createdAt: timestamp

### TokenBlacklist
- jti: string (JWT ID, primary key)
- expiresAt: timestamp (when original token expires)
- revokedAt: timestamp
- reason: string (revocation reason)

## Business Logic

### Token Generation
- JWT tokens expire after 15 minutes for access tokens
- Refresh tokens expire after 30 days
- Include standard claims: iss, aud, exp, iat, jti, sub
- Custom claims: scope, client_id, user_type
- Sign tokens using RS256 algorithm with rotating keys

### API Key Authentication
- API keys are 32-byte random values, base64-encoded
- Store SHA-256 hash of API key, never plaintext
- Support scoped permissions (read:users, write:orders, admin:*)
- Rate limit: 1000 requests per minute per API key
- Track last used timestamp for monitoring

### Token Validation
- Verify signature using public keys from JWKS endpoint
- Check expiration and not-before claims
- Validate against blacklist for revoked tokens
- Support multiple key rotation (up to 3 active keys)
- Cache valid tokens for 30 seconds to reduce database load

### Security Features
- Implement token rotation for refresh tokens
- Automatic key rotation every 90 days
- Rate limiting: 100 auth requests per minute per IP
- Audit logging for all authentication events
- Fail2ban integration for repeated failures

## Database
- Type: Cloud SQL PostgreSQL
- Tables: api_keys, refresh_tokens, token_blacklist, audit_logs
- Indexes: api_keys.key_hash, refresh_tokens.token_hash, token_blacklist.jti
- Connection pooling: 10-50 connections based on load

## Deployment
- Platform: Google Cloud Run
- Scaling: 1-100 instances (always minimum 1 for availability)
- Environment: development, staging, production
- Resources: 256MB RAM, 1 CPU (optimized for high throughput)
- Region: us-central1
- Authentication: Allow unauthenticated (handles auth validation)
- Environment Variables:
  - JWT_PRIVATE_KEY (from Secret Manager)
  - JWT_PUBLIC_KEY (from Secret Manager)
  - DATABASE_URL (Cloud SQL connection string)
  - REDIS_URL (for token caching)

## Dependencies
- gin-gonic/gin: Web framework
- golang-jwt/jwt: JWT handling
- lib/pq: PostgreSQL driver
- go-redis/redis: Redis client for caching
- google.golang.org/api: Google Cloud APIs
- uber-go/zap: Structured logging
- golang.org/x/crypto: Cryptographic functions
- golang.org/x/time/rate: Rate limiting

## Performance Optimizations
- In-memory LRU cache for frequently validated tokens
- Redis cache for API key lookups (1 hour TTL)
- Database connection pooling with prepared statements
- Horizontal scaling with stateless design
- GZIP compression for JWKS endpoint
- Health check endpoint with dependency status

## Monitoring
- Prometheus metrics for token validation rates
- Cloud Logging for audit events
- Cloud Monitoring alerts for high error rates
- Token expiration and rotation monitoring
- API key usage analytics