"""DTEK KREM live API implementation for Kyiv Oblast."""

from __future__ import annotations

from ...const import DTEK_KREM_AJAX_URL, DTEK_KREM_ORIGIN, DTEK_KREM_SHUTDOWNS_URL
from .ajax_api import DtekAjaxAPIBase


class DtekKremAPI(DtekAjaxAPIBase):
    """DTEK KREM live API — fetches data directly from dtek-krem.com.ua."""

    _csrf_cookie_name = "_csrf-dtek-krem"
    _ajax_url = DTEK_KREM_AJAX_URL
    _shutdowns_url = DTEK_KREM_SHUTDOWNS_URL
    _origin = DTEK_KREM_ORIGIN
    _log_prefix = "DTEK KREM"
