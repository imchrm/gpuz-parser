import logging
from collections.abc import Callable
from typing import Optional

import requests

from src.collectors.rubric_collector import _collect_from_listing
from src.config import BASE_URL
from src.models import Company, SearchParams

logger = logging.getLogger(__name__)


def collect_city(
    session: requests.Session,
    city_id: int,
    params: SearchParams,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Company]:
    start_url = f"{BASE_URL}/city/?Id={city_id}"
    return _collect_from_listing(
        session=session,
        start_url=start_url,
        params=params,
        source_rubric_id=None,
        progress_callback=progress_callback,
    )
