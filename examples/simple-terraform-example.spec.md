# Service Name: Weather Alert Service

Description: A simple weather alert API that demonstrates Terraform multi-cloud deployment with basic CRUD operations and external API integration.

Runtime: Node.js 20

## Endpoints

### GET /health
- Description: Health check endpoint
- Output: {"status": "healthy", "service": "weather-alert-service", "timestamp": "ISO8601"}

### GET /alerts
- Description: Get all weather alerts for a location
- Query Parameters:
  - location: city name or coordinates (required)
  - severity: filter by severity level (minor, moderate, severe, extreme)
  - active: filter active alerts only (true/false)
- Output: {"alerts": [AlertModel], "location": "string", "count": number}

### POST /alerts
- Description: Create a custom weather alert
- Input: {"location": "string", "type": "string", "message": "string", "severity": "minor|moderate|severe|extreme"}
- Output: {"alert": AlertModel, "message": "Alert created successfully"}

### GET /alerts/{id}
- Description: Get a specific weather alert by ID
- Path Parameters: id (UUID)
- Output: {"alert": AlertModel}

### DELETE /alerts/{id}
- Description: Delete a weather alert by ID
- Path Parameters: id (UUID)
- Output: {"message": "Alert deleted successfully", "deletedId": "UUID"}

### POST /subscribe
- Description: Subscribe to weather alerts for a location
- Input: {"email": "string", "location": "string", "severity": ["minor", "moderate", "severe", "extreme"]}
- Output: {"subscription": SubscriptionModel, "message": "Subscription created successfully"}

### GET /weather/{location}
- Description: Get current weather conditions for a location
- Path Parameters: location (city name or coordinates)
- Output: {"weather": WeatherModel, "alerts": [AlertModel]}

## Models

### AlertModel
- id: UUID (required, auto-generated)
- location: string (required)
- type: string (required, e.g., "thunderstorm", "flood", "hurricane")
- message: string (required, max 500 characters)
- severity: enum ["minor", "moderate", "severe", "extreme"] (required)
- isActive: boolean (required, default: true)
- createdAt: timestamp (required, auto-generated)
- expiresAt: timestamp (optional)
- source: string (optional, default: "user")

### SubscriptionModel
- id: UUID (required, auto-generated)
- email: string (required, valid email format)
- location: string (required)
- severityFilter: array of strings (required)
- isActive: boolean (required, default: true)
- createdAt: timestamp (required, auto-generated)
- lastNotified: timestamp (optional)

### WeatherModel
- location: string (required)
- temperature: number (required, in Celsius)
- condition: string (required, e.g., "sunny", "cloudy", "rainy")
- humidity: number (required, percentage)
- windSpeed: number (required, km/h)
- pressure: number (required, hPa)
- visibility: number (required, km)
- updatedAt: timestamp (required)

## External Integrations

- Weather API integration for real-time weather data
- Email service for alert notifications
- Optional SMS service for urgent alerts

## Environment Variables

- WEATHER_API_KEY: API key for weather data provider
- EMAIL_SERVICE_API_KEY: API key for email notifications
- DATABASE_URL: Database connection string (optional, uses in-memory for demo)
- PORT: Service port (default: 8080)
- LOG_LEVEL: Logging level (default: info)