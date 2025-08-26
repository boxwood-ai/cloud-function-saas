"""
Terraform-powered code generation components for the Cloud Function Generator
Extends the existing CodeGenerator to produce Terraform configurations
"""

import os
import re
import json
from typing import Dict, Optional, List
import anthropic

from spec_parser import ServiceSpec
from code_generator import CodeGenerator


class TerraformCodeGenerator(CodeGenerator):
    """Generate Cloud Run function code AND Terraform configuration using Claude"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, debug: bool = False):
        super().__init__(api_key, model, debug)
        self.terraform_template_dir = "terraform/modules"
    
    def generate_multi_cloud_deployment(self, spec: ServiceSpec, providers: List[str] = None) -> Dict[str, str]:
        """Generate complete multi-cloud deployment with Terraform configuration"""
        
        providers = providers or ['gcp']  # Default to GCP if no providers specified
        
        if self.debug:
            print(f"🔍 Debug - Generating for providers: {providers}")
        
        # Create the enhanced prompt for Terraform + application code generation
        prompt = self._build_terraform_prompt(spec, providers)
        
        if self.debug:
            print(f"🔍 Debug - Using model: {self.model}")
            print(f"🔍 Debug - Terraform prompt length: {len(prompt)} characters")
            print(f"🔍 Debug - Prompt preview: {prompt[:300]}...")
        
        try:
            if self.debug:
                print("🔍 Debug - Sending Terraform request to Claude...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert DevOps engineer specializing in Terraform, Docker, and multi-cloud deployments. Generate complete, production-ready application code AND Terraform configurations for multi-cloud serverless deployments.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if self.debug:
                print(f"🔍 Debug - Terraform response received, length: {len(response.content[0].text)} characters")
            
            generated_content = response.content[0].text
            files = self._parse_terraform_generated_files(generated_content)
            
            # Add provider-specific Terraform variable files
            for provider in providers:
                if provider not in files.get('terraform.tfvars', ''):
                    tfvars_content = self._generate_provider_tfvars(spec, provider)
                    files[f'terraform-{provider}.tfvars'] = tfvars_content
            
            if self.debug:
                print(f"🔍 Debug - Generated {len(files)} total files: {list(files.keys())}")
            
            return files
            
        except Exception as e:
            if self.debug:
                print(f"🔍 Debug - Error in Terraform generation: {e}")
            raise Exception(f"Failed to generate Terraform configuration: {e}")
    
    def _build_terraform_prompt(self, spec: ServiceSpec, providers: List[str]) -> str:
        """Build enhanced prompt for Terraform + application code generation"""
        
        # Determine container runtime based on spec
        runtime_info = self._get_runtime_info(spec.runtime)
        
        # Build provider-specific requirements
        provider_configs = []
        for provider in providers:
            if provider == 'gcp':
                provider_configs.append("""
                - Google Cloud Run service with auto-scaling
                - Container registry using Artifact Registry
                - IAM service accounts with least privilege
                - Cloud Run IAM policies for public access (if specified)
                - Monitoring and logging integration
                """)
            elif provider == 'aws':
                provider_configs.append("""
                - AWS ECS Fargate service with auto-scaling
                - Application Load Balancer for HTTP traffic
                - ECR repository for container images
                - CloudWatch logs and monitoring
                - VPC and security groups configuration
                """)
        
        prompt = f"""
Generate a complete multi-cloud serverless deployment for the following service specification:

**Service Details:**
- Name: {spec.name or 'cloud-microservice'}
- Description: {spec.description or 'Generated microservice'}
- Runtime: {spec.runtime or 'Node.js 20'}

**API Endpoints:**
{self._format_endpoints_for_terraform_prompt(spec.endpoints)}

**Data Models:**
{self._format_models_for_terraform_prompt(spec.models)}

**Target Cloud Providers:** {', '.join(providers)}

**REQUIRED OUTPUTS:**

1. **Application Files** ({runtime_info['language']} application):
   - package.json (with proper dependencies and scripts)
   - index.js (Express.js server with all endpoints implemented)
   - Dockerfile (optimized for Cloud Run/Fargate with proper port exposure)

2. **Terraform Configuration Files:**
   - main.tf (root module that calls provider-specific modules)
   - variables.tf (all input variables with descriptions and validation)
   - outputs.tf (service URLs, names, and deployment info)
   - terraform.tfvars.example (example values for all variables)

