# GCP Cloud Run Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.service_name))
    error_message = "Service name must contain only lowercase letters, numbers, and hyphens."
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

# Resource Configuration
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

variable "cpu_request" {
  description = "CPU request for the container"
  type        = string
  default     = "100m"
}

variable "memory_request" {
  description = "Memory request for the container"
  type        = string
  default     = "128Mi"
}

# Scaling Configuration
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

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

# Environment Variables
variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

# Security and Access
variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}

variable "service_account_email" {
  description = "Service account email to use for the service (empty string to create new)"
  type        = string
  default     = ""
}

variable "invoker_members" {
  description = "List of members to grant Cloud Run Invoker role"
  type        = list(string)
  default     = []
}

# Health Check
variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/"
}

# Build Configuration
variable "create_artifact_registry" {
  description = "Whether to create an Artifact Registry repository"
  type        = bool
  default     = true
}

variable "enable_cloud_build" {
  description = "Whether to create Cloud Build trigger"
  type        = bool
  default     = false
}

variable "repo_name" {
  description = "Repository name for Cloud Build (if enabled)"
  type        = string
  default     = ""
}

# Monitoring
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "uptime_check_content" {
  description = "Content to check for in uptime monitoring"
  type        = string
  default     = "OK"
}

variable "error_rate_threshold" {
  description = "Error rate threshold for alerting"
  type        = number
  default     = 0.1
}

variable "notification_channels" {
  description = "List of notification channels for alerts"
  type        = list(string)
  default     = []
}

# Networking
variable "vpc_connector_name" {
  description = "VPC connector name for private network access"
  type        = string
  default     = ""
}

variable "vpc_egress" {
  description = "VPC egress setting (all-traffic, private-ranges-only)"
  type        = string
  default     = "all-traffic"
}