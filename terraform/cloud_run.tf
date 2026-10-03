resource "google_cloud_run_v2_service" "bot" {
  name     = "deutsch-adk-coach"
  location = var.region

  deletion_protection = false

  template {
    service_account = google_service_account.app.email

    scaling {
      max_instance_count = 1
    }

    max_instance_request_concurrency = 1

    containers {
      image = var.bot_image

      resources {
        limits = {
          memory = var.bot_memory
          cpu    = var.bot_cpu
        }
        startup_cpu_boost = true
      }

      # Secrets injected as env vars from Secret Manager
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["gemini-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "TELEGRAM_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["telegram-bot-token"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_SEARCH_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["google-search-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_SEARCH_CX"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["google-search-cx"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "USE_LOCAL_STORAGE"
        value = "false"
      }

      env {
        name  = "ALLOWED_TELEGRAM_USERS"
        value = var.allowed_telegram_users
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.versions,
  ]
}

# Allow Cloud Scheduler to invoke the bot's trigger routes
resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.bot.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}
