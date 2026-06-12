from __future__ import annotations

from src.parsers.company_parser import parse_company_page, parse_phones


def test_parse_company_page_minimal() -> None:
    html = "<html><body><h1>Test Company (Ташкент)</h1></body></html>"
    company = parse_company_page(html, 12345)
    assert company.company_id == 12345
    assert company.name == "Test Company"
    assert company.url == "https://www.goldenpages.uz/company/?Id=12345"


def test_parse_company_page_no_city_in_name() -> None:
    html = "<html><body><h1>Simple Name</h1></body></html>"
    company = parse_company_page(html, 99)
    assert company.name == "Simple Name"


def test_parse_company_page_empty_html() -> None:
    company = parse_company_page("", 1)
    assert company.company_id == 1
    assert company.name is None
    assert company.phones == []


def test_parse_phones_ajax_response() -> None:
    html = (
        '<ul class="gp_phoneCom someclass">'
        '<li><a href="tel:+998712270834">+998 71 227-08-34</a></li>'
        '<li><a href="tel:+998712000056">+998 71 200-00-56</a></li>'
        '<li><a href="tel:1347">1347</a></li>'
        "</ul>"
    )
    phones = parse_phones(html)
    assert phones == ["+998712270834", "+998712000056", "1347"]


def test_parse_phones_empty() -> None:
    phones = parse_phones("")
    assert phones == []


def test_parse_phones_no_tel_links() -> None:
    html = "<div><a href='/company/?Id=1'>Link</a></div>"
    phones = parse_phones(html)
    assert phones == []
