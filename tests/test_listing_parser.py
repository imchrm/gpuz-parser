from __future__ import annotations

from src.parsers.listing_parser import get_next_page_url, get_total_count, parse_company_ids


def test_parse_company_ids_basic() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=123">Company 1</a>
    <a href="/company/?Id=456">Company 2</a>
    <a href="/rubrics/?Id=3473">Rubric</a>
    </body></html>
    """
    ids = parse_company_ids(html)
    assert ids == [123, 456]


def test_parse_company_ids_deduplication() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=100">Company</a>
    <a href="/company/?Id=100">Company duplicate</a>
    <a href="/company/?Id=200">Company 2</a>
    </body></html>
    """
    ids = parse_company_ids(html)
    assert ids == [100, 200]


def test_parse_company_ids_empty() -> None:
    ids = parse_company_ids("<html><body></body></html>")
    assert ids == []


def test_get_total_count_found() -> None:
    html = "<html><body><p>Найдено организаций: 617</p></body></html>"
    count = get_total_count(html)
    assert count == 617


def test_get_total_count_not_found() -> None:
    count = get_total_count("<html><body></body></html>")
    assert count == 0


def test_get_total_count_zero() -> None:
    html = "<html><body><p>Найдено организаций: 0</p></body></html>"
    count = get_total_count(html)
    assert count == 0


def test_get_next_page_url_with_next_link() -> None:
    html = """
    <html><body>
    <div class="pagination">
        <a href="/rubrics/?Id=3473&page=1">1</a>
        <span class="active">2</span>
        <a href="/rubrics/?Id=3473&page=3">Следующая</a>
    </div>
    </body></html>
    """
    url = get_next_page_url(html, "https://www.goldenpages.uz")
    assert url == "https://www.goldenpages.uz/rubrics/?Id=3473&page=3"


def test_get_next_page_url_no_next() -> None:
    html = "<html><body><div>No pagination</div></body></html>"
    url = get_next_page_url(html, "https://www.goldenpages.uz")
    assert url is None
