# GCP Cloud Run Terraform Module
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Container Registry for storing images
resource "google_artifact_registry_repository" "container_repo" {
  count         = var.create_artifact_registry ? 1 : 0
  location      = var.region
  repository_id = "${var.service_name}-repo"
  description   = "Container repository for ${var.service_name}"
  format        = "DOCKER"

  labels = {
    service     = var.service_name
    environment = var.environment
    managed_by  = "cloud-function-saas"
  }
}

# Build the container image using Cloud Build
resource "google_cloudbuild_trigger" "build_trigger" {
  count       = var.enable_cloud_build ? 1 : 0
  name        = "${var.service_name}-build"
  description = "Build trigger for ${var.service_name}"

  # Manual trigger - can be extended for Git integration
  trigger_template {
    branch_name = "main"
    repo_name   = var.repo_name
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t", "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}-repo/${var.service_name}:latest",
        "."
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}-repo/${var.service_name}:latest"
      ]
    }

    images = [
      "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}-repo/${var.service_name}:latest"
    ]
  }

  tags = ["cloud-function-saas", var.service_name]
}

# Cloud Run Service
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    metadata {
      labels = {
        service     = var.service_name
        environment = var.environment
        managed_by  = "cloud-function-saas"
      }
      annotations = {
        "autoscaling.knative.dev/maxScale"        = var.max_instances
        "autoscaling.knative.dev/minScale"        = var.min_instances
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/cpu-throttling"       = "false"
      }
    }

    spec {
      container_concurrency = var.container_concurrency
      timeout_seconds      = var.timeout_seconds

      containers {
        image = var.container_image

        ports {
          container_port = var.container_port
          name          = "http1"
        }

        # Environment variables
        dynamic "env" {
          for_each = var.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }

        # Resource limits
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
          requests = {
            cpu    = var.cpu_request
            memory = var.memory_request
          }
        }

        # Health check
        liveness_probe {
          http_get {
            path = var.health_check_path
          }
          initial_delay_seconds = 30
          period_seconds       = 60
          timeout_seconds      = 10
          failure_threshold    = 3
        }

        startup_probe {
          http_get {
            path = var.health_check_path
          }
          initial_delay_seconds = 0
          period_seconds       = 10
          timeout_seconds      = 10
          failure_threshold    = 30
        }
      }

      # Service account for the service
      service_account_name = var.service_account_email != "" ? var.service_account_email : google_service_account.cloud_run_service[0].email
    }
  }

  # Traffic configuration
  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/operation-id"],
    ]
  }
}

# Service Account for Cloud Run service
resource "google_service_account" "cloud_run_service" {
  count        = var.service_account_email == "" ? 1 : 0
  account_id   = "${var.service_name}-service"
  display_name = "Cloud Run service account for ${var.service_name}"
  description  = "Service account used by ${var.service_name} Cloud Run service"
}

# IAM Policy for public access (if enabled)
resource "google_cloud_run_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = google_cloud_run_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom IAM bindings
resource "google_cloud_run_service_iam_member" "custom" {
  for_each = toset(var.invoker_members)
  location = google_cloud_run_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name
  role     = "roles/run.invoker"
  member   = each.value
}

# Monitoring and Logging (if enabled)
resource "google_monitoring_uptime_check_config" "uptime" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "${var.service_name} Uptime Check"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = var.health_check_path
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = google_cloud_run_service.service.status[0].url
    }
  }

  content_matchers {
    content = var.uptime_check_content
    matcher = "CONTAINS_STRING"
  }
}

# Log-based alerting policy
resource "google_monitoring_alert_policy" "error_rate" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "${var.service_name} Error Rate"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Error rate too high"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.type=\"run.googleapis.com/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.error_rate_threshold

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }

  notification_channels = var.notification_channels
}