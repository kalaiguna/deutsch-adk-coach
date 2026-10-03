"""Web fetch tool — retrieves and strips a German article or transcript page."""
import logging
import urllib.parse
import urllib.request
import html
import re
from src.tools.web_search_tool import _ALLOWED_DOMAINS

logger = logging.getLogger(__name__)

_MAX_CHARS = 6000


def _is_allowed_url(url: str) -> bool:
    try:
        hostname = urllib.parse.urlparse(url).hostname or ""
        return any(hostname == d or hostname.endswith("." + d) for d in _ALLOWED_DOMAINS)
    except Exception:
        return False


def fetch_article_text(url: str) -> dict:
    """Fetch and return the plain text of a German article or transcript URL.

    Strips HTML tags and collapses whitespace. Truncates to 6000 characters
    so the result fits comfortably within a model context window.

    Args:
        url: Full HTTPS URL of the article or transcript page. Must be from an allowed domain.

    Returns:
        dict with keys: url, text — or error key on failure.
    """
    if not url or not url.startswith("https://"):
        return {"error": "url must be a valid https:// address."}
    if not _is_allowed_url(url):
        return {"error": f"Domain not in allowlist. Only approved German news sources are supported."}

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DeutschCoachBot/2.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        # Strip script/style blocks
        raw = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        # Strip remaining tags
        text = re.sub(r"<[^>]+>", " ", raw)
        # Decode HTML entities
        text = html.unescape(text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Truncate
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS] + "…"

        return {"url": url, "text": text}

    except Exception as e:
        logger.error("Fetch error for %s: %s", url, e)
        return {"error": str(e)}
