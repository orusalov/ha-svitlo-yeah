"""Base coordinator for DTEK live (cookie-based) API implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...api.dtek.ajax_api import DtekAjaxAPIBase, parse_cookie_string
from ...const import CONF_COOKIES
from .base import DtekCoordinatorBase

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class DtekAjaxCoordinator(DtekCoordinatorBase):
    """Base coordinator for DTEK APIs that use cookie-based authentication."""

    _api_class: type[DtekAjaxAPIBase]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(hass=hass, config_entry=config_entry)
        cookie_str = config_entry.options.get(
            CONF_COOKIES,
            config_entry.data.get(CONF_COOKIES, ""),
        )
        cookies = parse_cookie_string(cookie_str)
        self.api = self._api_class(cookies=cookies, group=self.group)
