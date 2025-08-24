# Shared Terraform Module for Cross-Cloud Resources

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# Local values for consistent naming
locals {
  name_suffix = var.use_random_suffix ? "-${random_id.suffix.hex}" : ""
  full_name   = "${var.service_name}${local.name_suffix}"
  
  common_tags = {
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "cloud-function-saas"
    CreatedAt   = timestamp()
  }
}

# Data sources for AWS (if AWS provider is configured)
data "aws_caller_identity" "current" {
  count = var.enable_aws_resources ? 1 : 0
}

data "aws_region" "current" {
  count = var.enable_aws_resources ? 1 : 0
}

# Data sources for GCP (if GCP provider is configured)
data "google_client_config" "default" {
  count = var.enable_gcp_resources ? 1 : 0
}

data "google_project" "project" {
  count = var.enable_gcp_resources ? 1 : 0
}

# Cross-cloud monitoring and alerting configuration
# This would typically integrate with third-party services like:
# - DataDog
# - New Relic
# - Splunk
# - PagerDuty

# Example: DataDog monitoring (commented as it requires DataDog provider)
# resource "datadog_monitor" "service_health" {
#   count   = var.enable_datadog_monitoring ? 1 : 0
#   name    = "${local.full_name} Health Check"
#   type    = "service check"
#   message = "Service ${local.full_name} is down"
#   
#   query = "\"http.can_connect\".over(\"instance:${local.full_name}\").by(\"*\").last(2).count_by_status()"
#   
#   monitor_thresholds {
#     warning  = 1
#     critical = 1
#   }
#   
#   notify_no_data    = false
#   renotify_interval = 0
#   
#   notify_audit = false
#   timeout_h    = 60
#   include_tags = true
#   
#   tags = ["service:${var.service_name}", "environment:${var.environment}"]
# }

# Shared secrets management (example using AWS Secrets Manager)
resource "aws_secretsmanager_secret" "shared_config" {
  count       = var.enable_aws_resources && var.create_shared_secrets ? 1 : 0
  name        = "${local.full_name}-config"
  description = "Shared configuration for ${var.service_name}"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "shared_config" {
  count     = var.enable_aws_resources && var.create_shared_secrets ? 1 : 0
  secret_id = aws_secretsmanager_secret.shared_config[0].id
  secret_string = jsonencode({
    service_name = var.service_name
    environment  = var.environment
    created_at   = timestamp()
    config       = var.shared_configuration
  })
}

# Shared secrets management (example using GCP Secret Manager)
resource "google_secret_manager_secret" "shared_config" {
  count     = var.enable_gcp_resources && var.create_shared_secrets ? 1 : 0
  secret_id = "${local.full_name}-config"

  replication {
    automatic = true
  }

  labels = {
    service     = var.service_name
    environment = var.environment
    managed-by  = "cloud-function-saas"
  }
}

resource "google_secret_manager_secret_version" "shared_config" {
  count   = var.enable_gcp_resources && var.create_shared_secrets ? 1 : 0
  secret  = google_secret_manager_secret.shared_config[0].id
  secret_data = jsonencode({
    service_name = var.service_name
    environment  = var.environment
    created_at   = timestamp()
    config       = var.shared_configuration
  })
}

# DNS management (if custom domain is provided)
# This would typically use Route 53 for AWS or Cloud DNS for GCP
# For now, we'll create a simple DNS record structure

resource "aws_route53_zone" "main" {
  count = var.enable_aws_resources && var.custom_domain != "" ? 1 : 0
  name  = var.custom_domain

  tags = local.common_tags
}

resource "google_dns_managed_zone" "main" {
  count       = var.enable_gcp_resources && var.custom_domain != "" ? 1 : 0
  name        = replace(local.full_name, "-", "")
  dns_name    = "${var.custom_domain}."
  description = "DNS zone for ${var.service_name}"

  labels = {
    service     = var.service_name
    environment = var.environment
    managed-by  = "cloud-function-saas"
  }
}

# SSL/TLS Certificate management
resource "aws_acm_certificate" "cert" {
  count           = var.enable_aws_resources && var.custom_domain != "" ? 1 : 0
  domain_name     = var.custom_domain
  validation_method = "DNS"

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_managed_ssl_certificate" "cert" {
  count = var.enable_gcp_resources && var.custom_domain != "" ? 1 : 0
  name  = "${local.full_name}-cert"

  managed {
    domains = [var.custom_domain]
  }

  labels = {
    service     = var.service_name
    environment = var.environment
    managed-by  = "cloud-function-saas"
  }
}