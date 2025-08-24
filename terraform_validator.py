"""
Terraform Configuration Validator and Auto-Fixer
Validates generated Terraform files and automatically fixes issues
"""

import os
import re
import shutil
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging

from spec_parser import ServiceSpec


class TerraformValidator:
    """Validates and auto-fixes Terraform configurations"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('terraform_validator')
    
    def validate_and_fix(self, generated_files: Dict[str, str], spec: ServiceSpec, 
                        providers: List[str], output_dir: str, max_retries: int = 3) -> Tuple[bool, Dict[str, str]]:
        """
        Validate generated files and automatically fix issues
        Returns: (success, fixed_files)
        """
        
        validation_results = self.validate_terraform_files(generated_files, providers)
        
        if validation_results['valid']:
            # Copy Terraform modules to output directory
            self._copy_terraform_modules(output_dir, providers)
            self.logger.info("✅ All Terraform files validated successfully")
            return True, generated_files
        
        self.logger.warning(f"⚠️ Validation issues found: {len(validation_results['issues'])}")
        for issue in validation_results['issues']:
            self.logger.warning(f"   • {issue}")
        
        # Attempt to auto-fix issues
        fixed_files = generated_files.copy()
        
        for attempt in range(max_retries):
            self.logger.info(f"🔧 Auto-fix attempt {attempt + 1}/{max_retries}")
            
            # Generate missing files
            missing_files = self._generate_missing_files(
                fixed_files, validation_results['missing_files'], spec, providers
            )
            fixed_files.update(missing_files)
            
            # Fix content issues
            fixed_files = self._fix_content_issues(
                fixed_files, validation_results['content_issues'], spec, providers
            )
            
            # Re-validate
            validation_results = self.validate_terraform_files(fixed_files, providers)
            
            if validation_results['valid']:
                # Copy Terraform modules to output directory  
                self._copy_terraform_modules(output_dir, providers)
                self.logger.info(f"✅ Auto-fix successful after {attempt + 1} attempts")
                return True, fixed_files
        
        self.logger.error(f"❌ Auto-fix failed after {max_retries} attempts")
        return False, fixed_files
    
    def validate_terraform_files(self, files: Dict[str, str], providers: List[str]) -> Dict:
        """Validate Terraform files structure and content"""
        
        required_files = ['main.tf', 'variables.tf', 'outputs.tf']
        missing_files = []
        content_issues = []
        
        # Check required files exist
        for file in required_files:
            if file not in files:
                missing_files.append(file)
        
        # Validate file contents
        if 'main.tf' in files:
            main_tf_issues = self._validate_main_tf(files['main.tf'], providers)
            content_issues.extend(main_tf_issues)
        
        if 'variables.tf' in files:
            variables_tf_issues = self._validate_variables_tf(files['variables.tf'], providers)
            content_issues.extend(variables_tf_issues)
        
        if 'outputs.tf' in files:
            outputs_tf_issues = self._validate_outputs_tf(files['outputs.tf'], providers)
            content_issues.extend(outputs_tf_issues)
        
        # Check provider-specific tfvars files
        for provider in providers:
            tfvars_file = f'terraform-{provider}.tfvars'
            if tfvars_file not in files:
                missing_files.append(tfvars_file)
        
        # Check application files exist
        dockerfile_exists = 'Dockerfile' in files
        
        # Check for runtime-specific files
        nodejs_files = any(f in files for f in ['package.json', 'index.js'])
        python_files = any(f in files for f in ['requirements.txt', 'main.py'])
        go_files = any(f in files for f in ['go.mod', 'main.go'])
        
        if not dockerfile_exists:
            missing_files.append('Dockerfile')
        
        if not (nodejs_files or python_files or go_files):
            content_issues.append("No runtime-specific application files found")
        
        is_valid = len(missing_files) == 0 and len(content_issues) == 0
        
        return {
            'valid': is_valid,
            'missing_files': missing_files,
            'content_issues': content_issues,
            'issues': missing_files + content_issues
        }
    
    def _validate_main_tf(self, content: str, providers: List[str]) -> List[str]:
        """Validate main.tf content"""
        issues = []
        
        # Check for terraform block
        if 'terraform {' not in content:
            issues.append("main.tf: Missing terraform configuration block")
        
        # Check for required providers
        if 'gcp' in providers and 'hashicorp/google' not in content:
            issues.append("main.tf: Missing Google Cloud provider configuration")
        
        if 'aws' in providers and 'hashicorp/aws' not in content:
            issues.append("main.tf: Missing AWS provider configuration")
        
        # Check for module blocks
        if 'gcp' in providers and 'module' not in content:
            issues.append("main.tf: Missing module blocks for GCP resources")
        
        if 'aws' in providers and 'module' not in content:
            issues.append("main.tf: Missing module blocks for AWS resources")
        
        return issues
    
    def _validate_variables_tf(self, content: str, providers: List[str]) -> List[str]:
        """Validate variables.tf content"""
        issues = []
        
        required_vars = ['service_name']
        
        if 'gcp' in providers:
            required_vars.extend(['project_id', 'region'])
        
        if 'aws' in providers:
            required_vars.extend(['aws_region'])
        
        for var in required_vars:
            if f'variable "{var}"' not in content:
                issues.append(f"variables.tf: Missing required variable '{var}'")
        
        return issues
    
    def _validate_outputs_tf(self, content: str, providers: List[str]) -> List[str]:
        """Validate outputs.tf content"""
        issues = []
        
        if 'output' not in content:
            issues.append("outputs.tf: No output definitions found")
        
        if 'service_url' not in content:
            issues.append("outputs.tf: Missing service_url output")
        
        return issues
    
    def _generate_missing_files(self, existing_files: Dict[str, str], missing_files: List[str], 
                               spec: ServiceSpec, providers: List[str]) -> Dict[str, str]:
        """Generate missing Terraform files"""
        
        generated_files = {}
        
        if 'main.tf' in missing_files:
            generated_files['main.tf'] = self._generate_main_tf(spec, providers)
        
        if 'variables.tf' in missing_files:
            generated_files['variables.tf'] = self._generate_variables_tf(spec, providers)
        
        if 'outputs.tf' in missing_files:
            generated_files['outputs.tf'] = self._generate_outputs_tf(spec, providers)
        
        # Generate missing tfvars files
        for provider in providers:
            tfvars_file = f'terraform-{provider}.tfvars'
            if tfvars_file in missing_files:
                # Import locally to avoid circular imports
                from terraform_code_generator import TerraformCodeGenerator
                generator = TerraformCodeGenerator()
                generated_files[tfvars_file] = generator._generate_provider_tfvars(spec, provider)
        
        # Generate missing application files
        if 'Dockerfile' in missing_files:
            generated_files['Dockerfile'] = self._generate_dockerfile(spec)
        
        # Generate runtime-specific files based on spec runtime
        runtime = (spec.runtime or 'Node.js').lower()
        if 'node' in runtime or 'javascript' in runtime:
            if 'package.json' not in existing_files and 'package.json' not in generated_files:
                generated_files['package.json'] = self._generate_package_json(spec)
            if 'index.js' not in existing_files and 'index.js' not in generated_files:
                generated_files['index.js'] = self._generate_nodejs_app(spec)
        elif 'python' in runtime:
            if 'requirements.txt' not in existing_files and 'requirements.txt' not in generated_files:
                generated_files['requirements.txt'] = self._generate_requirements_txt(spec)
            if 'main.py' not in existing_files and 'main.py' not in generated_files:
                generated_files['main.py'] = self._generate_python_app(spec)
        
        return generated_files
    
    def _generate_main_tf(self, spec: ServiceSpec, providers: List[str]) -> str:
        """Generate main.tf file"""
        
        service_name = (spec.name or 'cloud-microservice').lower().replace(' ', '-').replace('_', '-')
        
        content = '''# Generated Terraform Configuration for Multi-Cloud Deployment
terraform {
  required_version = ">= 1.5"
  
  required_providers {'''
        
        if 'gcp' in providers:
            content += '''
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }'''
        
        if 'aws' in providers:
            content += '''
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }'''
        
        content += '''
  }
}

# Local values for consistent naming
locals {
  service_name = var.service_name
  environment = var.environment
  
  common_tags = {
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "cloud-function-saas"
  }
}
'''
        
        if 'gcp' in providers:
            content += '''
# Google Cloud Provider Configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# GCP Serverless Module
module "gcp_serverless" {
  source = "./terraform/modules/gcp-serverless"
  
  project_id       = var.project_id
  region          = var.region
  service_name    = local.service_name
  container_image = var.container_image
  container_port  = var.container_port
  environment     = var.environment
  
  # Resource configuration
  cpu_limit    = var.cpu_limit
  memory_limit = var.memory_limit
  
  # Scaling configuration
  min_instances         = var.min_instances
  max_instances         = var.max_instances
  container_concurrency = var.container_concurrency
  
  # Security
  allow_unauthenticated = var.allow_unauthenticated
  
  # Environment variables
  environment_variables = var.environment_variables
  
  # Monitoring
  enable_monitoring   = var.enable_monitoring
  health_check_path  = var.health_check_path
}
'''
        
        if 'aws' in providers:
            content += '''
# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
}

# AWS Serverless Module
module "aws_serverless" {
  source = "./terraform/modules/aws-serverless"
  
  aws_region       = var.aws_region
  service_name     = local.service_name
  container_image  = var.container_image
  container_port   = var.container_port
  environment      = var.environment
  
  # ECS configuration
  cpu_units    = var.cpu_units
  memory_units = var.memory_units
  desired_count = var.desired_count
  
  # Auto scaling
  enable_autoscaling           = var.enable_autoscaling
  min_capacity                = var.min_capacity
  max_capacity                = var.max_capacity
  target_cpu_utilization      = var.target_cpu_utilization
  target_memory_utilization   = var.target_memory_utilization
  
  # Networking
  create_vpc          = var.create_vpc
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  
  # Environment variables
  environment_variables = var.environment_variables
  
  # Monitoring
  enable_monitoring = var.enable_monitoring
  health_check_path = var.health_check_path
}
'''
        
        return content
    
    def _generate_variables_tf(self, spec: ServiceSpec, providers: List[str]) -> str:
        """Generate variables.tf file"""
        
        content = '''# Terraform Variables for Multi-Cloud Deployment

variable "service_name" {
  description = "Name of the service"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.service_name))
    error_message = "Service name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "container_port" {
  description = "Port that the container listens on"
  type        = number
  default     = 8080
}

# Environment Variables
variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {
    NODE_ENV = "production"
    LOG_LEVEL = "info"
  }
}

# Health Check
variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/health"
}

# Monitoring
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}
'''
        
        if 'gcp' in providers:
            content += '''
# GCP Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

# GCP Resource Configuration
variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for the container"
  type        = string
  default     = "512Mi"
}

# GCP Scaling Configuration
variable "min_instances" {
  description = "Minimum number of instances"
  type        = string
  default     = "0"
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = string
  default     = "10"
}

variable "container_concurrency" {
  description = "Maximum number of concurrent requests per container"
  type        = number
  default     = 80
}

# GCP Security
variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}
'''
        
        if 'aws' in providers:
            content += '''
# AWS Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

# AWS ECS Configuration
variable "cpu_units" {
  description = "CPU units for the task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu_units)
    error_message = "CPU units must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory_units" {
  description = "Memory units for the task (MB)"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of running tasks"
  type        = number
  default     = 1
}

# AWS Auto Scaling
variable "enable_autoscaling" {
  description = "Enable auto scaling for the ECS service"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "target_memory_utilization" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

# AWS VPC Configuration
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = true
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}
'''
        
        return content
    
    def _generate_outputs_tf(self, spec: ServiceSpec, providers: List[str]) -> str:
        """Generate outputs.tf file"""
        
        content = '''# Terraform Outputs for Multi-Cloud Deployment

'''
        
        if 'gcp' in providers:
            content += '''# GCP Outputs
output "gcp_service_url" {
  description = "URL of the GCP Cloud Run service"
  value       = module.gcp_serverless.service_url
}

output "gcp_service_name" {
  description = "Name of the GCP Cloud Run service"
  value       = module.gcp_serverless.service_name
}

output "gcp_deployment_info" {
  description = "GCP deployment information"
  value       = module.gcp_serverless.deployment_info
}
'''
        
        if 'aws' in providers:
            content += '''# AWS Outputs
output "aws_service_url" {
  description = "URL of the AWS load balancer"
  value       = module.aws_serverless.service_url
}

output "aws_service_name" {
  description = "Name of the AWS ECS service"
  value       = module.aws_serverless.service_name
}

output "aws_deployment_info" {
  description = "AWS deployment information"
  value       = module.aws_serverless.deployment_info
}
'''
        
        # Add primary service URL output
        if len(providers) == 1:
            if 'gcp' in providers:
                content += '''
# Primary Service URL
output "service_url" {
  description = "Primary service URL"
  value       = module.gcp_serverless.service_url
}
'''
            elif 'aws' in providers:
                content += '''
# Primary Service URL
output "service_url" {
  description = "Primary service URL"
  value       = module.aws_serverless.service_url
}
'''
        else:
            # Multi-cloud deployment
            content += '''
# Multi-Cloud Service URLs
output "service_urls" {
  description = "All service URLs"
  value = {'''
            
            if 'gcp' in providers:
                content += '''
    gcp = module.gcp_serverless.service_url'''
            
            if 'aws' in providers:
                content += '''
    aws = module.aws_serverless.service_url'''
            
            content += '''
  }
}

# Primary Service URL (defaults to GCP if available)
output "service_url" {
  description = "Primary service URL"
  value       = ''' + ('module.gcp_serverless.service_url' if 'gcp' in providers else 'module.aws_serverless.service_url') + '''
}
'''
        
        content += '''
# Deployment Summary
output "deployment_summary" {
  description = "Complete deployment summary"
  value = {
    service_name = var.service_name
    environment  = var.environment
    providers    = [''' + ', '.join([f'"{p}"' for p in providers]) + ''']
    deployed_at  = timestamp()
  }
}
'''
        
        return content
    
    def _fix_content_issues(self, files: Dict[str, str], issues: List[str], 
                           spec: ServiceSpec, providers: List[str]) -> Dict[str, str]:
        """Fix content issues in existing files"""
        
        fixed_files = files.copy()
        
        # This is a simplified version - in practice, you might want more sophisticated fixes
        for issue in issues:
            if 'main.tf' in issue and 'main.tf' in fixed_files:
                # Regenerate main.tf if there are issues
                fixed_files['main.tf'] = self._generate_main_tf(spec, providers)
            
            elif 'variables.tf' in issue and 'variables.tf' in fixed_files:
                # Regenerate variables.tf if there are issues
                fixed_files['variables.tf'] = self._generate_variables_tf(spec, providers)
            
            elif 'outputs.tf' in issue and 'outputs.tf' in fixed_files:
                # Regenerate outputs.tf if there are issues
                fixed_files['outputs.tf'] = self._generate_outputs_tf(spec, providers)
        
        return fixed_files
    
    def _generate_dockerfile(self, spec: ServiceSpec) -> str:
        """Generate basic Dockerfile"""
        
        runtime = (spec.runtime or 'Node.js').lower()
        
        if 'node' in runtime or 'javascript' in runtime:
            return '''# Node.js Dockerfile for Cloud Run/Fargate
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["npm", "start"]
'''
        
        elif 'python' in runtime:
            return '''# Python Dockerfile for Cloud Run/Fargate
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "main.py"]
'''
        
        else:
            # Default Node.js
            return '''# Default Node.js Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1
CMD ["npm", "start"]
'''
    
    def _generate_package_json(self, spec: ServiceSpec) -> str:
        """Generate basic package.json for Node.js"""
        
        service_name = (spec.name or 'cloud-microservice').lower().replace(' ', '-')
        
        return f'''{{
  "name": "{service_name}",
  "version": "1.0.0",
  "description": "{spec.description or 'Generated microservice'}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "dependencies": {{
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "morgan": "^1.10.0"
  }},
  "engines": {{
    "node": ">=20.0.0"
  }},
  "keywords": [
    "microservice",
    "api",
    "cloud-function-saas"
  ],
  "author": "Cloud Function SaaS Generator",
  "license": "MIT"
}}
'''
    
    def _generate_nodejs_app(self, spec: ServiceSpec) -> str:
        """Generate basic Node.js Express application"""
        
        service_name = spec.name or 'Cloud Microservice'
        
        # Generate basic endpoints
        endpoints_code = ''
        if spec.endpoints:
            for endpoint in spec.endpoints:
                method = endpoint.get('method', 'GET').lower()
                path = endpoint.get('path', '/')
                description = endpoint.get('description', 'API endpoint')
                
                if path == '/health':
                    continue  # Health endpoint is handled separately
                
                if method == 'get':
                    endpoints_code += f'''
// {description}
app.get('{path}', (req, res) => {{
  res.json({{ 
    message: '{description}',
    path: '{path}',
    method: '{method.upper()}',
    timestamp: new Date().toISOString()
  }});
}});
'''
                elif method == 'post':
                    endpoints_code += f'''
// {description}  
app.post('{path}', (req, res) => {{
  res.json({{ 
    message: '{description}',
    data: req.body,
    path: '{path}',
    method: '{method.upper()}',
    timestamp: new Date().toISOString()
  }});
}});
'''
        
        return f'''const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();
const port = process.env.PORT || 8080;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {{
  res.json({{ 
    status: 'healthy',
    service: '{service_name}',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  }});
}});

// Root endpoint
app.get('/', (req, res) => {{
  res.json({{
    message: 'Welcome to {service_name}',
    description: '{spec.description or 'Generated microservice'}',
    health: '/health',
    timestamp: new Date().toISOString()
  }});
}});
{endpoints_code}
// Error handling middleware
app.use((err, req, res, next) => {{
  console.error(err.stack);
  res.status(500).json({{ 
    error: 'Something went wrong!',
    timestamp: new Date().toISOString()
  }});
}});

// 404 handler
app.use((req, res) => {{
  res.status(404).json({{ 
    error: 'Endpoint not found',
    path: req.path,
    timestamp: new Date().toISOString()
  }});
}});

// Start server
app.listen(port, '0.0.0.0', () => {{
  console.log(`{service_name} listening on port ${{port}}`);
  console.log(`Health check: http://localhost:${{port}}/health`);
}});

module.exports = app;
'''
    
    def _generate_requirements_txt(self, spec: ServiceSpec) -> str:
        """Generate basic requirements.txt for Python"""
        
        return '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
'''
    
    def _generate_python_app(self, spec: ServiceSpec) -> str:
        """Generate basic Python FastAPI application"""
        
        service_name = spec.name or 'Cloud Microservice'
        
        # Generate basic endpoints
        endpoints_code = ''
        if spec.endpoints:
            for endpoint in spec.endpoints:
                method = endpoint.get('method', 'GET').lower()
                path = endpoint.get('path', '/')
                description = endpoint.get('description', 'API endpoint')
                
                if path == '/health' or path == '/':
                    continue  # These are handled separately
                
                if method == 'get':
                    endpoints_code += f'''
@app.get("{path}")
async def {path.replace('/', '').replace('-', '_') or 'endpoint'}():
    """{description}"""
    return {{
        "message": "{description}",
        "path": "{path}",
        "method": "{method.upper()}",
        "timestamp": datetime.utcnow().isoformat()
    }}
'''
                elif method == 'post':
                    endpoints_code += f'''
@app.post("{path}")
async def {path.replace('/', '').replace('-', '_') or 'endpoint'}(data: dict):
    """{description}"""
    return {{
        "message": "{description}",
        "data": data,
        "path": "{path}",
        "method": "{method.upper()}",
        "timestamp": datetime.utcnow().isoformat()
    }}
'''
        
        return f'''import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="{service_name}",
    description="{spec.description or 'Generated microservice'}",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {{
        "message": "Welcome to {service_name}",
        "description": "{spec.description or 'Generated microservice'}",
        "health": "/health",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{
        "status": "healthy",
        "service": "{service_name}",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }}
{endpoints_code}
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
'''

    def _copy_terraform_modules(self, output_dir: str, providers: List[str]):
        """Copy required Terraform modules to output directory"""
        
        # Find the project root directory (where terraform/modules should be)
        current_dir = Path(__file__).parent
        terraform_modules_source = current_dir / "terraform" / "modules"
        
        if not terraform_modules_source.exists():
            self.logger.warning(f"Terraform modules not found at {terraform_modules_source}")
            return
        
        # Create terraform/modules directory in output
        terraform_modules_dest = Path(output_dir) / "terraform" / "modules"
        terraform_modules_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy required modules based on providers
        modules_to_copy = ['shared']  # Always copy shared module
        
        if 'gcp' in providers:
            modules_to_copy.append('gcp-serverless')
        
        if 'aws' in providers:
            modules_to_copy.append('aws-serverless')
        
        for module_name in modules_to_copy:
            source_module = terraform_modules_source / module_name
            dest_module = terraform_modules_dest / module_name
            
            if source_module.exists():
                try:
                    if dest_module.exists():
                        shutil.rmtree(dest_module)
                    shutil.copytree(source_module, dest_module)
                    self.logger.info(f"✅ Copied Terraform module: {module_name}")
                except Exception as e:
                    self.logger.error(f"Failed to copy module {module_name}: {e}")
            else:
                self.logger.warning(f"Module {module_name} not found at {source_module}")