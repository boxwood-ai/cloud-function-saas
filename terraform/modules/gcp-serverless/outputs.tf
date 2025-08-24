# GCP Cloud Run Module Outputs

output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.service.name
}

output "service_id" {
  description = "Full resource ID of the Cloud Run service"
  value       = google_cloud_run_service.service.id
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_service.service.location
}

output "service_project" {
  description = "Project ID of the Cloud Run service"
  value       = google_cloud_run_service.service.project
}

output "service_account_email" {
  description = "Email of the service account used by the Cloud Run service"
  value       = var.service_account_email != "" ? var.service_account_email : google_service_account.cloud_run_service[0].email
}

output "service_account_id" {
  description = "ID of the service account used by the Cloud Run service"
  value       = var.service_account_email != "" ? var.service_account_email : google_service_account.cloud_run_service[0].account_id
}

output "latest_revision_name" {
  description = "Name of the latest revision"
  value       = google_cloud_run_service.service.status[0].latest_ready_revision_name
}

output "container_image" {
  description = "Container image used by the service"
  value       = var.container_image
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository (if created)"
  value       = var.create_artifact_registry ? google_artifact_registry_repository.container_repo[0].name : null
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL (if created)"
  value       = var.create_artifact_registry ? "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}-repo" : null
}

output "cloud_build_trigger_id" {
  description = "Cloud Build trigger ID (if created)"
  value       = var.enable_cloud_build ? google_cloudbuild_trigger.build_trigger[0].trigger_id : null
}

output "uptime_check_id" {
  description = "Uptime check ID (if monitoring enabled)"
  value       = var.enable_monitoring ? google_monitoring_uptime_check_config.uptime[0].uptime_check_id : null
}

output "alert_policy_name" {
  description = "Alert policy name (if monitoring enabled)"
  value       = var.enable_monitoring ? google_monitoring_alert_policy.error_rate[0].name : null
}

output "deployment_info" {
  description = "Comprehensive deployment information"
  value = {
    service_url     = google_cloud_run_service.service.status[0].url
    service_name    = google_cloud_run_service.service.name
    region         = var.region
    project_id     = var.project_id
    container_image = var.container_image
    environment    = var.environment
    deployed_at    = timestamp()
  }
}