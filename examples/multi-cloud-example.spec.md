# Service Name: Multi-Cloud Task Manager API

Description: A task management API that demonstrates multi-cloud deployment capabilities with full CRUD operations, authentication, and real-time notifications.

Runtime: Node.js 20

Environment: production

## Endpoints

### GET /health
- Description: Health check endpoint for load balancers and monitoring
- Output: {"status": "healthy", "timestamp": "ISO8601", "version": "1.0.0"}

### GET /tasks
- Description: Retrieve all tasks for the authenticated user with optional filtering
- Query Parameters:
  - status: filter by task status (pending, in_progress, completed)
  - priority: filter by priority level (low, medium, high, urgent)
  - limit: maximum number of tasks to return (default: 50)
  - offset: pagination offset (default: 0)
- Output: {"tasks": [TaskModel], "total": number, "limit": number, "offset": number}

### POST /tasks
- Description: Create a new task for the authenticated user
- Input: {"title": "string", "description": "string", "priority": "low|medium|high|urgent", "dueDate": "ISO8601"}
- Output: {"task": TaskModel, "message": "Task created successfully"}

### GET /tasks/{id}
- Description: Retrieve a specific task by ID
- Path Parameters: id (UUID)
- Output: {"task": TaskModel}

### PUT /tasks/{id}
- Description: Update an existing task
- Path Parameters: id (UUID)
- Input: {"title": "string", "description": "string", "status": "pending|in_progress|completed", "priority": "low|medium|high|urgent", "dueDate": "ISO8601"}
- Output: {"task": TaskModel, "message": "Task updated successfully"}

### DELETE /tasks/{id}
- Description: Delete a task by ID
- Path Parameters: id (UUID)
- Output: {"message": "Task deleted successfully", "deletedId": "UUID"}

### POST /tasks/{id}/comments
- Description: Add a comment to a specific task
- Path Parameters: id (UUID)
- Input: {"comment": "string", "author": "string"}
- Output: {"comment": CommentModel, "message": "Comment added successfully"}

### GET /tasks/{id}/comments
- Description: Retrieve all comments for a specific task
- Path Parameters: id (UUID)
- Output: {"comments": [CommentModel], "taskId": "UUID"}

### POST /auth/login
- Description: Authenticate user and return JWT token
- Input: {"email": "string", "password": "string"}
- Output: {"token": "JWT_string", "user": UserModel, "expiresIn": number}

### POST /auth/logout
- Description: Logout user and invalidate token
- Headers: Authorization: Bearer {token}
- Output: {"message": "Logged out successfully"}

### GET /user/profile
- Description: Get current user profile information
- Headers: Authorization: Bearer {token}
- Output: {"user": UserModel}

### PUT /user/profile
- Description: Update user profile information
- Headers: Authorization: Bearer {token}
- Input: {"name": "string", "email": "string", "preferences": PreferencesModel}
- Output: {"user": UserModel, "message": "Profile updated successfully"}

### GET /analytics/dashboard
- Description: Get task analytics and dashboard data for the user
- Headers: Authorization: Bearer {token}
- Query Parameters:
  - timeRange: analysis time range (7d, 30d, 90d, 1y)
- Output: {"analytics": AnalyticsModel, "charts": ChartDataModel}

### POST /notifications/webhook
- Description: Webhook endpoint for external integrations
- Headers: X-Webhook-Secret: {secret}
- Input: {"event": "string", "data": object, "timestamp": "ISO8601"}
- Output: {"received": true, "processedAt": "ISO8601"}

## Models

### TaskModel
- id: UUID (required, auto-generated)
- title: string (required, max 200 characters)
- description: string (optional, max 2000 characters)
- status: enum ["pending", "in_progress", "completed"] (required, default: "pending")
- priority: enum ["low", "medium", "high", "urgent"] (required, default: "medium")
- createdAt: timestamp (required, auto-generated)
- updatedAt: timestamp (required, auto-updated)
- dueDate: timestamp (optional)
- userId: UUID (required, foreign key)
- tags: array of strings (optional)
- estimatedHours: number (optional)
- completedAt: timestamp (optional, set when status becomes "completed")

### CommentModel
- id: UUID (required, auto-generated)
- taskId: UUID (required, foreign key)
- comment: string (required, max 1000 characters)
- author: string (required, max 100 characters)
- createdAt: timestamp (required, auto-generated)
- updatedAt: timestamp (required, auto-updated)

### UserModel
- id: UUID (required, auto-generated)
- name: string (required, max 100 characters)
- email: string (required, unique, valid email format)
- createdAt: timestamp (required, auto-generated)
- updatedAt: timestamp (required, auto-updated)
- lastLoginAt: timestamp (optional)
- preferences: PreferencesModel (optional)
- isActive: boolean (required, default: true)

### PreferencesModel
- theme: enum ["light", "dark", "system"] (default: "system")
- notifications: object (default: {"email": true, "push": false})
- timezone: string (default: "UTC")
- dateFormat: enum ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"] (default: "MM/DD/YYYY")

### AnalyticsModel
- totalTasks: number
- completedTasks: number
- pendingTasks: number
- overdueTasks: number
- completionRate: number (percentage)
- averageCompletionTime: number (hours)
- productivityScore: number (0-100)
- tasksCompletedThisWeek: number
- tasksCompletedThisMonth: number

### ChartDataModel
- taskStatusDistribution: object
- priorityDistribution: object
- completionTrend: array of objects
- productivityTimeline: array of objects

## Security Requirements

- JWT-based authentication for protected endpoints
- Password hashing using bcrypt with salt rounds >= 12
- Rate limiting: 100 requests per minute per IP
- Input validation and sanitization for all endpoints
- CORS configuration for web applications
- Security headers (helmet.js)
- API key authentication for webhook endpoints

## Performance Requirements

- Response time < 200ms for CRUD operations
- Response time < 500ms for analytics endpoints
- Support for 1000+ concurrent users
- Database connection pooling
- Redis caching for frequently accessed data
- Gzip compression for responses
- CDN integration for static assets

## Monitoring and Logging

- Structured JSON logging with correlation IDs
- Request/response logging with performance metrics
- Error tracking and alerting
- Health check endpoint with detailed status
- Metrics collection (request count, response times, error rates)
- Custom business metrics (tasks created/completed per hour)

## Multi-Cloud Configuration

This service is designed to be deployed across multiple cloud platforms:

### Google Cloud Platform
- Cloud Run for serverless container hosting
- Cloud SQL PostgreSQL for data persistence
- Cloud Memorystore Redis for caching
- Cloud Monitoring for observability
- Cloud Load Balancing for high availability

### Amazon Web Services
- ECS Fargate for container orchestration
- RDS PostgreSQL for data persistence
- ElastiCache Redis for caching
- CloudWatch for monitoring and logging
- Application Load Balancer for traffic distribution

### Database Schema
The service expects a PostgreSQL database with the following tables:
- users (user authentication and profiles)
- tasks (main task data)
- comments (task comments and annotations)
- sessions (active user sessions for JWT management)

### Environment Variables
Required environment variables:
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string
- JWT_SECRET: Secret key for JWT token signing
- CORS_ORIGIN: Allowed CORS origins
- LOG_LEVEL: Logging level (debug, info, warn, error)
- NODE_ENV: Environment (development, staging, production)