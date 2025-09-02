# Example Specifications

These simplified examples demonstrate how to write specs for Cloud Function SaaS. Each spec is 20-50 lines and focuses on a single use case.

## Quick Start

Start with the [template](../template.md) in the parent directory and customize it for your needs.

## Examples

1. **[01-hello-world.md](01-hello-world.md)** - Simplest possible API
2. **[02-todo-list.md](02-todo-list.md)** - Basic CRUD operations
3. **[03-email-sender.md](03-email-sender.md)** - Python service for sending emails
4. **[04-webhook-receiver.md](04-webhook-receiver.md)** - Receive and log webhooks
5. **[05-key-value-store.md](05-key-value-store.md)** - In-memory cache service
6. **[06-auth-basic.md](06-auth-basic.md)** - Simple JWT authentication
7. **[07-url-shortener.md](07-url-shortener.md)** - URL shortening service
8. **[08-file-upload.md](08-file-upload.md)** - File upload and storage

## Spec Structure

Each spec follows this minimal structure:

```markdown
# Service Name: Your Service
Description: One-line description
Runtime: Node.js 20 or Python 3.11

## Endpoints
Define your REST API endpoints with:
- Description
- Input (if needed)
- Output
- Auth (if needed)

## Models (optional)
Define data structures if needed
```

Keep it simple! The AI agents will handle the implementation details.