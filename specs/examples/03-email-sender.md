# Service Name: Email Notification Service
Description: Send email notifications via API
Runtime: Python 3.11

## Endpoints

### POST /send-email
- Description: Send an email
- Input: { to: string, subject: string, body: string }
- Output: { success: boolean, messageId: string }

### POST /send-bulk
- Description: Send emails to multiple recipients
- Input: { recipients: array, subject: string, body: string }
- Output: { sent: number, failed: number }

## Models

### EmailRequest
- to: string (email format)
- subject: string (max 200 chars)
- body: string (required)