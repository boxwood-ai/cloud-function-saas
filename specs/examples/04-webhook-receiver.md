# Service Name: Webhook Receiver
Description: Receive and log webhook events
Runtime: Node.js 20

## Endpoints

### POST /webhook
- Description: Receive webhook payload
- Input: Any JSON payload
- Output: { received: true, id: string }

### GET /events
- Description: List recent webhook events
- Output: { events: array, count: number }

### GET /events/:id
- Description: Get specific event details
- Output: Event object

## Models

### Event
- id: string (UUID)
- payload: object
- headers: object
- receivedAt: timestamp