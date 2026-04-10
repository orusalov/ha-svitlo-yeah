"""DTEK KREM coordinator — live API for Kyiv Oblast."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...api.dtek.krem import DtekKremAPI
from ...models.providers import DtekKremProvider
from .ajax_api import DtekAjaxCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class DtekKremCoordinator(DtekAjaxCoordinator):
    """Coordinator for DTEK KREM live API."""

    _api_class = DtekKremAPI

    @property
    def provider(self) -> DtekKremProvider:
        """Get the configured provider."""
        return DtekKremProvider()
