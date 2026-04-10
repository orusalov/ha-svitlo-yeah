"""DTEK OEM coordinator — live API for Odesa Oblast."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...api.dtek.oem import DtekOemAPI
from ...models.providers import DtekOemProvider
from .ajax_api import DtekAjaxCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class DtekOemCoordinator(DtekAjaxCoordinator):
    """Coordinator for DTEK OEM live API."""

    _api_class = DtekOemAPI

    @property
    def provider(self) -> DtekOemProvider:
        """Get the configured provider."""
        return DtekOemProvider()
