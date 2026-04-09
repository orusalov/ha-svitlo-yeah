"""DTEK KREM live API implementation for Kyiv Oblast."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import aiohttp

from ...const import DTEK_KREM_AJAX_URL, DTEK_KREM_SHUTDOWNS_URL
from .base import DtekAPIBase

if TYPE_CHECKING:
    pass

LOGGER = logging.getLogger(__name__)

_CSRF_META_RE = re.compile(r'<meta\s+name="csrf-token"\s+content="([^"]+)"')
_INITIAL_UPDATE = "01.01.2020 00:00"

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0)"
        " Gecko/20100101 Firefox/120.0"
    ),
    "Accept-Language": "uk,en-US;q=0.7,en;q=0.3",
}


_COOKIE_ATTR_NAMES = frozenset(
    {"domain", "path", "expires", "max-age", "samesite", "httponly", "secure"}
)


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
        elif part.lower() not in _COOKIE_ATTR_NAMES:
            # flags like HttpOnly, Secure — skip silently
            pass
    return cookies


class DtekKremAPI(DtekAPIBase):
    """DTEK KREM live API — fetches data directly from dtek-krem.com.ua."""

    def __init__(self, cookies: dict[str, str], group: str | None = None) -> None:
        """Initialize with browser cookies."""
        super().__init__(group)
        self._cookies = cookies
        self._last_update: str = _INITIAL_UPDATE

    async def _fetch_csrf_token(self, session: aiohttp.ClientSession) -> str | None:
        """Get a fresh CSRF token by loading the shutdowns page."""
        try:
            async with session.get(
                DTEK_KREM_SHUTDOWNS_URL,
                headers={
                    **_BROWSER_HEADERS,
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                html = await response.text()
                match = _CSRF_META_RE.search(html)
                if match:
                    return match.group(1)
                LOGGER.warning("DTEK KREM: CSRF token not found in page HTML")
        except aiohttp.ClientError:
            LOGGER.exception("DTEK KREM: Error fetching page for CSRF token")
        return None

    async def fetch_data(self) -> None:
        """Fetch outage data from DTEK KREM API."""
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            csrf_token = await self._fetch_csrf_token(session)
            if not csrf_token:
                LOGGER.error("DTEK KREM: Cannot proceed without CSRF token")
                return

            try:
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
