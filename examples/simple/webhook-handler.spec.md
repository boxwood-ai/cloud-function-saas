# Service Name: Webhook Handler
Description: Handle third-party webhooks
Runtime: Node.js 20

## Endpoints

### POST /webhooks/stripe
- Description: Process Stripe payment webhooks
- Input: Stripe webhook payload
- Output: { received: boolean }

### POST /webhooks/github
- Description: Process GitHub webhooks
- Input: GitHub webhook payload  
- Output: { received: boolean }

## Business Logic
- Verify webhook signatures
- Update payment status in database
- Send notifications for important events
- Retry failed processing