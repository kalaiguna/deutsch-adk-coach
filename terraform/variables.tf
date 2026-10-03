variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Cloud Functions"
  type        = string
  default     = "europe-west1"
}

variable "billing_account_id" {
  description = "GCP billing account ID (format: XXXXXX-XXXXXX-XXXXXX)"
  type        = string
}

# ── Secrets ───────────────────────────────────────────────────────────────────

variable "gemini_api_key" {
  description = "Gemini API key (Google AI Studio or Vertex AI)"
  type        = string
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Telegram bot token from @BotFather"
  type        = string
  sensitive   = true
}

variable "google_search_api_key" {
  description = "Google Custom Search API key (required for /lektuere and /hoeren)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_search_cx" {
  description = "Google Programmable Search Engine CX ID"
  type        = string
  default     = ""
}

variable "allowed_telegram_users" {
  description = "Comma-separated Telegram user IDs allowed to use the bot. Empty = open."
  type        = string
  default     = ""
}

# ── Model ─────────────────────────────────────────────────────────────────────

variable "gemini_model" {
  description = "Gemini model ID"
  type        = string
  default     = "gemini-2.5-flash"
}

# ── Cloud Run ─────────────────────────────────────────────────────────────────

variable "bot_image" {
  description = "Container image URI for the Telegram bot (e.g. gcr.io/PROJECT/deutsch-adk-coach:latest)"
  type        = string
}

variable "bot_memory" {
  description = "Cloud Run memory allocation for the bot"
  type        = string
  default     = "512Mi"
}

variable "bot_cpu" {
  description = "Cloud Run CPU allocation for the bot"
  type        = string
  default     = "1"
}

# ── Cloud Functions ───────────────────────────────────────────────────────────

variable "functions_source_bucket" {
  description = "GCS bucket name for Cloud Function source archive"
  type        = string
}

# ── Budget ────────────────────────────────────────────────────────────────────

variable "monthly_budget_usd" {
  description = "Monthly GCP spend budget in USD. Alerts fire at 50%, 90%, and 100%."
  type        = number
  default     = 20
}

variable "budget_alert_email" {
  description = "Email address to receive budget alert notifications"
  type        = string
}
