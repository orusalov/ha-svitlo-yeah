"""DTEK OEM live API implementation for Odesa Oblast."""

from __future__ import annotations

from ...const import DTEK_OEM_AJAX_URL, DTEK_OEM_ORIGIN, DTEK_OEM_SHUTDOWNS_URL
from .ajax_api import DtekAjaxAPIBase


class DtekOemAPI(DtekAjaxAPIBase):
    """DTEK OEM live API — fetches data directly from dtek-oem.com.ua."""

    _csrf_cookie_name = "_csrf-dtek-oem"
    _ajax_url = DTEK_OEM_AJAX_URL
    _shutdowns_url = DTEK_OEM_SHUTDOWNS_URL
    _origin = DTEK_OEM_ORIGIN
    _log_prefix = "DTEK OEM"
