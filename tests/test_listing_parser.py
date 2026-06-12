from src.parsers.listing_parser import get_next_page_url, get_total_count, parse_company_ids

LISTING_HTML = """
<html><body>
<div class="found">Найдено организаций: 617</div>
<div class="companies">
  <a href="/company/?Id=111">Company 1</a>
  <a href="/company/?Id=222">Company 2</a>
  <a href="/company/?Id=111">Company 1 duplicate</a>
</div>
<div class="pagination">
  <span class="active">1</span>
  <a href="/rubrics/?Id=3473&amp;page=2">2</a>
  <a href="/rubrics/?Id=3473&amp;page=2">Следующая</a>
</div>
</body></html>
"""

NO_NEXT_HTML = """
<html><body>
<div class="pagination">
  <a href="/rubrics/?Id=3473&amp;page=1">1</a>
  <span class="active">2</span>
</div>
</body></html>
"""


def test_parse_company_ids_deduplicates() -> None:
    ids = parse_company_ids(LISTING_HTML)
    assert ids == [111, 222]


def test_get_total_count() -> None:
    assert get_total_count(LISTING_HTML) == 617


def test_get_total_count_missing() -> None:
    assert get_total_count("<html></html>") == 0


def test_get_next_page_url_finds_next_link() -> None:
    url = get_next_page_url(LISTING_HTML, "https://www.goldenpages.uz")
    assert url is not None
    assert "page=2" in url


def test_get_next_page_url_last_page_returns_none() -> None:
    url = get_next_page_url(NO_NEXT_HTML, "https://www.goldenpages.uz")
    assert url is None
