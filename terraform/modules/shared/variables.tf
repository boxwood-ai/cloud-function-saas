# Shared Module Variables

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

variable "use_random_suffix" {
  description = "Add a random suffix to resource names for uniqueness"
  type        = bool
  default     = false
}

# Cloud Provider Flags
variable "enable_aws_resources" {
  description = "Enable AWS-specific shared resources"
  type        = bool
  default     = false
}

variable "enable_gcp_resources" {
  description = "Enable GCP-specific shared resources"
  type        = bool
  default     = false
}

variable "enable_azure_resources" {
  description = "Enable Azure-specific shared resources"
  type        = bool
  default     = false
}

# Secrets Management
variable "create_shared_secrets" {
  description = "Create shared secrets in cloud secret managers"
  type        = bool
  default     = true
}

variable "shared_configuration" {
  description = "Shared configuration values to store in secrets"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# DNS and Domain Management
variable "custom_domain" {
  description = "Custom domain name for the service"
  type        = string
  default     = ""
}

variable "create_dns_zone" {
  description = "Create DNS zones for custom domain"
  type        = bool
  default     = true
}

# SSL/TLS Configuration
variable "create_ssl_certificate" {
  description = "Create SSL certificates for custom domain"
  type        = bool
  default     = true
}

variable "certificate_validation_method" {
  description = "Certificate validation method (DNS or EMAIL)"
  type        = string
  default     = "DNS"
  validation {
    condition     = contains(["DNS", "EMAIL"], var.certificate_validation_method)
    error_message = "Certificate validation method must be DNS or EMAIL."
  }
}

# Monitoring Configuration
variable "enable_datadog_monitoring" {
  description = "Enable DataDog monitoring integration"
  type        = bool
  default     = false
}

variable "enable_newrelic_monitoring" {
  description = "Enable New Relic monitoring integration"
  type        = bool
  default     = false
}

variable "monitoring_endpoints" {
  description = "List of monitoring endpoints to configure"
  type = list(object({
    name = string
    url  = string
    type = string
  }))
  default = []
}

# Alerting Configuration
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "alert_slack_webhook" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_pagerduty" {
  description = "Enable PagerDuty integration for alerts"
  type        = bool
  default     = false
}

variable "pagerduty_service_key" {
  description = "PagerDuty service key for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

# Cross-Cloud Networking
variable "enable_cross_cloud_networking" {
  description = "Enable cross-cloud networking setup"
  type        = bool
  default     = false
}

variable "aws_vpc_cidr" {
  description = "CIDR block for AWS VPC (if cross-cloud networking enabled)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "gcp_vpc_cidr" {
  description = "CIDR block for GCP VPC (if cross-cloud networking enabled)"
  type        = string
  default     = "10.1.0.0/16"
}

# Backup and Disaster Recovery
variable "enable_backup" {
  description = "Enable backup configuration"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Cost Management
variable "enable_cost_alerts" {
  description = "Enable cost monitoring and alerts"
  type        = bool
  default     = false
}

variable "monthly_cost_budget" {
  description = "Monthly cost budget threshold for alerts (USD)"
  type        = number
  default     = 100
}

# Compliance and Security
variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring (GDPR, SOC2, etc.)"
  type        = bool
  default     = false
}

variable "compliance_standards" {
  description = "List of compliance standards to monitor"
  type        = list(string)
  default     = []
}

variable "enable_security_scanning" {
  description = "Enable security scanning and vulnerability assessment"
  type        = bool
  default     = true
}

# Tagging Strategy
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}