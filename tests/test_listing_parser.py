from __future__ import annotations

from src.parsers.listing_parser import get_next_page_url, get_total_count, parse_company_ids

BASE = "https://www.goldenpages.uz"

# ---------------------------------------------------------------------------
# parse_company_ids
# ---------------------------------------------------------------------------

def test_parse_company_ids_basic() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=123">Company 1</a>
    <a href="/company/?Id=456">Company 2</a>
    <a href="/rubrics/?Id=3473">Rubric</a>
    </body></html>
    """
    assert parse_company_ids(html) == [123, 456]


def test_parse_company_ids_deduplication() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=100">Company</a>
    <a href="/company/?Id=100">Company duplicate</a>
    <a href="/company/?Id=200">Company 2</a>
    </body></html>
    """
    assert parse_company_ids(html) == [100, 200]


def test_parse_company_ids_preserves_order() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=300">C3</a>
    <a href="/company/?Id=100">C1</a>
    <a href="/company/?Id=200">C2</a>
    </body></html>
    """
    assert parse_company_ids(html) == [300, 100, 200]


def test_parse_company_ids_empty_page() -> None:
    assert parse_company_ids("<html><body></body></html>") == []


def test_parse_company_ids_ignores_non_company_links() -> None:
    html = """
    <html><body>
    <a href="/rubrics/?Id=3473">Rubric</a>
    <a href="/city/?Id=296">City</a>
    <a href="/region/?Id=328">Region</a>
    </body></html>
    """
    assert parse_company_ids(html) == []


def test_parse_company_ids_skips_invalid_id() -> None:
    html = """
    <html><body>
    <a href="/company/?Id=abc">Bad</a>
    <a href="/company/?Id=42">Good</a>
    </body></html>
    """
    assert parse_company_ids(html) == [42]


def test_parse_company_ids_realistic_listing() -> None:
    html = """
    <html><body>
    <div class="company-list">
      <div class="company-card">
        <a href="/company/?Id=57473">ООО «ТеплоЭнерго»</a>
        <a href="/rubrics/?Id=3473">Теплоснабжение</a>
      </div>
      <div class="company-card">
        <a href="/company/?Id=12988">Узбекгаз</a>
        <a href="/rubrics/?Id=3473">Теплоснабжение</a>
      </div>
    </div>
    </body></html>
    """
    assert parse_company_ids(html) == [57473, 12988]


# ---------------------------------------------------------------------------
# get_total_count
# ---------------------------------------------------------------------------

def test_get_total_count_found() -> None:
    html = "<html><body><p>Найдено организаций: 617</p></body></html>"
    assert get_total_count(html) == 617


def test_get_total_count_zero() -> None:
    html = "<html><body><p>Найдено организаций: 0</p></body></html>"
    assert get_total_count(html) == 0


def test_get_total_count_not_found() -> None:
    assert get_total_count("<html><body></body></html>") == 0


def test_get_total_count_large_number() -> None:
    html = "<html><body><span>Найдено организаций: 12345</span></body></html>"
    assert get_total_count(html) == 12345


def test_get_total_count_in_parent_text() -> None:
    # Count is split across nested tags — parent.get_text() merges them
    html = """
    <html><body>
    <div><span>Найдено организаций:</span> <b>83</b></div>
    </body></html>
    """
    assert get_total_count(html) == 83


def test_get_total_count_with_spaces() -> None:
    html = "<html><body><p>Найдено организаций:   42</p></body></html>"
    assert get_total_count(html) == 42


# ---------------------------------------------------------------------------
# get_next_page_url
# ---------------------------------------------------------------------------

def test_get_next_page_url_next_link_present() -> None:
    html = """
    <html><body>
    <div class="pagination">
        <a href="/rubrics/?Id=3473&Page=1">1</a>
        <span class="active">2</span>
        <a href="/rubrics/?Id=3473&Page=3">Следующая</a>
    </div>
    </body></html>
    """
    url = get_next_page_url(html, BASE)
    assert url == f"{BASE}/rubrics/?Id=3473&Page=3"


def test_get_next_page_url_следующая_case_insensitive() -> None:
    html = """
    <html><body>
    <a href="/rubrics/?Id=100&Page=5">следующая</a>
    </body></html>
    """
    url = get_next_page_url(html, BASE)
    assert url == f"{BASE}/rubrics/?Id=100&Page=5"


def test_get_next_page_url_no_pagination() -> None:
    html = "<html><body><div>No pagination here</div></body></html>"
    assert get_next_page_url(html, BASE) is None


def test_get_next_page_url_last_page_no_next() -> None:
    html = """
    <html><body>
    <div class="pagination">
        <a href="/rubrics/?Id=3473&Page=1">1</a>
        <a href="/rubrics/?Id=3473&Page=2">2</a>
        <span class="active">3</span>
    </div>
    </body></html>
    """
    assert get_next_page_url(html, BASE) is None


def test_get_next_page_url_active_sibling_fallback() -> None:
    # No "Следующая" link — falls back to active page's next sibling
    html = """
    <html><body>
    <div class="pagination">
        <a href="/rubrics/?Id=3473&Page=1">1</a>
        <a class="active" href="/rubrics/?Id=3473&Page=2">2</a>
        <a href="/rubrics/?Id=3473&Page=3">3</a>
    </div>
    </body></html>
    """
    url = get_next_page_url(html, BASE)
    assert url == f"{BASE}/rubrics/?Id=3473&Page=3"


def test_get_next_page_url_absolute_href() -> None:
    html = """
    <html><body>
    <a href="https://www.goldenpages.uz/rubrics/?Id=99&Page=2">Следующая</a>
    </body></html>
    """
    url = get_next_page_url(html, BASE)
    assert url == "https://www.goldenpages.uz/rubrics/?Id=99&Page=2"
