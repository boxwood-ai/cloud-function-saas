# Service Name: Key-Value Store
Description: Simple in-memory cache service
Runtime: Node.js 20

## Endpoints

### GET /store/:key
- Description: Get value by key
- Output: { key: string, value: any }

### PUT /store/:key
- Description: Set or update value
- Input: { value: any, ttl: number }
- Output: { success: boolean }

### DELETE /store/:key
- Description: Delete a key
- Output: { deleted: boolean }

### GET /store
- Description: List all keys
- Output: { keys: array }