3. **Provider-Specific Configuration:**
   For each provider, generate provider-specific resource configuration using the modules:
{chr(10).join(provider_configs)}

**Terraform Requirements:**
- Use the pre-built modules located at: terraform/modules/gcp-serverless and terraform/modules/aws-serverless
- Configure proper provider authentication (ADC for GCP, AWS CLI for AWS)
- Set up container image building and pushing to respective registries
- Configure auto-scaling, health checks, and monitoring
- Output service URLs and important resource identifiers
- Include proper variable validation and descriptions
- Support for environment-specific deployment (dev/staging/prod)

**Application Requirements:**
- Implement all {len(spec.endpoints)} API endpoints defined in the spec
- Include proper error handling and logging
- Add health check endpoint at /health
- Use environment variables for configuration
- Include input validation and sanitization
- Follow REST API best practices
- Container should listen on PORT environment variable (default 8080)

**Security Requirements:**
- Use least-privilege IAM roles
- Implement proper CORS configuration
- Sanitize all inputs
- Use HTTPS/TLS for all communications
- Store sensitive configuration in cloud secret managers

**CRITICAL: You MUST generate ALL required files in the exact format specified below.**

**Format your response as:**
```
FILE: filename.ext
content of the file
```

**REQUIRED FILES (you must generate ALL of these):**

1. **APPLICATION FILES** (choose based on runtime):
   - FILE: package.json (for Node.js)
   - FILE: index.js (for Node.js) 
   - FILE: requirements.txt (for Python)
   - FILE: main.py (for Python)
   - FILE: Dockerfile

2. **TERRAFORM CONFIGURATION FILES** (ALL required):
   - FILE: main.tf
   - FILE: variables.tf  
   - FILE: outputs.tf

3. **TERRAFORM VARIABLES FILES** (for each provider):
   - FILE: terraform-gcp.tfvars (if deploying to GCP)
   - FILE: terraform-aws.tfvars (if deploying to AWS)

**VALIDATION CHECKLIST - Ensure every response includes:**
✅ Application code files (package.json/requirements.txt + main code file + Dockerfile)  
✅ main.tf (with terraform block, providers, and modules)
✅ variables.tf (with all required variables for chosen providers)
✅ outputs.tf (with service_url and deployment info outputs)
✅ Provider-specific .tfvars files

**If you don't generate ALL required files, the deployment will fail!**

For Terraform files, make sure to:
1. Reference the correct module paths (terraform/modules/gcp-serverless, terraform/modules/aws-serverless)
2. Pass all required variables to modules
3. Configure proper provider blocks
4. Include data sources for dynamic values (project IDs, regions, etc.)
5. Set up proper state management (local state for now)

