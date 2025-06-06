"""Helpers for interacting with Jellyfin."""

import logging
from datetime import datetime
from typing import Tuple, Optional

import requests

logger = logging.getLogger(__name__)


def _headers(api_key: str) -> dict:
    return {"X-Emby-Token": api_key}


def test_jellyfin_connection(url: str, api_key: str) -> Tuple[bool, str]:
    """Try to reach the Jellyfin server and return status and message."""
    try:
        resp = requests.get(f"{url}/System/Info/Public", headers=_headers(api_key), timeout=5)
        if resp.status_code == 200:
            return True, "Connection successful"
        return False, f"Status code {resp.status_code}"
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Jellyfin connection failed: %s", exc)
        return False, str(exc)


def get_latest_item_time(url: str, api_key: str) -> Optional[datetime]:
    """Return the creation time of the most recently added library item."""
    try:
        logger.debug("Querying Jellyfin for latest item")
        resp = requests.get(
            f"{url}/Items/Latest",
            params={"Limit": 1},
            headers=_headers(api_key),
            timeout=5,
        )
        if resp.status_code == 200 and resp.json():
            item = resp.json()[0]
            created = datetime.fromisoformat(item["DateCreated"].rstrip("Z"))
            logger.debug("Latest item time: %s", created)
            return created
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Failed to query Jellyfin latest item: %s", exc)
    return None

