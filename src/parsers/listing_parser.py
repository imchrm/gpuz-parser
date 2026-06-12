from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup


def parse_company_ids(html: str) -> list[int]:
    soup = BeautifulSoup(html, "lxml")
    ids: list[int] = []
    seen: set[int] = set()
    for tag in soup.find_all("a", href=re.compile(r"/company/\?Id=")):
        href = tag.get("href", "")
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        id_vals = qs.get("Id", [])
        if id_vals:
            try:
                company_id = int(id_vals[0])
                if company_id not in seen:
                    seen.add(company_id)
                    ids.append(company_id)
            except ValueError:
                pass
    return ids


def get_total_count(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    text_node = soup.find(string=re.compile(r"Найдено организаций:"))
    if not text_node:
        return 0
    match = re.search(r"Найдено организаций:\s*(\d+)", str(text_node))
    if match:
        return int(match.group(1))
    # Try parent element text
    if text_node.parent:
        full_text = text_node.parent.get_text(strip=True)
        match2 = re.search(r"Найдено организаций:\s*(\d+)", full_text)
        if match2:
            return int(match2.group(1))
    return 0


def get_next_page_url(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    # Look for "Следующая" link
    next_tag = soup.find("a", string=re.compile(r"Следующ", re.I))
    if next_tag:
        href = next_tag.get("href", "")
        if href:
            return urljoin(base_url, str(href))
    # Look for pagination links and find next page number
    paginator = soup.find(class_=re.compile(r"paginat|pagination|pager", re.I))
    if paginator and isinstance(paginator, BeautifulSoup.__class__) or paginator:
        current_tag = paginator.find(class_=re.compile(r"active|current|selected", re.I)) if hasattr(paginator, 'find') else None  # type: ignore[union-attr]
        if current_tag:
            next_sibling = current_tag.find_next_sibling("a")
            if next_sibling:
                href = next_sibling.get("href", "")
                if href:
                    return urljoin(base_url, str(href))
    return None
