import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from src.config import BASE_URL
from src.models import Company, WorkingHours


def parse_company_page(html: str, company_id: int) -> Company:
    soup = BeautifulSoup(html, "lxml")

    name = _parse_name(soup)
    alt_names = _parse_alt_names(soup)
    city = _parse_link_text(soup, "/city/?Id=")
    region = _parse_link_text(soup, "/region/?Id=")
    district = _parse_link_text(soup, "/district/?Id=")
    street, building = _parse_street_and_building(soup)
    postal_code = _parse_link_text(soup, "/orgbyindex/?Id=")
    landmarks = _parse_landmarks(soup)
    activity_types, rubric_ids = _parse_rubrics(soup)
    inn = _parse_inn(soup)
    years_on_site = _parse_years_on_site(soup)
    last_updated = _parse_last_updated(soup)
    rating = _parse_rating(soup)
    review_count = _parse_review_count(soup)
    working_hours = _parse_working_hours(soup)
    website, telegram = _parse_external_links(soup)

    return Company(
        company_id=company_id,
        url=f"{BASE_URL}/company/?Id={company_id}",
        name=name,
        alt_names=alt_names,
        city=city,
        region=region,
        district=district,
        street=street,
        building=building,
        postal_code=postal_code,
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
    # Remove trailing city name in parentheses, e.g. "Company Name (Tashkent)"
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
    return [part.strip() for part in text.split(";") if part.strip()]


def _parse_link_text(soup: BeautifulSoup, path: str) -> Optional[str]:
    tag = soup.find("a", href=re.compile(re.escape(path)))
    if not tag:
        return None
    return tag.get_text(strip=True) or None


def _parse_street_and_building(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    street_tag = soup.find("a", href=re.compile(re.escape("/street/?Id=")))
    if not street_tag:
        return None, None
    street = street_tag.get_text(strip=True) or None

    # Building number is the next text node after the street link
    building: Optional[str] = None
    next_node = street_tag.next_sibling
    if next_node and isinstance(next_node, str):
        building_text = next_node.strip().lstrip(",").strip()
        building = building_text or None

    return street, building


def _parse_landmarks(soup: BeautifulSoup) -> list[str]:
    label = soup.find(string=re.compile(r"Ориентиры:"))
    if not label:
        return []
    parent = label.parent
    if not parent:
        return []
    text = parent.get_text(strip=True)
    text = re.sub(r"^Ориентиры:\s*", "", text)
    return [part.strip() for part in text.split(";") if part.strip()]


def _parse_rubrics(soup: BeautifulSoup) -> tuple[list[str], list[int]]:
    activity_types: list[str] = []
    rubric_ids: list[int] = []
    for tag in soup.find_all("a", href=re.compile(r"/rubrics/\?Id=")):
        href = tag.get("href", "")
        match = re.search(r"Id=(\d+)", href)
        if match:
            rubric_ids.append(int(match.group(1)))
            activity_types.append(tag.get_text(strip=True))
    return activity_types, rubric_ids


def _parse_inn(soup: BeautifulSoup) -> Optional[str]:
    label = soup.find(string=re.compile(r"ИНН:"))
    if not label:
        return None
    parent = label.parent
    if not parent:
        return None
    text = parent.get_text(strip=True)
    match = re.search(r"ИНН:\s*(\S+)", text)
    return match.group(1) if match else None


def _parse_years_on_site(soup: BeautifulSoup) -> Optional[int]:
    match_tag = soup.find(string=re.compile(r"\d+\s+лет на сайте"))
    if not match_tag:
        return None
    match = re.search(r"(\d+)\s+лет на сайте", str(match_tag))
    return int(match.group(1)) if match else None


def _parse_last_updated(soup: BeautifulSoup) -> Optional[str]:
    match_tag = soup.find(string=re.compile(r"Обновлено:"))
    if not match_tag:
        return None
    match = re.search(r"Обновлено:\s*(\d{2}\.\d{2}\.\d{4})", str(match_tag))
    return match.group(1) if match else None


def _parse_rating(soup: BeautifulSoup) -> Optional[float]:
    # Rating is typically in a span or div with a numeric value
    rating_tag = soup.find(class_=re.compile(r"rating|score", re.I))
    if not rating_tag:
        return None
    text = rating_tag.get_text(strip=True)
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None
    return None


def _parse_review_count(soup: BeautifulSoup) -> Optional[int]:
    review_tag = soup.find(string=re.compile(r"\d+\s+отзыв"))
    if not review_tag:
        return None
    match = re.search(r"(\d+)\s+отзыв", str(review_tag))
    return int(match.group(1)) if match else None


def _parse_working_hours(soup: BeautifulSoup) -> list[WorkingHours]:
    hours: list[WorkingHours] = []
    # Working hours are typically in a table with day rows
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        day_text = cells[0].get_text(strip=True)
        if not day_text:
            continue
        time_text = cells[1].get_text(strip=True)
        if re.search(r"выходной|closed", time_text, re.I):
            hours.append(WorkingHours(day=day_text, is_day_off=True))
            continue
        # Parse time ranges like "09:00-18:00" or "09:00-13:00 14:00-18:00"
        time_parts = time_text.split()
        open_time: Optional[str] = None
        close_time: Optional[str] = None
        lunch_start: Optional[str] = None
        lunch_end: Optional[str] = None
        ranges = [p for p in time_parts if re.match(r"\d{2}:\d{2}-\d{2}:\d{2}", p)]
        if len(ranges) >= 1:
            parts = ranges[0].split("-")
            open_time = parts[0]
            close_time = parts[1]
        if len(ranges) >= 2:
            # Second range is after lunch break — first range ends at lunch_start
            lunch_parts = ranges[1].split("-")
            lunch_start = close_time
            lunch_end = lunch_parts[0]
            close_time = lunch_parts[1]
        if open_time:
            hours.append(WorkingHours(
                day=day_text,
                open_time=open_time,
                close_time=close_time,
                lunch_start=lunch_start,
                lunch_end=lunch_end,
            ))
    return hours


def _parse_external_links(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    website: Optional[str] = None
    telegram: Optional[str] = None
    for tag in soup.find_all("a", href=re.compile(r"/go/\?u=")):
        href = tag.get("href", "")
        title = tag.get("title", "").lower()
        text = tag.get_text(strip=True).lower()
        if "t.me" in title or "telegram" in title or "t.me" in text or "telegram" in text:
            if telegram is None:
                telegram = href
        else:
            if website is None:
                website = href
    return website, telegram
