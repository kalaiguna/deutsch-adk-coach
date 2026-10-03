# GCS bucket for Cloud Function source archives
resource "google_storage_bucket" "functions_source" {
  name                        = var.functions_source_bucket
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

# Zip the functions/ directory and upload it
data "archive_file" "token_endpoint" {
  type        = "zip"
  source_dir  = "${path.root}/../functions"
  output_path = "${path.module}/.build/token_endpoint.zip"
}

resource "google_storage_bucket_object" "token_endpoint_source" {
  name   = "token_endpoint_${data.archive_file.token_endpoint.output_md5}.zip"
  bucket = google_storage_bucket.functions_source.name
  source = data.archive_file.token_endpoint.output_path
}

resource "google_cloudfunctions2_function" "token_endpoint" {
  name     = "token-endpoint"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "token_endpoint"

    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = google_storage_bucket_object.token_endpoint_source.name
      }
    }
  }

  service_config {
    max_instance_count               = 10
    min_instance_count               = 0
    available_memory                 = "256M"
    timeout_seconds                  = 30
    service_account_email            = google_service_account.app.email
    all_traffic_on_latest_revision   = true

    secret_environment_variables {
      key        = "GEMINI_API_KEY"
      project_id = var.project_id
      secret     = google_secret_manager_secret.secrets["gemini-api-key"].secret_id
      version    = "latest"
    }

    environment_variables = {
      GEMINI_MODEL = var.gemini_model
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.versions,
  ]
}

# Allow unauthenticated calls (browser needs to reach the token endpoint)
resource "google_cloud_run_v2_service_iam_member" "token_endpoint_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloudfunctions2_function.token_endpoint.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
