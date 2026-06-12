from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Optional

import requests

from src.config import BASE_URL
from src.http_client import fetch_page, fetch_phones
from src.models import Company, SearchParams
from src.parsers.company_parser import parse_company_page, parse_phones
from src.parsers.listing_parser import get_next_page_url, parse_company_ids

logger = logging.getLogger(__name__)

SEARCH_URL = f"{BASE_URL}/search/"

# WARNING: /search/* is blocked by robots.txt (Disallow: */search/*).
# Use rubric or city collectors instead.


def collect_keyword(
    session: requests.Session,
    keyword: str,
    params: SearchParams,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Company]:
    # TODO: Verify exact POST parameter names via network inspection.
    # Placeholder names: SearchForm[keyword] and SearchForm[city_id].
    post_data: dict[str, object] = {"SearchForm[keyword]": keyword}
    if params.city_id is not None:
        post_data["SearchForm[city_id]"] = params.city_id

    companies: list[Company] = []
    total_collected = 0

    try:
        response = session.post(SEARCH_URL, data=post_data, timeout=(10, 30))
        response.raise_for_status()
        html = response.text
    except Exception as exc:
        logger.error("Failed to POST search for keyword '%s': %s", keyword, exc)
        return companies

    current_url: Optional[str] = SEARCH_URL

    while html:
        company_ids = parse_company_ids(html)
        if not company_ids:
            break

        for company_id in company_ids:
            if params.limit is not None and total_collected >= params.limit:
                return companies

            company_html = fetch_page(
                session,
                f"{BASE_URL}/company/?Id={company_id}",
                params.delay_min,
                params.delay_max,
            )
            if not company_html:
                logger.warning("Empty response for company %d", company_id)
                continue

            company = parse_company_page(company_html, company_id)

            phones_html = fetch_phones(session, company_id)
            if phones_html:
                company.phones = parse_phones(phones_html)

            companies.append(company)
            total_collected += 1

            if progress_callback:
                progress_callback(total_collected, 0)

        next_url = get_next_page_url(html, BASE_URL)
        if not next_url or next_url == current_url:
            break
        current_url = next_url
        html = fetch_page(session, next_url, params.delay_min, params.delay_max)

    return companies
