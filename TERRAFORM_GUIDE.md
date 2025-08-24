# 🚀 Terraform Multi-Cloud Deployment Guide

Cloud Function SaaS now supports multi-cloud deployments using Terraform! Deploy your AI-generated microservices to Google Cloud Platform, Amazon Web Services, or both simultaneously.

## ✨ New Features

- **Multi-Cloud Support**: Deploy to GCP, AWS, or both clouds simultaneously
- **Terraform Infrastructure as Code**: All infrastructure defined and versioned as code
- **Smart State Management**: Automatic backend configuration and state management
- **Provider-Specific Optimizations**: Cloud-native configurations for each platform
- **Backwards Compatibility**: Legacy Cloud Run deployment still available

## 🚀 Quick Start

### Prerequisites

1. **Terraform** (v1.5+): [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
2. **Cloud CLI Tools** (for your target clouds):
   - **Google Cloud SDK**: `gcloud auth login`
   - **AWS CLI**: `aws configure`
3. **Python Dependencies**: `pip install -r requirements.txt`
4. **Anthropic API Key**: Set in `.env` file

### Basic Multi-Cloud Deployment

```bash
# Deploy to GCP (default)
python terraform_prototype.py examples/example-spec.md

# Deploy to AWS
python terraform_prototype.py examples/example-spec.md --provider aws

# Deploy to both GCP and AWS
python terraform_prototype.py examples/example-spec.md --provider both
# OR
python terraform_prototype.py examples/example-spec.md --provider gcp,aws
```

### Advanced Options

```bash
# Plan only (don't deploy)
python terraform_prototype.py spec.md --terraform-plan-only --provider aws

# Use custom Terraform workspace
python terraform_prototype.py spec.md --terraform-workspace production

# Use custom variables file
python terraform_prototype.py spec.md --terraform-var-file custom.tfvars

# Destroy existing deployment
python terraform_prototype.py spec.md --terraform-destroy --output-dir ./generated/previous-deployment
```

## 🏗️ Architecture Overview

### Generated Files Structure

```
generated/20240824_143022_my-service_gcp-aws/
├── 📱 Application Files:
│   ├── package.json         # Node.js dependencies
│   ├── index.js            # Express.js application
│   └── Dockerfile          # Multi-stage container build
├── 🏗️ Terraform Configuration:
│   ├── main.tf             # Root module configuration
│   ├── variables.tf        # Input variables with validation
│   ├── outputs.tf          # Service URLs and resource info
│   ├── terraform-gcp.tfvars # GCP-specific variables
│   └── terraform-aws.tfvars # AWS-specific variables
└── 📚 Documentation:
    └── README-DEPLOYMENT.md # Deployment instructions
```

### Infrastructure Components

#### Google Cloud Platform
- **Cloud Run**: Serverless container platform
- **Artifact Registry**: Container image storage
- **Cloud Build**: CI/CD integration (optional)
- **IAM**: Service accounts and permissions
- **Cloud Monitoring**: Observability and alerting

#### Amazon Web Services
- **ECS Fargate**: Serverless container platform
- **Application Load Balancer**: HTTP traffic distribution
- **ECR**: Container image storage
- **VPC**: Network isolation and security
- **CloudWatch**: Logs and monitoring

## 📋 Provider Comparison

| Feature | GCP (Cloud Run) | AWS (ECS Fargate) |
|---------|-----------------|-------------------|
| **Scaling** | 0-1000 instances | 1-10 tasks (configurable) |
| **Cold Start** | ~100ms | ~1-2s |
| **Pricing** | Pay-per-request | Pay-per-task-hour |
| **SSL/TLS** | Automatic | Via ALB |
| **Custom Domains** | Built-in | Route53 + Certificate Manager |
| **Monitoring** | Cloud Monitoring | CloudWatch |

## 🔧 Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Required
ANTHROPIC_API_KEY=your_claude_api_key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id  # For GCP deployments

# Optional Terraform Configuration
TF_VAR_environment=dev
TF_VAR_enable_monitoring=true

# AWS Configuration (if deploying to AWS)
AWS_DEFAULT_REGION=us-west-2
```

### Provider-Specific Variables

#### GCP Variables (`terraform-gcp.tfvars`)
```hcl
# Google Cloud Platform Configuration
project_id = "your-gcp-project-id"
region = "us-central1"
service_name = "my-microservice"

# Container Configuration
container_image = "gcr.io/your-project/my-service:latest"
container_port = 8080

# Scaling
min_instances = "0"
max_instances = "10"
container_concurrency = 80

# Resources
cpu_limit = "1000m"
memory_limit = "512Mi"

# Security
allow_unauthenticated = true
```

#### AWS Variables (`terraform-aws.tfvars`)
```hcl
# Amazon Web Services Configuration
aws_region = "us-west-2"
service_name = "my-microservice"

# Container Configuration
container_image = "123456789.dkr.ecr.us-west-2.amazonaws.com/my-service:latest"
container_port = 8080

# ECS Configuration
cpu_units = 512
memory_units = 1024
desired_count = 1

# Auto Scaling
min_capacity = 1
max_capacity = 10
target_cpu_utilization = 70

# Networking
create_vpc = true
vpc_cidr = "10.0.0.0/16"
```

## 🔄 State Management

### Local State (Default)
```bash
# Uses local terraform.tfstate file
python terraform_prototype.py spec.md --provider gcp
```

### Remote State (Recommended for Production)

#### GCS Backend (GCP)
```bash
# Automatically configured for GCP deployments
export TF_BACKEND_BUCKET="your-project-terraform-state"
python terraform_prototype.py spec.md --provider gcp
```

#### S3 Backend (AWS)
```bash
# Automatically configured for AWS deployments
export TF_BACKEND_BUCKET="your-account-terraform-state"
export TF_BACKEND_DYNAMODB_TABLE="terraform-state-lock"
python terraform_prototype.py spec.md --provider aws
```

### State Migration
```bash
# The system will automatically recommend and help set up remote state
# when deploying to cloud providers
```

## 🎯 Deployment Workflows

### Development Workflow
1. **Generate and Plan**:
   ```bash
   python terraform_prototype.py spec.md --terraform-plan-only
   ```

2. **Review Plan**: Check the generated Terraform plan in output directory

3. **Deploy**:
   ```bash
   cd generated/your-service-timestamp/
   terraform apply
   ```

### Production Workflow
1. **Use Workspaces**:
   ```bash
   python terraform_prototype.py spec.md --terraform-workspace production
   ```

2. **Remote State**: Automatically configured based on target cloud

3. **CI/CD Integration**: Use generated Terraform configs in your CI/CD pipeline

### Multi-Cloud Workflow
1. **Deploy to Both Clouds**:
   ```bash
   python terraform_prototype.py spec.md --provider both
   ```

2. **Different Configurations**: Use separate `.tfvars` files for each cloud

3. **Load Balancing**: Configure global load balancing between clouds (manual setup)

## 🔍 Monitoring and Observability

### GCP Monitoring
- **Cloud Monitoring**: Automatic metrics collection
- **Cloud Logging**: Structured application logs
- **Uptime Checks**: Health monitoring
- **Error Reporting**: Automatic error tracking

### AWS Monitoring
- **CloudWatch Metrics**: CPU, memory, request metrics
- **CloudWatch Logs**: Application and container logs
- **Application Load Balancer**: Health checks and metrics
- **Container Insights**: Enhanced container monitoring

### Multi-Cloud Monitoring
For multi-cloud deployments, consider:
- **DataDog**: Unified monitoring across clouds
- **New Relic**: Application performance monitoring
- **Prometheus + Grafana**: Open-source monitoring stack

## 🛠️ Troubleshooting

### Common Issues

#### Authentication Issues
```bash
# GCP: Check authentication
gcloud auth list
gcloud config list

# AWS: Check authentication
aws sts get-caller-identity
aws configure list
```

#### Terraform Issues
```bash
# Validate configuration
terraform validate

# Check state
terraform show

# Refresh state
terraform refresh

# Force unlock (if stuck)
terraform force-unlock LOCK_ID
```

#### Container Build Issues
```bash
# Check Docker
docker --version
docker ps

# Test local build
cd generated/your-service/
docker build -t test-image .
docker run -p 8080:8080 test-image
```

### Provider-Specific Issues

#### GCP Issues
- **Cloud Run API not enabled**: `gcloud services enable run.googleapis.com`
- **Insufficient permissions**: Add Cloud Run Admin and Service Account User roles
- **Artifact Registry not enabled**: `gcloud services enable artifactregistry.googleapis.com`

#### AWS Issues
- **ECS service failed**: Check VPC and security group configuration
- **Task definition invalid**: Verify CPU/memory combinations are valid
- **Load balancer unhealthy**: Check health check path and container port

### Getting Help

1. **Check logs**: All deployment logs are saved in the output directory
2. **Enable debug mode**: Use `--debug` flag for detailed output
3. **Review Terraform plan**: Use `--terraform-plan-only` to see what will be created
4. **Manual deployment**: Generated files can be deployed manually with `terraform apply`

## 🔧 Advanced Configuration

### Custom Terraform Modules
You can modify the generated Terraform configurations or use your own modules:

1. Edit files in `generated/your-service/`
2. Add custom modules in `modules/` directory
3. Update `main.tf` to reference your modules

### Environment-Specific Deployments
```bash
# Development
python terraform_prototype.py spec.md --terraform-workspace dev

# Staging
python terraform_prototype.py spec.md --terraform-workspace staging

# Production
python terraform_prototype.py spec.md --terraform-workspace production
```

### Custom Variables
Create custom `.tfvars` files for your specific needs:
```bash
python terraform_prototype.py spec.md --terraform-var-file custom.tfvars
```

## 🚀 Migration from Legacy

### From Legacy CloudRun to Terraform
1. **Generate with Terraform**: Re-run with new prototype
2. **Import existing resources** (optional):
   ```bash
   terraform import google_cloud_run_service.service your-service-name
   ```
3. **Apply configuration**: Terraform will manage the existing service

### Backwards Compatibility
Legacy deployment is still available:
```bash
python prototype.py spec.md  # Original prototype
python terraform_prototype.py spec.md --legacy  # Legacy mode in new prototype
```

## 📚 Examples

### Simple API Service
```bash
python terraform_prototype.py examples/user-api-nodejs.spec.md --provider gcp
```

### Multi-Cloud Deployment
```bash
python terraform_prototype.py examples/data-processor-python.spec.md --provider both
```

### Production Deployment
```bash
python terraform_prototype.py examples/auth-service-go.spec.md \
  --provider aws \
  --terraform-workspace production \
  --terraform-var-file production.tfvars
```

---

## 💡 Tips and Best Practices

1. **Start Small**: Begin with single-cloud deployments before going multi-cloud
2. **Use Workspaces**: Separate environments with Terraform workspaces
3. **Version Control**: Commit generated Terraform files for reproducibility
4. **Remote State**: Use cloud storage for state in production
5. **Monitor Costs**: Both clouds charge differently - monitor your usage
6. **Security**: Review generated IAM policies before production use
7. **Testing**: Use `--terraform-plan-only` to preview changes

Happy multi-cloud deploying! 🎉