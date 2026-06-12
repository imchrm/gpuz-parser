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
    # Building number is the text node immediately after the street link
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
    # Anchor to relative paths only — avoids picking up absolute-URL nav links
    for tag in soup.find_all("a", href=re.compile(r"^/rubrics/\?Id=")):
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
    # Walk up ancestors until the INN value appears in combined text
    node = text_node.parent
    while node and node.name not in ("body", "html", "[document]"):
        full_text = node.get_text(strip=True)
        match = re.search(r"ИНН:\s*(\S+)", full_text)
        if match:
            return match.group(1)
        node = node.parent
    return None


def _parse_years(soup: BeautifulSoup) -> Optional[int]:
    # Matches "5 лет", "2 года", "1 год" на сайте
    text_node = soup.find(string=re.compile(r"\d+\s+(?:лет|год[а]?)\s+на\s+сайте"))
    if not text_node:
        return None
    match = re.search(r"(\d+)\s+(?:лет|год[а]?)\s+на\s+сайте", str(text_node))
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
    # Numeric rating in dedicated count element (e.g. class="review_all__count")
    tag = soup.find(class_=re.compile(r"review_all__count", re.I))
    if not tag:
        # Fallback for alternative markup
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
    # Real page uses "оценок: N | отзывов: N" pattern
    text_node = soup.find(string=re.compile(r"оценок:\s*\d+"))
    if text_node:
        match = re.search(r"оценок:\s*(\d+)", str(text_node))
        if match:
            return int(match.group(1))
    # Fallback: any text node with a number near "отзыв"
    text_node = soup.find(string=re.compile(r"\d+.*отзыв|\bотзыв.*\d+", re.I))
    if text_node:
        match = re.search(r"(\d+)", str(text_node))
        if match:
            return int(match.group(1))
    return None


def _parse_working_hours(soup: BeautifulSoup) -> list[WorkingHours]:
    hours: list[WorkingHours] = []

    # Real site uses <div class="gp_work_wrap"> rows inside a gp_work_time container
    work_section = soup.find(class_="gp_work_time")
    if work_section and hasattr(work_section, "find_all"):
        for row in work_section.find_all(class_="gp_work_wrap"):  # type: ignore[union-attr]
            classes = row.get("class") or []
            if "fw-600" in classes:
                continue  # header row
            cols = row.find_all("div", recursive=False)
            # "Сегодня" badge appears as an extra first col on the current day's row
            if cols and cols[0].get_text(strip=True) == "Сегодня":
                cols = cols[1:]
            if len(cols) < 2:
                continue
            day_text = cols[0].get_text(strip=True).rstrip(":")
            time_text = cols[1].get_text(strip=True)
            if re.search(r"выходн", time_text, re.I):
                hours.append(WorkingHours(day=day_text, is_day_off=True))
                continue
            # Times are formatted as "09.00 - 18.00" (dots), normalize to colons
            time_match = re.match(r"(\d{2}[.:]\d{2})\s*[-–]\s*(\d{2}[.:]\d{2})", time_text)
            if time_match:
                open_t = time_match.group(1).replace(".", ":")
                close_t = time_match.group(2).replace(".", ":")
                wh = WorkingHours(day=day_text, open_time=open_t, close_time=close_t)
                if len(cols) >= 3:
                    lunch_text = cols[2].get_text(strip=True)
                    lunch_match = re.match(
                        r"(\d{2}[.:]\d{2})\s*[-–]\s*(\d{2}[.:]\d{2})", lunch_text
                    )
                    if lunch_match:
                        wh.lunch_start = lunch_match.group(1).replace(".", ":")
                        wh.lunch_end = lunch_match.group(2).replace(".", ":")
                hours.append(wh)
        return hours

    # Fallback: table-based layout (alternative markup)
    for row in soup.find_all("tr"):
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
        time_match = re.match(r"(\d{2}[.:]\d{2})\s*[-–]\s*(\d{2}[.:]\d{2})", time_text)
        if time_match:
            open_t = time_match.group(1).replace(".", ":")
            close_t = time_match.group(2).replace(".", ":")
            wh = WorkingHours(day=day_text, open_time=open_t, close_time=close_t)
            lunch_match = re.search(
                r"обед[:\s]*(\d{2}[.:]\d{2})\s*[-–]\s*(\d{2}[.:]\d{2})", time_text, re.I
            )
            if lunch_match:
                wh.lunch_start = lunch_match.group(1).replace(".", ":")
                wh.lunch_end = lunch_match.group(2).replace(".", ":")
            hours.append(wh)
    return hours


def _parse_external_links(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    # Company website links have title="Перейти на сайт"; the URL is in the link text.
    # Telegram links have title="Telegram" with an SVG icon and no readable text.
    # Other /go/ links (site nav, social icons) have no title — skip them.
    website: Optional[str] = None
    telegram: Optional[str] = None
    for tag in soup.find_all("a", href=re.compile(r"/go/\?u=")):
        title = (tag.get("title") or "").strip()
        text = tag.get_text(strip=True)
        href = str(tag.get("href", ""))

        if title == "Telegram":
            if telegram is None:
                if text:
                    telegram = text if text.startswith("http") else f"https://{text}"
                else:
                    # SVG-only icon — store the goldenpages redirect as fallback
                    telegram = BASE_URL + href
        elif title == "Перейти на сайт":
            if text and website is None:
                website = text if text.startswith("http") else f"https://{text}"
    return website, telegram
