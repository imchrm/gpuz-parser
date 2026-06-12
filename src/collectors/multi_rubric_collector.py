from __future__ import annotations

import logging

import requests

from src.collectors.rubric_collector import collect_rubric
from src.models import Company, ScraperResult, SearchParams

logger = logging.getLogger(__name__)


def collect_rubrics(
    session: requests.Session,
    rubric_ids: list[int],
    params: SearchParams,
) -> tuple[list[Company], ScraperResult]:
    all_companies: dict[int, Company] = {}
    duplicates = 0
    errors: list[str] = []

    for rubric_id in rubric_ids:
        logger.info("Collecting rubric %d", rubric_id)
        try:
            companies = collect_rubric(session, rubric_id, params)
        except Exception as exc:
            msg = f"Error collecting rubric {rubric_id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            continue

        for company in companies:
            if company.company_id in all_companies:
                duplicates += 1
            else:
                all_companies[company.company_id] = company

    result_list = list(all_companies.values())
    result = ScraperResult(
        total_found=len(result_list) + duplicates,
        total_exported=len(result_list),
        duplicates_removed=duplicates,
        errors=errors,
    )
    return result_list, result
