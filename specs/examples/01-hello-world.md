# Service Name: Hello World API
Description: Simple greeting service
Runtime: Node.js 20

## Endpoints

### GET /
- Description: Say hello
- Output: { message: "Hello World!" }

### GET /greet/:name
- Description: Personalized greeting
- Output: { message: string }