import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_company_ids(html: str) -> list[int]:
    soup = BeautifulSoup(html, "lxml")
    ids: list[int] = []
    seen: set[int] = set()
    for tag in soup.find_all("a", href=re.compile(r"/company/\?Id=\d+")):
        match = re.search(r"Id=(\d+)", tag.get("href", ""))
        if match:
            company_id = int(match.group(1))
            if company_id not in seen:
                seen.add(company_id)
                ids.append(company_id)
    return ids


def get_total_count(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    match_tag = soup.find(string=re.compile(r"Найдено организаций:\s*\d+"))
    if not match_tag:
        return 0
    match = re.search(r"Найдено организаций:\s*(\d+)", str(match_tag))
    return int(match.group(1)) if match else 0


def get_next_page_url(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    # Look for a "Следующая" link first
    next_tag = soup.find("a", string=re.compile(r"Следующая|След\.|»", re.I))
    if next_tag and next_tag.get("href"):
        return urljoin(base_url, str(next_tag["href"]))

    # Fall back: find the active page number, then look for the next one
    paginator = soup.find(class_=re.compile(r"paginat|pagination|pager", re.I))
    if not paginator:
        return None

    active = paginator.find(class_=re.compile(r"active|current|selected", re.I))
    if not active:
        return None

    # Find the next sibling anchor after the active element
    next_sibling = active.find_next_sibling("a")
    if next_sibling and next_sibling.get("href"):
        return urljoin(base_url, str(next_sibling["href"]))

    return None
