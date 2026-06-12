from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

from src.config import BASE_URL
from src.models import Company, WorkingHours


def parse_company_page(html: str, company_id: int) -> Company:
    soup = BeautifulSoup(html, "lxml")
    url = f"{BASE_URL}/company/?Id={company_id}"

    name = _parse_name(soup)
    alt_names = _parse_alt_names(soup)
    city = _parse_link_text(soup, "/city/?Id=")
    district = _parse_link_text(soup, "/district/?Id=")
    street = _parse_link_text(soup, "/street/?Id=")
    building = _parse_building(soup)
    postal_code = _parse_link_text(soup, "/orgbyindex/?Id=")
    region = _parse_link_text(soup, "/region/?Id=")
    landmarks = _parse_landmarks(soup)
    activity_types, rubric_ids = _parse_rubrics(soup)
    inn = _parse_inn(soup)
    years_on_site = _parse_years(soup)
    last_updated = _parse_last_updated(soup)
    rating = _parse_rating(soup)
    review_count = _parse_review_count(soup)
    working_hours = _parse_working_hours(soup)
    website, telegram = _parse_external_links(soup)

    return Company(
        company_id=company_id,
        url=url,
        name=name,
        alt_names=alt_names,
        city=city,
        district=district,
        street=street,
        building=building,
        postal_code=postal_code,
        region=region,
        landmarks=landmarks,
        activity_types=activity_types,
        rubric_ids=rubric_ids,
        inn=inn,
        years_on_site=years_on_site,
        last_updated=last_updated,
        rating=rating,
        review_count=review_count,
        working_hours=working_hours,
        website=website,
        telegram=telegram,
    )


def parse_phones(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    phones: list[str] = []
    for tag in soup.find_all("a", href=re.compile(r"^tel:")):
        href = tag.get("href", "")
        number = href.removeprefix("tel:")
        if number:
            phones.append(number)
    return phones


def _parse_name(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1")
    if not h1:
        return None
    text = h1.get_text(strip=True)
    # Remove trailing city in parentheses e.g. "Company Name (Ташкент)"
    text = re.sub(r"\s*\([^)]+\)\s*$", "", text).strip()
    return text or None


def _parse_alt_names(soup: BeautifulSoup) -> list[str]:
    h1 = soup.find("h1")
    if not h1:
        return []
    sibling = h1.find_next_sibling()
    if not sibling:
        return []
    text = sibling.get_text(strip=True)
    if not text:
        return []
    return [s.strip() for s in text.split(";") if s.strip()]


def _parse_link_text(soup: BeautifulSoup, path: str) -> Optional[str]:
    tag = soup.find("a", href=re.compile(re.escape(path)))
    if not tag:
        return None
    return tag.get_text(strip=True) or None


def _parse_building(soup: BeautifulSoup) -> Optional[str]:
    street_tag = soup.find("a", href=re.compile(r"/street/\?Id="))
    if not street_tag:
        return None
    # Building number is usually the text node immediately after the street link
    next_node = street_tag.next_sibling
    if next_node:
        text = str(next_node).strip().lstrip(",").strip()
        return text or None
    return None


def _parse_landmarks(soup: BeautifulSoup) -> list[str]:
    text_node = soup.find(string=re.compile(r"Ориентиры:"))
    if not text_node:
        return []
    parent = text_node.parent
    if not parent:
        return []
    full_text = parent.get_text(strip=True)
    part = full_text.split("Ориентиры:", 1)[-1].strip()
    return [s.strip() for s in part.split(";") if s.strip()]


def _parse_rubrics(soup: BeautifulSoup) -> tuple[list[str], list[int]]:
    activity_types: list[str] = []
    rubric_ids: list[int] = []
    for tag in soup.find_all("a", href=re.compile(r"/rubrics/\?Id=")):
        text = tag.get_text(strip=True)
        href = tag.get("href", "")
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        ids = qs.get("Id", [])
        if ids:
            try:
                rubric_ids.append(int(ids[0]))
            except ValueError:
                pass
        if text:
            activity_types.append(text)
    return activity_types, rubric_ids


def _parse_inn(soup: BeautifulSoup) -> Optional[str]:
    text_node = soup.find(string=re.compile(r"ИНН:"))
    if not text_node:
        return None
    parent = text_node.parent
    if not parent:
        return None
    full_text = parent.get_text(strip=True)
    match = re.search(r"ИНН:\s*(\S+)", full_text)
    return match.group(1) if match else None


def _parse_years(soup: BeautifulSoup) -> Optional[int]:
    text_node = soup.find(string=re.compile(r"\d+\s+лет\s+на\s+сайте"))
    if not text_node:
        return None
    match = re.search(r"(\d+)\s+лет\s+на\s+сайте", str(text_node))
    return int(match.group(1)) if match else None


def _parse_last_updated(soup: BeautifulSoup) -> Optional[str]:
    text_node = soup.find(string=re.compile(r"Обновлено:"))
    if not text_node:
        return None
    match = re.search(r"Обновлено:\s*(\d{2}\.\d{2}\.\d{4})", str(text_node))
    if match:
        return match.group(1)
    parent = text_node.parent
    if parent:
        full_text = parent.get_text(strip=True)
        match2 = re.search(r"Обновлено:\s*(\d{2}\.\d{2}\.\d{4})", full_text)
        return match2.group(1) if match2 else None
    return None


def _parse_rating(soup: BeautifulSoup) -> Optional[float]:
    # Rating is typically in a span/div with numeric content near review section
    tag = soup.find(class_=re.compile(r"rating|stars", re.I))
    if not tag:
        return None
    text = tag.get_text(strip=True)
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            pass
    return None


def _parse_review_count(soup: BeautifulSoup) -> Optional[int]:
    text_node = soup.find(string=re.compile(r"отзыв", re.I))
    if not text_node:
        return None
    match = re.search(r"(\d+)", str(text_node))
    return int(match.group(1)) if match else None


def _parse_working_hours(soup: BeautifulSoup) -> list[WorkingHours]:
    hours: list[WorkingHours] = []
    # Look for table rows with day names
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        day_text = cells[0].get_text(strip=True)
        if not day_text:
            continue
        time_text = cells[1].get_text(strip=True)
        if re.search(r"выходн", time_text, re.I):
            hours.append(WorkingHours(day=day_text, is_day_off=True))
            continue
        # Try to parse open-close and lunch times
        time_match = re.match(r"(\d{2}:\d{2})\s*[-–]\s*(\d{2}:\d{2})", time_text)
        if time_match:
            wh = WorkingHours(
                day=day_text,
                open_time=time_match.group(1),
                close_time=time_match.group(2),
            )
            lunch_match = re.search(
                r"обед[:\s]*(\d{2}:\d{2})\s*[-–]\s*(\d{2}:\d{2})", time_text, re.I
            )
            if lunch_match:
                wh.lunch_start = lunch_match.group(1)
                wh.lunch_end = lunch_match.group(2)
            hours.append(wh)
    return hours


def _parse_external_links(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    website: Optional[str] = None
    telegram: Optional[str] = None
    for tag in soup.find_all("a", href=re.compile(r"/go/\?u=")):
        href = tag.get("href", "")
        title = tag.get("title", "")
        text = tag.get_text(strip=True)
        if "t.me" in title or "t.me" in text or "telegram" in title.lower():
            if telegram is None:
                telegram = href
        else:
            if website is None:
                website = href
    return website, telegram
