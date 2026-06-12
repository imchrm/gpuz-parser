import logging
from collections.abc import Callable
from typing import Optional

import requests

from src.config import BASE_URL, DEFAULT_DELAY_MAX, DEFAULT_DELAY_MIN
from src.http_client import fetch_page, fetch_phones
from src.models import Company, SearchParams
from src.parsers.company_parser import parse_company_page, parse_phones
from src.parsers.listing_parser import get_next_page_url, parse_company_ids

logger = logging.getLogger(__name__)

SEARCH_URL = BASE_URL + "/search/"


def collect_keyword(
    session: requests.Session,
    keyword: str,
    params: SearchParams,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Company]:
    # TODO: exact POST parameter names need verification via DevTools on /search/
    # Placeholders based on Yii framework conventions observed on the site
    form_data = {
        "SearchForm[keyword]": keyword,
    }
    if params.city_id is not None:
        form_data["SearchForm[city_id]"] = str(params.city_id)

    try:
        resp = session.post(SEARCH_URL, data=form_data, timeout=(10, 30))
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.error("Search POST failed: %s", exc)
        return []

    companies: list[Company] = []
    collected = 0
    current_url: Optional[str] = None

    while True:
        company_ids = parse_company_ids(html)
        for company_id in company_ids:
            if params.limit is not None and collected >= params.limit:
                return companies

            company_html = fetch_page(session, f"{BASE_URL}/company/?Id={company_id}",
                                      params.delay_min, params.delay_max)
            if not company_html:
                continue

            company = parse_company_page(company_html, company_id)
            phones_html = fetch_phones(session, company_id)
            if phones_html:
                company.phones = parse_phones(phones_html)

            companies.append(company)
            collected += 1
            if progress_callback:
                progress_callback(collected, params.limit or 0)

        next_url = get_next_page_url(html, SEARCH_URL)
        if not next_url:
            break
        html = fetch_page(session, next_url, params.delay_min, params.delay_max)
        if not html:
            break

    return companies
