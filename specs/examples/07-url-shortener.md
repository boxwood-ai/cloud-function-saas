# Service Name: URL Shortener
Description: Create and manage short URLs
Runtime: Python 3.11

## Endpoints

### POST /shorten
- Description: Create short URL
- Input: { url: string, custom: string }
- Output: { shortUrl: string, code: string }

### GET /s/:code
- Description: Redirect to original URL
- Output: 301 redirect

### GET /stats/:code
- Description: Get URL statistics
- Output: { clicks: number, created: timestamp }

## Models

### ShortLink
- code: string (unique, 6 chars)
- originalUrl: string (URL format)
- clicks: number (default: 0)
- createdAt: timestamp