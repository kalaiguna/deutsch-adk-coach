# Secrets are stored in Secret Manager and injected into Cloud Run / Cloud Functions
# as environment variables at runtime.

locals {
  secrets = {
    gemini-api-key         = var.gemini_api_key
    telegram-bot-token     = var.telegram_bot_token
    google-search-api-key  = var.google_search_api_key
    google-search-cx       = var.google_search_cx
  }
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = local.secrets
  secret_id = "deutsch-adk-coach-${each.key}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "versions" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value
}

# Service account used by both Cloud Run and Cloud Functions
resource "google_service_account" "app" {
  account_id   = "deutsch-adk-coach"
  display_name = "deutsch-adk-coach runtime"
}

# Allow the service account to read secrets
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Allow the service account to write to Firestore
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}
