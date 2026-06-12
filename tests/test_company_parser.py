from src.parsers.company_parser import parse_company_page, parse_phones

PHONES_HTML = """
<ul class="gp_phoneCom list-unstyled mb-0">
    <li><a href="tel:+998712270834" class="d-flex flex-column" title="">+998 (71) 227-08-34</a></li>
    <li><a href="tel:+998712000056" class="d-flex flex-column" title="">+998 (71) 200-00-56</a></li>
    <li><a href="tel:1347" class="d-flex flex-column" title="Колл-центр">1347 - Колл-центр</a></li>
</ul>
"""

MINIMAL_HTML = """
<html><body>
<h1>ООО Рога и Копыта (Ташкент)</h1>
</body></html>
"""


def test_parse_phones_extracts_all_numbers() -> None:
    phones = parse_phones(PHONES_HTML)
    assert phones == ["+998712270834", "+998712000056", "1347"]


def test_parse_phones_empty_html() -> None:
    assert parse_phones("") == []


def test_parse_phones_no_tel_links() -> None:
    assert parse_phones("<p>no phones here</p>") == []


def test_parse_company_name_strips_city() -> None:
    company = parse_company_page(MINIMAL_HTML, 99)
    assert company.name == "ООО Рога и Копыта"
    assert company.company_id == 99


def test_parse_company_missing_fields_return_none() -> None:
    company = parse_company_page(MINIMAL_HTML, 1)
    assert company.city is None
    assert company.phones == []
    assert company.website is None
