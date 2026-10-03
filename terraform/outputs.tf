output "bot_url" {
  description = "Cloud Run URL for the Telegram bot"
  value       = google_cloud_run_v2_service.bot.uri
}

output "token_endpoint_url" {
  description = "Cloud Function URL for the browser token endpoint"
  value       = google_cloudfunctions2_function.token_endpoint.url
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.default.name
}

output "budget_pubsub_topic" {
  description = "Pub/Sub topic receiving budget alert notifications"
  value       = google_pubsub_topic.budget_alerts.id
}

output "service_account_email" {
  description = "Runtime service account used by Cloud Run and Cloud Functions"
  value       = google_service_account.app.email
}