Generate complete, production-ready files that can be immediately deployed.
"""
        
        return prompt
    
    def _format_endpoints_for_terraform_prompt(self, endpoints) -> str:
        """Format endpoints for the Terraform prompt"""
        if not endpoints:
            return "- GET / (health check endpoint)\n"
        
        formatted = []
        for endpoint in endpoints:
            method = endpoint.get('method', 'GET').upper()
            path = endpoint.get('path', '/')
            description = endpoint.get('description', 'API endpoint')
            formatted.append(f"- {method} {path}: {description}")
        
        return '\n'.join(formatted) if formatted else "- GET / (health check endpoint)\n"
    
    def _format_models_for_terraform_prompt(self, models) -> str:
        """Format models for the Terraform prompt"""
        if not models:
            return "No specific data models defined.\n"
        
        formatted = []
        for model_name, fields in models.items():
            formatted.append(f"- {model_name}:")
            if isinstance(fields, list):
                for field in fields:
                    formatted.append(f"  - {field}")
            elif isinstance(fields, dict):
                for field_name, field_type in fields.items():
                    formatted.append(f"  - {field_name}: {field_type}")
        
        return '\n'.join(formatted) if formatted else "No specific data models defined.\n"
    
    def _get_runtime_info(self, runtime: str) -> dict:
        """Get runtime-specific information"""
        runtime_lower = (runtime or '').lower()
        
        if 'node' in runtime_lower or 'javascript' in runtime_lower:
            return {
                'language': 'Node.js',
                'package_manager': 'npm',
                'main_file': 'index.js',
                'package_file': 'package.json'
            }
        elif 'python' in runtime_lower:
            return {
                'language': 'Python',
                'package_manager': 'pip',
                'main_file': 'main.py',
                'package_file': 'requirements.txt'
            }
        elif 'go' in runtime_lower:
            return {
                'language': 'Go',
                'package_manager': 'go mod',
                'main_file': 'main.go',
                'package_file': 'go.mod'
            }
        else:
            # Default to Node.js
            return {
                'language': 'Node.js',
                'package_manager': 'npm',
                'main_file': 'index.js',
                'package_file': 'package.json'
            }
    
    def _parse_terraform_generated_files(self, generated_content: str) -> Dict[str, str]:
        """Parse generated content that includes both application and Terraform files"""
        files = {}
        
        # Look for file blocks in the format: FILE: filename.ext
        file_pattern = r'(?:FILE|```FILE):\s*([^\n]+)\n(.*?)(?=(?:FILE:|```FILE:|$))'
        matches = re.finditer(file_pattern, generated_content, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            filename = match.group(1).strip()
            content = match.group(2).strip()
            
            # Clean up content - remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            files[filename] = content
        
        # If no FILE: blocks found, try to parse using the old method
        if not files:
            files = self._parse_generated_files(generated_content)
        
        # Ensure we have essential files
        if 'main.tf' not in files and 'terraform' in generated_content.lower():
            # Try to extract Terraform configuration from generic content
            self._extract_terraform_from_content(generated_content, files)
        
        return files
    
    def _extract_terraform_from_content(self, content: str, files: Dict[str, str]):
        """Extract Terraform configuration from unstructured content"""
        # This is a fallback method to extract Terraform blocks
        # Look for terraform blocks and try to separate them into files
        
        # Extract main.tf content
        main_tf_pattern = r'(?:```(?:terraform|hcl)?[\s\n])?((?:terraform\s*\{|resource\s+|data\s+|module\s+).*?)(?=```|$)'
        main_tf_match = re.search(main_tf_pattern, content, re.DOTALL)
        if main_tf_match and 'main.tf' not in files:
            files['main.tf'] = main_tf_match.group(1).strip()
        
        # Extract variables.tf content
        variables_pattern = r'(?:```(?:terraform|hcl)?[\s\n])?((?:variable\s+).*?)(?=```|$)'
        variables_match = re.search(variables_pattern, content, re.DOTALL)
        if variables_match and 'variables.tf' not in files:
            files['variables.tf'] = variables_match.group(1).strip()
        
        # Extract outputs.tf content
        outputs_pattern = r'(?:```(?:terraform|hcl)?[\s\n])?((?:output\s+).*?)(?=```|$)'
        outputs_match = re.search(outputs_pattern, content, re.DOTALL)
        if outputs_match and 'outputs.tf' not in files:
            files['outputs.tf'] = outputs_match.group(1).strip()
    
    def _generate_provider_tfvars(self, spec: ServiceSpec, provider: str) -> str:
        """Generate provider-specific terraform.tfvars content"""
        
        service_name = (spec.name or 'cloud-microservice').lower().replace(' ', '-').replace('_', '-')
        
        # Get project ID from environment
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-gcp-project-id')
        region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        if provider == 'gcp':
            return f'''# Google Cloud Platform Configuration
project_id = "{project_id}"
region = "{region}"
service_name = "{service_name}"
environment = "dev"

# Container Configuration
container_image = "gcr.io/{project_id}/{service_name}:latest"
container_port = 8080

# Scaling Configuration
min_instances = "0"
max_instances = "10"
container_concurrency = 80

# Resource Limits
cpu_limit = "1000m"
memory_limit = "512Mi"
cpu_request = "100m"
memory_request = "128Mi"

# Security
allow_unauthenticated = true
service_account_email = ""

# Environment Variables
environment_variables = {{
  NODE_ENV = "production"
  LOG_LEVEL = "info"
}}

# Monitoring
enable_monitoring = true
health_check_path = "/health"
'''
        
        elif provider == 'aws':
            return f'''# Amazon Web Services Configuration
aws_region = "us-west-2"
service_name = "{service_name}"
environment = "dev"

# Container Configuration
container_image = "your-account-id.dkr.ecr.us-west-2.amazonaws.com/{service_name}:latest"
container_port = 8080

# ECS Configuration
cpu_units = 512
memory_units = 1024
desired_count = 1

# Auto Scaling
enable_autoscaling = true
min_capacity = 1
max_capacity = 10
target_cpu_utilization = 70
target_memory_utilization = 80

# VPC Configuration
create_vpc = true
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]

# Environment Variables
environment_variables = {{
  NODE_ENV = "production"
  LOG_LEVEL = "info"
}}

# Monitoring
enable_monitoring = true
health_check_path = "/health"
log_retention_days = 30
'''
        
        else:
            return f'''# Configuration for {provider}
service_name = "{service_name}"
environment = "dev"
'''
    
    def generate_deployment_readme(self, spec: ServiceSpec, providers: List[str]) -> str:
        """Generate README with deployment instructions"""
        
        service_name = spec.name or 'Cloud Microservice'
        providers_str = ', '.join(providers)
        
        return f'''# {service_name} - Multi-Cloud Deployment

This microservice has been generated with Terraform configuration for deployment to: **{providers_str}**

## Quick Start

### Prerequisites

1. **Terraform** (v1.5+): [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
2. **Cloud CLI Tools:**
   {'- **Google Cloud SDK**: `gcloud auth login` and `gcloud config set project YOUR_PROJECT_ID`' if 'gcp' in providers else ''}
   {'- **AWS CLI**: `aws configure` with your credentials' if 'aws' in providers else ''}
3. **Docker** (for local building): [Install Docker](https://docs.docker.com/get-docker/)

### Deployment Steps

1. **Configure Variables:**
   ```bash
   # Copy and edit the appropriate variables file
   {'cp terraform-gcp.tfvars terraform.tfvars  # For GCP deployment' if 'gcp' in providers else ''}
   {'cp terraform-aws.tfvars terraform.tfvars  # For AWS deployment' if 'aws' in providers else ''}
   
   # Edit terraform.tfvars with your specific values
   nano terraform.tfvars
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Plan Deployment:**
   ```bash
   terraform plan
   ```

4. **Deploy:**
   ```bash
   terraform apply
   ```

5. **Get Service URL:**
   ```bash
   terraform output service_url
   ```

## API Endpoints

{self._format_api_endpoints_for_readme(spec.endpoints)}

## Environment Variables

The following environment variables can be configured:

- `NODE_ENV`: Runtime environment (default: production)
- `LOG_LEVEL`: Logging level (default: info)
- `PORT`: Container port (default: 8080)

## Monitoring

{'- **GCP**: Cloud Monitoring and Cloud Logging' if 'gcp' in providers else ''}
{'- **AWS**: CloudWatch Logs and Metrics' if 'aws' in providers else ''}

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Troubleshooting

1. **Authentication Issues:**
   {'- Ensure `gcloud auth list` shows your authenticated account' if 'gcp' in providers else ''}
   {'- Ensure `aws sts get-caller-identity` returns your account info' if 'aws' in providers else ''}

2. **Permission Issues:**
   - Verify your account has necessary IAM permissions for the target cloud platform

3. **Container Build Issues:**
   - Check that Docker is running and accessible
   - Verify container registry permissions

## Architecture

This deployment uses:
{'- **GCP**: Cloud Run (serverless containers) with Artifact Registry' if 'gcp' in providers else ''}
{'- **AWS**: ECS Fargate (serverless containers) with ECR and Application Load Balancer' if 'aws' in providers else ''}

All infrastructure is defined as code using Terraform modules for consistency and reusability.
'''
    
    def _format_api_endpoints_for_readme(self, endpoints) -> str:
        """Format endpoints for README documentation"""
        if not endpoints:
            return """
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check endpoint |
"""
        
        formatted = ["| Method | Path | Description |", "|--------|------|-------------|"]
        for endpoint in endpoints:
            method = endpoint.get('method', 'GET').upper()
            path = endpoint.get('path', '/')
            description = endpoint.get('description', 'API endpoint')
            formatted.append(f"| {method} | {path} | {description} |")
        
        # Always add health check endpoint
        formatted.append("| GET | /health | Health check endpoint |")
        
        return '\n'.join(formatted)