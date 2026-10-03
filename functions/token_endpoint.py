"""Cloud Function — POST /token
Returns a short-lived Gemini API key for the browser to use with the Live API.
The real GEMINI_API_KEY is never exposed to the client.

Deploy:
  gcloud functions deploy gemini-token \
    --gen2 --runtime python312 --trigger-http \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY=<key> \
    --entry-point token_endpoint \
    --region europe-west1
"""
import os
import functions_framework
from flask import jsonify

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash-live-001")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


@functions_framework.http
def token_endpoint(request):
    if request.method == "OPTIONS":
        return ("", 204, CORS_HEADERS)

    if request.method != "POST":
        return (jsonify({"error": "Method not allowed"}), 405, CORS_HEADERS)

    if not GEMINI_API_KEY:
        return (jsonify({"error": "GEMINI_API_KEY not configured on server"}), 500, CORS_HEADERS)

    # For Gemini Live API the browser connects directly using the API key.
    # In production, replace this with a proper short-lived credential exchange
    # (e.g. Firebase App Check + signed token) to scope usage per user.
    payload = {"token": GEMINI_API_KEY, "model": GEMINI_MODEL}
    return (jsonify(payload), 200, CORS_HEADERS)
