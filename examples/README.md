# Example Specifications

This directory contains sample `spec.md` files demonstrating different types of microservices that can be generated using the Cloud Function Microservice Generator.

## Available Examples

### 1. User Management API (Node.js)
**File:** `user-api-nodejs.spec.md`

A complete REST API for user authentication and profile management featuring:
- User registration and login endpoints
- JWT token authentication
- Profile management CRUD operations
- Firestore database integration
- Input validation and security best practices

**Use Case:** Backend API for web/mobile applications requiring user management

---

### 2. Data Processing Pipeline (Python)
**File:** `data-processor-python.spec.md`

A data processing microservice that handles CSV file uploads and BigQuery integration:
- File upload and validation endpoints
- Async processing with job status tracking
- BigQuery data loading and transformation
- Cloud Pub/Sub webhook handling
- Error handling and data quality validation

**Use Case:** ETL pipelines, data ingestion, and batch processing workflows

---

### 3. Authentication Service (Go)
**File:** `auth-service-go.spec.md`

A high-performance authentication microservice built for enterprise use:
- JWT token generation and validation
- API key management system
- Token refresh and revocation
- JWKS endpoint for public key distribution
- PostgreSQL database with connection pooling

**Use Case:** Centralized authentication for microservice architectures

---

### 4. Webhook Handler (Node.js)
**File:** `webhook-handler-nodejs.spec.md`

A webhook processing service handling multiple third-party integrations:
- Stripe payment webhook processing
- GitHub repository event handling
- SendGrid email event notifications
- Event deduplication and retry logic
- Comprehensive error handling and monitoring

**Use Case:** Integration hub for third-party service notifications

## How to Use These Examples

1. **Copy an example that matches your needs:**
   ```bash
   cp examples/user-api-nodejs.spec.md ./spec.md
   ```

2. **Customize the specification:**
   - Modify endpoints to match your requirements
   - Update data models and business logic
   - Adjust deployment settings

3. **Generate your microservice:**
   ```bash
   npx cloud-function-generator generate
   ```

## Common Patterns

### REST API Services
- Use Node.js or Go for high-performance APIs
- Implement proper authentication and authorization
- Include comprehensive input validation
- Set up appropriate database connections

### Data Processing
- Use Python for data transformation and analysis
- Implement async processing for large datasets
- Include proper error handling and retry logic
- Set up monitoring for data quality

### Integration Services
- Handle webhook signature verification
- Implement idempotent processing
- Use proper retry mechanisms
- Include comprehensive logging

### Authentication Services
- Use strong cryptographic practices
- Implement proper token management
- Include rate limiting and security measures
- Set up monitoring for security events

## Customization Tips

### Endpoints
- Modify HTTP methods, paths, and parameters
- Add or remove authentication requirements
- Update input/output data structures
- Customize validation rules

### Database
- Change database type (Firestore, Cloud SQL, etc.)
- Modify data models and relationships
- Update indexes and constraints
- Adjust connection settings

### Deployment
- Modify resource allocation (CPU, RAM)
- Update scaling parameters
- Change deployment regions
- Adjust environment variables

### Dependencies
- Add or remove npm/pip/go packages
- Update runtime versions
- Include custom libraries
- Modify security dependencies

## Best Practices

1. **Always specify validation rules** for inputs
2. **Include comprehensive error handling** scenarios  
3. **Set appropriate resource limits** for your workload
4. **Use environment variables** for configuration
5. **Include monitoring and logging** requirements
6. **Specify security requirements** clearly
7. **Document business logic** thoroughly

## Need Help?

- Check the main README.md for detailed specification format
- Review the generated code to understand the patterns
- Modify examples incrementally to learn the system
- Use the `--dry-run` flag to preview generated code