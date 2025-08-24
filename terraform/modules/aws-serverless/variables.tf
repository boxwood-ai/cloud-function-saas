# AWS ECS Fargate Module Variables

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "service_name" {
  description = "Name of the ECS service"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9-]+$", var.service_name))
    error_message = "Service name must contain only alphanumeric characters and hyphens."
  }
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

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# VPC Configuration
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "VPC ID to use (if not creating new VPC)"
  type        = string
  default     = ""
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

variable "subnet_ids" {
  description = "Subnet IDs to use (if not creating new VPC)"
  type        = list(string)
  default     = []
}

# ECS Configuration
variable "create_ecs_cluster" {
  description = "Whether to create a new ECS cluster"
  type        = bool
  default     = true
}

variable "ecs_cluster_name" {
  description = "ECS cluster name to use (if not creating new cluster)"
  type        = string
  default     = ""
}

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

# Auto Scaling
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

# Environment Variables
variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

# Health Check
variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/"
}

# Logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# ECR Configuration
variable "create_ecr_repository" {
  description = "Whether to create an ECR repository"
  type        = bool
  default     = true
}

# Monitoring
variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring and alerting"
  type        = bool
  default     = true
}

# Security
variable "certificate_arn" {
  description = "SSL certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}

variable "custom_domain" {
  description = "Custom domain name for the service (optional)"
  type        = string
  default     = ""
}