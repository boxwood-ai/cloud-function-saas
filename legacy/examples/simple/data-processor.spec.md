# Service Name: CSV Processor
Description: Process CSV files and save to database
Runtime: Python 3.11

## Endpoints

### POST /upload
- Description: Upload and process CSV file
- Input: multipart file upload
- Output: { success: boolean, rowCount: number }

### GET /status/{jobId}
- Description: Check processing status
- Output: { status: string, progress: number }

## Models

### ProcessingJob
- filename: string
- status: enum [pending, processing, completed, failed]
- rowCount: integer
- createdAt: timestamp

## Business Logic
- Accept CSV files up to 10MB
- Validate data format
- Save processed data to database
- Send email notification when complete