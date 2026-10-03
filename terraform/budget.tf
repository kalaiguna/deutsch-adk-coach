# Pub/Sub topic — receives machine-readable budget alert notifications.
# A future subscriber can use this to disable paid commands when threshold is hit.
resource "google_pubsub_topic" "budget_alerts" {
  name = "deutsch-adk-budget-alerts"

  depends_on = [google_project_service.apis]
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "deutsch-adk-coach monthly budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(floor(var.monthly_budget_usd))
      nanos         = tonumber(floor((var.monthly_budget_usd - floor(var.monthly_budget_usd)) * 1000000000))
    }
  }

  # Alert at 50%, 90%, and 100% of budget
  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    # Email notification
    monitoring_notification_channels = [
      google_monitoring_notification_channel.budget_email.id,
    ]

    # Pub/Sub notification for programmatic subscribers
    pubsub_topic                     = google_pubsub_topic.budget_alerts.id
    disable_default_iam_notifications = false
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "budget_email" {
  display_name = "deutsch-adk-coach budget alerts"
  type         = "email"

  labels = {
    email_address = var.budget_alert_email
  }
}
