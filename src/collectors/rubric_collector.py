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


def collect_rubric(
    session: requests.Session,
    rubric_id: int,
    params: SearchParams,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Company]:
    companies: list[Company] = []
    url: Optional[str] = f"{BASE_URL}/rubrics/?Id={rubric_id}"
    total_collected = 0

    while url:
        html = fetch_page(session, url, params.delay_min, params.delay_max)
        if not html:
            logger.warning("Empty response for URL: %s", url)
            break

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
            company.source_rubric_id = rubric_id

            phones_html = fetch_phones(session, company_id)
            if phones_html:
                company.phones = parse_phones(phones_html)

            companies.append(company)
            total_collected += 1

            if progress_callback:
                progress_callback(total_collected, 0)

        next_url = get_next_page_url(html, BASE_URL)
        url = next_url

    return companies
