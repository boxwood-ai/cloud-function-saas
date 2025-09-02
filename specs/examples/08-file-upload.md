# Service Name: File Upload Service
Description: Handle file uploads and storage
Runtime: Node.js 20

## Endpoints

### POST /upload
- Description: Upload a file
- Input: multipart/form-data with file
- Output: { fileId: string, url: string, size: number }

### GET /files/:id
- Description: Download file
- Output: File binary data

### DELETE /files/:id
- Description: Delete a file
- Output: { deleted: boolean }

### GET /files
- Description: List uploaded files
- Output: { files: array }

## Models

### File
- id: string (UUID)
- filename: string
- size: number (bytes)
- mimeType: string
- uploadedAt: timestamp