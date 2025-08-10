# Service Name: Payment Webhook Handler
Description: Processes Stripe webhook events for payment notifications and updates
Version: 1.0.0
Runtime: Node.js 20

## Endpoints

### POST /webhooks/stripe
- Description: Handle Stripe webhook events (payment intents, subscriptions, etc.)
- Input: Raw Stripe webhook payload with Stripe-Signature header
- Output: { received: boolean, processed: boolean, eventId: string }
- Auth: Stripe webhook signature validation
- Validation: Stripe signature verification, event deduplication

### POST /webhooks/github
- Description: Handle GitHub webhook events (push, PR, releases)
- Input: GitHub webhook payload with X-GitHub-Event and X-Hub-Signature headers
- Output: { received: boolean, action: string, repository: string }
- Auth: GitHub webhook secret validation
- Validation: GitHub signature verification, supported event types

### POST /webhooks/sendgrid
- Description: Handle SendGrid email event notifications
- Input: Array of SendGrid event objects
- Output: { received: boolean, processed: number, errors: array }
- Auth: SendGrid webhook authentication
- Validation: SendGrid event format, email address validation

### GET /webhooks/health
- Description: Health check with webhook endpoint status
- Input: None
- Output: { status: string, endpoints: object, lastProcessed: timestamp }
- Auth: None required

### GET /webhooks/events/{eventId}
- Description: Get webhook event processing details
- Input: eventId in path
- Output: { eventId: string, source: string, status: string, attempts: number, lastAttempt: timestamp }
- Auth: API key required
- Validation: Valid UUID format for eventId

## Models

### WebhookEvent
- id: UUID (primary key)
- source: enum [stripe, github, sendgrid]
- eventType: string (payment_intent.succeeded, push, delivered, etc.)
- externalId: string (external event ID from webhook provider)
- payload: JSON (original webhook payload)
- signature: string (webhook signature for verification)
- status: enum [received, processing, processed, failed, retrying]
- attempts: integer (processing attempt count)
- maxAttempts: integer (default: 3)
- createdAt: timestamp
- processedAt: timestamp (nullable)
- errorMessage: string (nullable)

### ProcessingResult
- eventId: UUID (foreign key to WebhookEvent)
- action: string (what action was taken)
- success: boolean
- duration: integer (processing time in ms)
- metadata: JSON (action-specific data)
- createdAt: timestamp

## Business Logic

### Stripe Webhook Processing
- Verify webhook signature using Stripe webhook secret
- Handle events: payment_intent.succeeded, payment_intent.failed, subscription.updated
- Update payment status in Firestore
- Send email notifications for successful payments
- Retry failed payment processing up to 3 times

### GitHub Webhook Processing
- Verify webhook signature using HMAC SHA-256
- Handle events: push (to main branch), pull_request.opened, release.published
- Trigger deployment pipeline for main branch pushes
- Send Slack notifications for new releases
- Update project status in database

### SendGrid Webhook Processing
- Process email delivery events: delivered, opened, clicked, bounced, spam_report
- Update email campaign statistics
- Handle bounce management (temporary vs permanent)
- Track email engagement metrics
- Update contact preferences for unsubscribes

### Error Handling and Retries
- Implement exponential backoff for retries (1s, 4s, 16s)
- Dead letter queue for permanently failed events
- Idempotent processing using external event IDs
- Detailed error logging with context
- Alert on high failure rates

### Security
- Validate all webhook signatures before processing
- Rate limiting: 1000 requests per minute per source
- Request body size limit: 1MB
- Timeout protection: 30 seconds max processing time
- IP allowlisting for known webhook sources

## Database
- Type: Firestore
- Collections: webhook_events, processing_results, email_metrics
- Indexes: webhook_events.source, webhook_events.status, webhook_events.createdAt
- TTL: Archive processed events after 30 days

## Deployment
- Platform: Google Cloud Run
- Scaling: 0-50 instances (handle traffic spikes)
- Environment: development, staging, production
- Resources: 512MB RAM, 1 CPU
- Region: us-central1
- Authentication: Allow unauthenticated (validates webhook signatures)
- Timeout: 300 seconds (5 minutes for complex processing)
- Environment Variables:
  - STRIPE_WEBHOOK_SECRET (from Secret Manager)
  - GITHUB_WEBHOOK_SECRET (from Secret Manager)
  - SENDGRID_WEBHOOK_AUTH (from Secret Manager)
  - FIRESTORE_PROJECT_ID
  - SLACK_WEBHOOK_URL
  - EMAIL_SERVICE_URL

## Dependencies
- express: Web framework
- stripe: Stripe API client
- crypto: Built-in crypto for webhook verification
- @google-cloud/firestore: Database client
- @google-cloud/pubsub: For async processing
- node-fetch: HTTP requests for external services
- joi: Request validation
- helmet: Security headers
- express-rate-limit: Rate limiting

## Integrations
- Stripe API for payment status updates
- GitHub API for repository operations
- SendGrid API for email management
- Slack API for notifications
- Google Cloud Pub/Sub for async processing
- Google Cloud Tasks for retry mechanisms

## Monitoring
- Cloud Logging for all webhook events
- Cloud Monitoring metrics for processing rates
- Error rate alerts (>5% failure rate)
- Processing latency monitoring
- Dead letter queue monitoring
- Webhook source availability checks