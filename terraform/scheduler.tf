# Dedicated service account for Cloud Scheduler so it can invoke Cloud Run
resource "google_service_account" "scheduler" {
  account_id   = "deutsch-adk-scheduler"
  display_name = "deutsch-adk-coach Cloud Scheduler invoker"
}

locals {
  bot_url = google_cloud_run_v2_service.bot.uri

  scheduler_jobs = {
    conversation = {
      description = "Tuesday + Thursday daily conversation (09:00 Berlin)"
      schedule    = "0 9 * * 2,4"
      route       = "/trigger/conversation"
    }
    quiz = {
      description = "Friday quiz review (09:00 Berlin)"
      schedule    = "0 9 * * 5"
      route       = "/trigger/quiz"
    }
    hoeren = {
      description = "Sunday listening comprehension (09:00 Berlin)"
      schedule    = "0 9 * * 0"
      route       = "/trigger/hoeren"
    }
    bericht = {
      description = "1st of month monthly report (08:00 Berlin)"
      schedule    = "0 8 1 * *"
      route       = "/trigger/bericht"
    }
    grammatik = {
      description = "10th of month grammar deep-dive (09:00 Berlin)"
      schedule    = "0 9 10 * *"
      route       = "/trigger/grammatik"
    }
  }
}

resource "google_cloud_scheduler_job" "sessions" {
  for_each = local.scheduler_jobs

  name             = "deutsch-adk-${each.key}"
  description      = each.value.description
  schedule         = each.value.schedule
  time_zone        = "Europe/Berlin"
  attempt_deadline = "30s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${local.bot_url}${each.value.route}"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = local.bot_url
    }
  }

  depends_on = [google_project_service.apis]
}
