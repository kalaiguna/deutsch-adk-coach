"""Web search tool — Google Custom Search API, scoped to German news sources."""
import logging
import urllib.parse
import urllib.request
import json
from src import config

logger = logging.getLogger(__name__)

_ALLOWED_DOMAINS = [
    "tagesschau.de",
    "spiegel.de",
    "heise.de",
    "handelsblatt.com",
    "dw.com",
    "easygerman.org",
    "zdf.de",
    "sz.de",
]


def search_german_article(query: str, source_type: str = "reading") -> dict:
    """Search for a real German-language article or podcast episode.

    Args:
        query: Search terms in German (topic or keywords).
        source_type: "reading" targets news articles (tagesschau, Spiegel, Heise, Handelsblatt);
                     "listening" targets audio/transcript sources (DW, Easy German).

    Returns:
        dict with keys: title, url, snippet — or error key on failure.
    """
    if not config.GOOGLE_SEARCH_API_KEY or not config.GOOGLE_SEARCH_CX:
        logger.warning("GOOGLE_SEARCH_API_KEY or GOOGLE_SEARCH_CX not set; returning stub result")
        return {
            "error": "Search API not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in .env."
        }

    if source_type == "listening":
        site_filter = " OR ".join(f"site:{d}" for d in ["dw.com", "easygerman.org"])
    else:
        site_filter = " OR ".join(
            f"site:{d}" for d in ["tagesschau.de", "spiegel.de", "heise.de", "handelsblatt.com"]
        )

    full_query = f"{query} {site_filter}"
    params = urllib.parse.urlencode({
        "key": config.GOOGLE_SEARCH_API_KEY,
        "cx": config.GOOGLE_SEARCH_CX,
        "q": full_query,
        "lr": "lang_de",
        "num": 3,
    })
    url = f"https://www.googleapis.com/customsearch/v1?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        items = data.get("items", [])
        if not items:
            return {"error": "No results found for this query."}
        item = items[0]
        return {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
    except Exception as e:
        logger.error("Search API error: %s", e)
        return {"error": str(e)}
