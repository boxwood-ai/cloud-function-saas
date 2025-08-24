# Terraform Integration Architecture

## Current Architecture Analysis

**Current Flow:**
```
spec.md → SpecParser → CodeGenerator (Claude AI) → CloudRunDeployer → GCP Cloud Run
```

**Generated Files:**
- `package.json` (Node.js dependencies)
- `index.js` (Express.js server)
- `Dockerfile` (Container definition)

## New Terraform-Powered Architecture

**New Flow:**
```
spec.md → SpecParser → TerraformCodeGenerator (Claude AI) → TerraformDeployer → Multi-Cloud
```

**Generated Files:**
- Application code (same as before)
- `main.tf` (Terraform configuration)
- `variables.tf` (Cloud-specific variables)
- `outputs.tf` (Service URLs and endpoints)
- `terraform.tfvars` (Environment values)

## Key Design Decisions

### 1. Provider Selection Strategy
```python
# CLI Usage Examples:
python prototype.py spec.md --provider gcp          # GCP only
python prototype.py spec.md --provider aws          # AWS only  
python prototype.py spec.md --provider both         # Both clouds
python prototype.py spec.md --provider gcp,aws      # Both clouds (alt syntax)
```

### 2. Terraform Module Structure
```
terraform/
├── modules/
│   ├── gcp-serverless/
│   │   ├── main.tf       # Cloud Run configuration
│   │   ├── variables.tf  # GCP-specific variables
│   │   └── outputs.tf    # Cloud Run URL, etc.
│   ├── aws-serverless/
│   │   ├── main.tf       # Fargate/ECS configuration
│   │   ├── variables.tf  # AWS-specific variables
│   │   └── outputs.tf    # ALB URL, etc.
│   └── shared/
│       ├── main.tf       # Common resources
│       ├── variables.tf  # Shared variables
│       └── outputs.tf    # Shared outputs
```

### 3. Generated Terraform Configuration
For each deployment, generate a customized `main.tf` that:
- Imports appropriate modules based on provider selection
- Configures provider authentication
- Sets up container registries and build processes
- Deploys serverless containers with proper networking

### 4. State Management
- **Local State**: Default for development/testing
- **Remote State**: Optional S3/GCS backend for production
- **Workspace Support**: Separate states per environment

### 5. Authentication Strategy
- **GCP**: Use existing ADC/gcloud CLI integration
- **AWS**: AWS CLI credentials or IAM roles
- **Multi-cloud**: Support both simultaneously

## Implementation Components

### 1. TerraformCodeGenerator
Extends existing CodeGenerator to produce Terraform configs alongside application code.

### 2. TerraformDeployer
Replaces CloudRunDeployer with Terraform orchestration layer.

### 3. Cloud Provider Modules
Pre-built Terraform modules for each cloud platform.

### 4. CLI Updates
Add provider selection and Terraform-specific options.

## Backwards Compatibility

Maintain existing CloudRunDeployer for users who don't want Terraform complexity:
```python
python prototype.py spec.md --legacy-deploy  # Use old CloudRunDeployer
```