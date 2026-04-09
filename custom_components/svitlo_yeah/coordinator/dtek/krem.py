"""DTEK KREM coordinator — live API for Kyiv Oblast."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...api.dtek.krem import DtekKremAPI, parse_cookie_string
from ...const import CONF_COOKIES
from ...models.providers import DtekKremProvider
from .base import DtekCoordinatorBase

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class DtekKremCoordinator(DtekCoordinatorBase):
    """Coordinator for DTEK KREM live API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(hass=hass, config_entry=config_entry)
        cookie_str = config_entry.options.get(
            CONF_COOKIES,
            config_entry.data.get(CONF_COOKIES, ""),
        )
        cookies = parse_cookie_string(cookie_str)
        self.api = DtekKremAPI(cookies=cookies, group=self.group)

    @property
    def provider(self) -> DtekKremProvider:
        """Get the configured provider."""
        return DtekKremProvider()
