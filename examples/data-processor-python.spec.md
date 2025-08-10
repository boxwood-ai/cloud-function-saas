# Service Name: Data Processing Pipeline
Description: Processes uploaded CSV files, validates data, and exports to BigQuery
Version: 1.0.0
Runtime: Python 3.11

## Endpoints

### POST /process/upload
- Description: Upload and process a CSV file
- Input: multipart/form-data with file field + { dataset: string, table: string, validateOnly?: boolean }
- Output: { success: boolean, jobId: string, rowCount: number, validationErrors?: array }
- Auth: Bearer token required (service-to-service)
- Validation: File must be CSV, max 50MB, required headers validation

### GET /process/status/{jobId}
- Description: Get processing job status and results
- Input: jobId in path
- Output: { jobId: string, status: enum, progress: number, errors?: array, completedAt?: string }
- Auth: Bearer token required
- Validation: Valid UUID format for jobId

### POST /process/webhook
- Description: Handle Cloud Storage object creation events
- Input: Cloud Pub/Sub message with storage event data
- Output: { success: boolean, message: string }
- Auth: Cloud Pub/Sub service account
- Validation: Valid Pub/Sub message format

### GET /process/health
- Description: Health check endpoint
- Input: None
- Output: { status: string, timestamp: string, version: string }
- Auth: None required

## Models

### ProcessingJob
- id: UUID (primary key)
- filename: string (original filename)
- gcsPath: string (Cloud Storage object path)
- dataset: string (BigQuery dataset)
- table: string (BigQuery table name)
- status: enum [pending, processing, completed, failed]
- rowCount: integer (total rows processed)
- validRowCount: integer (valid rows)
- errorCount: integer (rows with errors)
- errors: array (validation error details)
- createdAt: timestamp
- completedAt: timestamp (nullable)
- processedBy: string (service account email)

### ValidationError
- row: integer (row number)
- column: string (column name)
- value: string (invalid value)
- error: string (error description)
- severity: enum [warning, error]

## Business Logic

### File Processing
- Accept only CSV files with UTF-8 encoding
- Maximum file size: 50MB
- Required columns: id, name, email, created_date
- Validate email format, date format (ISO 8601), ID as positive integer
- Skip empty rows, log warnings for malformed rows

### Data Validation
- Email: RFC 5322 compliant format
- Date: ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
- ID: Positive integer, unique within file
- Name: 1-255 characters, no special characters except spaces, hyphens, apostrophes
- Reject files with >25% invalid rows

### BigQuery Integration
- Create table if it doesn't exist with appropriate schema
- Use streaming inserts for real-time processing
- Handle duplicate detection using ID field
- Create separate error table for rejected rows
- Partition tables by processing date

### Error Handling
- Retry failed BigQuery operations up to 3 times with exponential backoff
- Store validation errors in Firestore for later review
- Send failure notifications to Cloud Logging
- Continue processing valid rows even if some rows fail

## Database
- Type: Firestore + BigQuery
- Firestore Collections: processing_jobs, validation_errors
- BigQuery: Destination datasets for processed data
- Indexes: processing_jobs.status, processing_jobs.createdAt

## Deployment
- Platform: Google Cloud Run
- Scaling: 0-20 instances
- Environment: development, staging, production
- Resources: 2GB RAM, 2 CPU (for large file processing)
- Region: us-central1
- Authentication: Require authentication (service-to-service)
- Timeout: 900 seconds (15 minutes for large files)
- Environment Variables:
  - GOOGLE_CLOUD_PROJECT
  - BIGQUERY_DATASET_PREFIX
  - FIRESTORE_PROJECT_ID
  - STORAGE_BUCKET_NAME

## Dependencies
- fastapi: Web framework
- pandas: Data processing
- google-cloud-bigquery: BigQuery client
- google-cloud-firestore: Firestore client
- google-cloud-storage: Cloud Storage client
- google-cloud-pubsub: Pub/Sub client
- pydantic: Data validation
- python-multipart: File upload handling
- uvicorn: ASGI server

## Cloud Resources
- Cloud Storage bucket for temporary file storage
- BigQuery dataset for processed data
- Pub/Sub topic for async processing triggers
- Cloud Scheduler for cleanup jobs (delete old temp files)
- Secret Manager for API keys and sensitive configuration