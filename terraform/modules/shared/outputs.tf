# Shared Module Outputs

output "service_name" {
  description = "Name of the service"
  value       = var.service_name
}

output "full_service_name" {
  description = "Full service name with suffix"
  value       = local.full_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# AWS Outputs
output "aws_account_id" {
  description = "AWS Account ID (if AWS resources enabled)"
  value       = var.enable_aws_resources ? data.aws_caller_identity.current[0].account_id : null
}

output "aws_region" {
  description = "AWS Region (if AWS resources enabled)"
  value       = var.enable_aws_resources ? data.aws_region.current[0].name : null
}

output "aws_secrets_arn" {
  description = "ARN of AWS Secrets Manager secret (if created)"
  value       = var.enable_aws_resources && var.create_shared_secrets ? aws_secretsmanager_secret.shared_config[0].arn : null
}

output "aws_route53_zone_id" {
  description = "Route53 hosted zone ID (if created)"
  value       = var.enable_aws_resources && var.custom_domain != "" ? aws_route53_zone.main[0].zone_id : null
}

output "aws_certificate_arn" {
  description = "ACM certificate ARN (if created)"
  value       = var.enable_aws_resources && var.custom_domain != "" ? aws_acm_certificate.cert[0].arn : null
}

# GCP Outputs
output "gcp_project_id" {
  description = "GCP Project ID (if GCP resources enabled)"
  value       = var.enable_gcp_resources ? data.google_project.project[0].project_id : null
}

output "gcp_region" {
  description = "GCP Region (if GCP resources enabled)"
  value       = var.enable_gcp_resources ? data.google_client_config.default[0].region : null
}

output "gcp_secret_id" {
  description = "GCP Secret Manager secret ID (if created)"
  value       = var.enable_gcp_resources && var.create_shared_secrets ? google_secret_manager_secret.shared_config[0].secret_id : null
}

output "gcp_dns_zone_name" {
  description = "GCP Cloud DNS zone name (if created)"
  value       = var.enable_gcp_resources && var.custom_domain != "" ? google_dns_managed_zone.main[0].name : null
}

output "gcp_certificate_name" {
  description = "GCP managed SSL certificate name (if created)"
  value       = var.enable_gcp_resources && var.custom_domain != "" ? google_compute_managed_ssl_certificate.cert[0].name : null
}

# Cross-Cloud Outputs
output "deployment_summary" {
  description = "Summary of deployed shared resources"
  value = {
    service_name        = local.full_name
    environment         = var.environment
    aws_enabled         = var.enable_aws_resources
    gcp_enabled         = var.enable_gcp_resources
    custom_domain       = var.custom_domain
    secrets_created     = var.create_shared_secrets
    monitoring_enabled  = var.enable_datadog_monitoring || var.enable_newrelic_monitoring
    ssl_enabled         = var.custom_domain != "" && var.create_ssl_certificate
    deployed_at         = timestamp()
  }
}

output "resource_identifiers" {
  description = "Key resource identifiers for cross-cloud reference"
  value = {
    aws = var.enable_aws_resources ? {
      account_id      = data.aws_caller_identity.current[0].account_id
      region         = data.aws_region.current[0].name
      secrets_arn    = var.create_shared_secrets ? aws_secretsmanager_secret.shared_config[0].arn : null
      zone_id        = var.custom_domain != "" ? aws_route53_zone.main[0].zone_id : null
      certificate_arn = var.custom_domain != "" ? aws_acm_certificate.cert[0].arn : null
    } : null
    
    gcp = var.enable_gcp_resources ? {
      project_id      = data.google_project.project[0].project_id
      region         = data.google_client_config.default[0].region
      secret_id      = var.create_shared_secrets ? google_secret_manager_secret.shared_config[0].secret_id : null
      dns_zone       = var.custom_domain != "" ? google_dns_managed_zone.main[0].name : null
      certificate    = var.custom_domain != "" ? google_compute_managed_ssl_certificate.cert[0].name : null
    } : null
  }
  sensitive = true
}

output "monitoring_config" {
  description = "Monitoring configuration for external systems"
  value = {
    service_name      = local.full_name
    environment       = var.environment
    endpoints         = var.monitoring_endpoints
    datadog_enabled   = var.enable_datadog_monitoring
    newrelic_enabled  = var.enable_newrelic_monitoring
    pagerduty_enabled = var.enable_pagerduty
    alert_email       = var.alert_email
  }
  sensitive = true
}

output "dns_configuration" {
  description = "DNS configuration for domain setup"
  value = var.custom_domain != "" ? {
    domain             = var.custom_domain
    aws_zone_id        = var.enable_aws_resources ? aws_route53_zone.main[0].zone_id : null
    aws_name_servers   = var.enable_aws_resources ? aws_route53_zone.main[0].name_servers : null
    gcp_zone_name      = var.enable_gcp_resources ? google_dns_managed_zone.main[0].name : null
    gcp_name_servers   = var.enable_gcp_resources ? google_dns_managed_zone.main[0].name_servers : null
  } : null
}