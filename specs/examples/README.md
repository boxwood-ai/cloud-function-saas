# Example Specifications

This directory contains sample `spec.md` files demonstrating different types of microservices that can be generated using the Cloud Function Microservice Generator.

## Specification Complexity Levels

### 📝 Simple Specs (`/simple/` directory)
Minimal specifications with just the essential requirements. The AI generator will:
- Automatically choose best practices and patterns
- Add comprehensive error handling and validation
- Select appropriate dependencies and configurations
- Generate production-ready security features
- Include standard monitoring and deployment settings

**Use when:** You want to get started quickly with sensible defaults.

### 🔧 Comprehensive Specs (main directory)
Detailed specifications that give you full control over every aspect:
- Explicit validation rules and error handling
- Specific dependency and configuration choices
- Custom business logic and security requirements
- Detailed deployment and resource specifications
- Precise integration and monitoring setup

**Use when:** You need specific patterns, integrations, or have exact requirements.

## Available Examples

### 1. User Management API (Node.js)
**Simple:** `simple/user-api.spec.md` | **Comprehensive:** `user-api-nodejs.spec.md`

REST API for user authentication and profile management:
- User registration and login endpoints
- JWT token authentication  
- Profile management CRUD operations
- Database integration and validation

**Use Case:** Backend API for web/mobile applications

---

### 2. Data Processing Pipeline (Python)
**Simple:** `simple/data-processor.spec.md` | **Comprehensive:** `data-processor-python.spec.md`

Data processing microservice for file handling:
- File upload and validation endpoints
- Async processing with job status tracking
- Database integration and error handling
- Email notifications

**Use Case:** ETL pipelines, data ingestion, batch processing

---

### 3. Authentication Service (Go)
**Simple:** `simple/auth-service.spec.md` | **Comprehensive:** `auth-service-go.spec.md`

High-performance authentication microservice:
- JWT token generation and validation
- API key management system
- Public key distribution (JWKS)
- Rate limiting and security

**Use Case:** Centralized authentication for microservices

---

### 4. Webhook Handler (Node.js)  
**Simple:** `simple/webhook-handler.spec.md` | **Comprehensive:** `webhook-handler-nodejs.spec.md`

Webhook processing service for third-party integrations:
- Multiple webhook provider support
- Signature verification and security
- Event processing and notifications
- Retry logic and error handling

**Use Case:** Integration hub for external services

## How to Use These Examples

1. **Choose your complexity level:**
   ```bash
   # For quick start with defaults
   cp examples/simple/user-api.spec.md ./spec.md
   
   # For full control over implementation  
   cp examples/user-api-nodejs.spec.md ./spec.md
   ```

2. **Customize the specification (optional for simple specs):**
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