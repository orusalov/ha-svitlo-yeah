"""DTEK KREM live API implementation for Kyiv Oblast."""

from __future__ import annotations

import base64
import logging
import re
import secrets
import string
from urllib.parse import unquote

import aiohttp

from ...const import DTEK_KREM_AJAX_URL, DTEK_KREM_SHUTDOWNS_URL
from .base import DtekAPIBase

LOGGER = logging.getLogger(__name__)

_INITIAL_UPDATE = "01.01.2020 00:00"
_CSRF_COOKIE_NAME = "_csrf-dtek-krem"
_CSRF_TOKEN_RE = re.compile(r's:\d+:"([^"]+)";\}$')
_COOKIE_ATTR_NAMES = frozenset(
    {"domain", "path", "expires", "max-age", "samesite", "httponly", "secure"}
)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0)"
        " Gecko/20100101 Firefox/120.0"
    ),
    "Accept-Language": "uk,en-US;q=0.7,en;q=0.3",
}


def parse_cookie_string(cookie_str: str) -> dict[str, str]:
    """Parse a Cookie header string into a dict, filtering Set-Cookie attributes."""
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, _, value = part.partition("=")
            key = key.strip()
            if key.lower() not in _COOKIE_ATTR_NAMES:
                cookies[key] = value.strip()
    return cookies


def _extract_raw_csrf_token(csrf_cookie_value: str) -> str | None:
    """Extract raw CSRF token from Yii2 _csrf cookie value.

    Cookie format (URL-encoded PHP serialized):
    hash:2:{i:0;s:15:"_csrf-dtek-krem";i:1;s:32:"RAW_TOKEN";}
    """
    decoded = unquote(csrf_cookie_value)
    match = _CSRF_TOKEN_RE.search(decoded)
    if match:
        return match.group(1)
    LOGGER.warning("DTEK KREM: Cannot extract raw token from CSRF cookie: %s", decoded)
    return None


def _mask_csrf_token(raw_token: str) -> str:
    """Generate a Yii2-compatible masked CSRF token.

    Yii2 masking: base64url(mask + (mask XOR raw_token))
    where mask is a random string of the same length as raw_token.
    """
    alphabet = string.ascii_letters + string.digits + "-_"
    mask = "".join(secrets.choice(alphabet) for _ in range(len(raw_token)))
    xored = bytes(a ^ b for a, b in zip(mask.encode(), raw_token.encode()))
    masked = base64.b64encode(mask.encode() + xored).decode()
    return masked.translate(str.maketrans("+/", "-_"))


class DtekKremAPI(DtekAPIBase):
    """DTEK KREM live API — fetches data directly from dtek-krem.com.ua."""

    def __init__(self, cookies: dict[str, str], group: str | None = None) -> None:
        """Initialize with browser cookies."""
        super().__init__(group)
        self._cookies = cookies
        self._last_update: str = _INITIAL_UPDATE

    def _get_csrf_token(self) -> str | None:
        """Build a masked CSRF token from the stored _csrf-dtek-krem cookie."""
        csrf_cookie = self._cookies.get(_CSRF_COOKIE_NAME)
        if not csrf_cookie:
            LOGGER.error("DTEK KREM: %s cookie not found", _CSRF_COOKIE_NAME)
            return None
        raw_token = _extract_raw_csrf_token(csrf_cookie)
        if not raw_token:
            return None
        return _mask_csrf_token(raw_token)

    async def fetch_data(self) -> None:
        """Fetch outage data from DTEK KREM API."""
        csrf_token = self._get_csrf_token()
        if not csrf_token:
            LOGGER.error("DTEK KREM: Cannot proceed without CSRF token")
            return

        try:
            async with aiohttp.ClientSession(cookies=self._cookies) as session:
                async with session.post(
                    DTEK_KREM_AJAX_URL,
                    headers={
                        **_BROWSER_HEADERS,
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Referer": DTEK_KREM_SHUTDOWNS_URL,
                        "X-CSRF-Token": csrf_token,
                        "X-Requested-With": "XMLHttpRequest",
                        "Origin": "https://www.dtek-krem.com.ua",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    },
                    data={
                        "method": "checkDisconUpdate",
                        "update": self._last_update,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)

        except (aiohttp.ClientError, ValueError):
            LOGGER.exception("DTEK KREM: Error fetching outage data")
            return

        if not data:
            LOGGER.warning("DTEK KREM: Empty response")
            return

        if not data.get("result"):
            LOGGER.debug(
                "DTEK KREM: No update since %s — cached data still valid",
                self._last_update,
            )
            return

        fact = data.get("fact")
        if not fact:
            LOGGER.warning("DTEK KREM: result=True but no 'fact' in response")
            return

        self.data = fact
        if "update" in fact:
            self._last_update = fact["update"]
        LOGGER.debug("DTEK KREM: Data updated, update=%s", self._last_update)
