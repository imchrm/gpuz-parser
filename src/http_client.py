from __future__ import annotations

import logging
import random
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import PHONE_API_URL, USER_AGENT

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
def _get(session: requests.Session, url: str, **kwargs: object) -> requests.Response:
    response = session.get(url, timeout=(10, 30), **kwargs)  # type: ignore[arg-type]
    response.raise_for_status()
    return response


def fetch_page(
    session: requests.Session,
    url: str,
    delay_min: float = 1.5,
    delay_max: float = 3.5,
) -> str:
    try:
        response = _get(session, url)
        time.sleep(random.uniform(delay_min, delay_max))
        return response.text
    except Exception as exc:
        logger.error("Failed to fetch %s: %s", url, exc)
        return ""


def fetch_phones(session: requests.Session, company_id: int) -> str:
    url = PHONE_API_URL
    params = {"cid": company_id, "ctype": "phone", "clang": "ru"}
    try:
        response = _get(session, url, params=params)
        return response.text
    except Exception as exc:
        logger.error("Failed to fetch phones for company %d: %s", company_id, exc)
        return ""
