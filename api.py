"""Live data (APIs unit): fetch currency exchange rates from a free REST API."""
import json
import logging
import urllib.request

API_URL = "https://open.er-api.com/v6/latest/ZAR"
log = logging.getLogger(__name__)


def fetch_rates(timeout: int = 8) -> dict[str, float]:
    """Return {currency: rate} relative to ZAR. Raises RuntimeError on failure."""
    try:
        with urllib.request.urlopen(API_URL, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("result") != "success":
            raise RuntimeError("API returned an error")
        return data["rates"]
    except Exception as e:  # network, JSON, or key errors
        log.error("Rate fetch failed: %s", e)
        raise RuntimeError("Could not load live rates. Check your internet connection.") from e
