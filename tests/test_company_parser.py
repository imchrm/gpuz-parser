from __future__ import annotations

import pytest

from src.parsers.company_parser import parse_company_page, parse_phones

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_COMPANY_HTML = """
<html><body>
  <h1>ООО «ТеплоЭнерго» (Ташкент)</h1>
  <div>Теплоэнерго; Teploenergy</div>

  <a href="/city/?Id=296">Ташкент</a>
  <a href="/region/?Id=328">Ташкентская область</a>
  <a href="/district/?Id=14">Юнусабадский район</a>
  <a href="/orgbyindex/?Id=100210">100210</a>
  <a href="/street/?Id=5823">ул. Амира Темура</a>, 15а

  <div>Ориентиры: рядом с ЦУМом; напротив кинотеатра Навруз</div>

  <a href="/rubrics/?Id=3473">Теплоснабжение</a>
  <a href="/rubrics/?Id=3778">Коммунальные услуги</a>

  <div>ИНН: 123456789</div>
  <div>7 лет на сайте</div>
  <div>Обновлено: 12.06.2026</div>

  <span class="rating">4.7</span>
  <div>15 отзывов</div>

  <table>
    <tr><td>Пн-Пт</td><td>09:00 - 18:00</td></tr>
    <tr><td>Сб</td><td>09:00 - 15:00 обед: 12:00 - 13:00</td></tr>
    <tr><td>Вс</td><td>Выходной</td></tr>
  </table>

  <a href="/go/?u=abc123" rel="nofollow noopener" target="_blank">www.teploenergo.uz</a>
  <a href="/go/?u=def456" rel="nofollow noopener" target="_blank">t.me/teploenergo</a>
</body></html>
"""


# ---------------------------------------------------------------------------
# Full company page — happy path
# ---------------------------------------------------------------------------

def test_parse_full_company_name() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.name == "ООО «ТеплоЭнерго»"


def test_parse_full_company_id_and_url() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.company_id == 57473
    assert company.url == "https://www.goldenpages.uz/company/?Id=57473"


def test_parse_full_company_alt_names() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.alt_names == ["Теплоэнерго", "Teploenergy"]


def test_parse_full_company_location() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.city == "Ташкент"
    assert company.region == "Ташкентская область"
    assert company.district == "Юнусабадский район"
    assert company.postal_code == "100210"
    assert company.street == "ул. Амира Темура"


def test_parse_full_company_building() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.building == "15а"


def test_parse_full_company_landmarks() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.landmarks == ["рядом с ЦУМом", "напротив кинотеатра Навруз"]


def test_parse_full_company_rubrics() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.activity_types == ["Теплоснабжение", "Коммунальные услуги"]
    assert company.rubric_ids == [3473, 3778]


def test_parse_full_company_inn() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.inn == "123456789"


def test_parse_full_company_years_on_site() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.years_on_site == 7


def test_parse_full_company_last_updated() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.last_updated == "12.06.2026"


def test_parse_full_company_rating() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.rating == 4.7


def test_parse_full_company_review_count() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.review_count == 15


def test_parse_full_company_website() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.website == "https://www.teploenergo.uz"


def test_parse_full_company_telegram() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert company.telegram == "https://t.me/teploenergo"


# ---------------------------------------------------------------------------
# Working hours
# ---------------------------------------------------------------------------

def test_parse_working_hours_count() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    assert len(company.working_hours) == 3


def test_parse_working_hours_regular_day() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    mon = company.working_hours[0]
    assert mon.day == "Пн-Пт"
    assert mon.open_time == "09:00"
    assert mon.close_time == "18:00"
    assert mon.is_day_off is False


def test_parse_working_hours_with_lunch() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    sat = company.working_hours[1]
    assert sat.day == "Сб"
    assert sat.open_time == "09:00"
    assert sat.close_time == "15:00"
    assert sat.lunch_start == "12:00"
    assert sat.lunch_end == "13:00"


def test_parse_working_hours_day_off() -> None:
    company = parse_company_page(FULL_COMPANY_HTML, 57473)
    sun = company.working_hours[2]
    assert sun.day == "Вс"
    assert sun.is_day_off is True
    assert sun.open_time is None
    assert sun.close_time is None


# ---------------------------------------------------------------------------
# Edge cases — name stripping
# ---------------------------------------------------------------------------

def test_parse_name_strips_city_suffix() -> None:
    html = "<html><body><h1>Рестик (Самарканд)</h1></body></html>"
    assert parse_company_page(html, 1).name == "Рестик"


def test_parse_name_no_city_suffix() -> None:
    html = "<html><body><h1>Simple Name</h1></body></html>"
    assert parse_company_page(html, 2).name == "Simple Name"


def test_parse_name_missing_h1() -> None:
    html = "<html><body><p>No heading</p></body></html>"
    assert parse_company_page(html, 3).name is None


# ---------------------------------------------------------------------------
# Edge cases — empty / missing fields
# ---------------------------------------------------------------------------

def test_parse_empty_html_returns_defaults() -> None:
    company = parse_company_page("", 1)
    assert company.company_id == 1
    assert company.name is None
    assert company.phones == []
    assert company.alt_names == []
    assert company.activity_types == []
    assert company.rubric_ids == []
    assert company.landmarks == []
    assert company.working_hours == []
    assert company.website is None
    assert company.telegram is None
    assert company.inn is None
    assert company.rating is None
    assert company.review_count is None
    assert company.years_on_site is None
    assert company.last_updated is None


def test_parse_inn_not_present() -> None:
    html = "<html><body><h1>Компания</h1></body></html>"
    assert parse_company_page(html, 5).inn is None


def test_parse_landmarks_single() -> None:
    html = "<html><body><span>Ориентиры: у входа в метро</span></body></html>"
    company = parse_company_page(html, 6)
    assert company.landmarks == ["у входа в метро"]


def test_parse_landmarks_multiple_semicolons() -> None:
    html = "<html><body><span>Ориентиры: ориентир А; ориентир Б; ориентир В</span></body></html>"
    company = parse_company_page(html, 7)
    assert company.landmarks == ["ориентир А", "ориентир Б", "ориентир В"]


def test_parse_rating_with_comma() -> None:
    html = '<html><body><span class="rating">4,5</span></body></html>'
    assert parse_company_page(html, 8).rating == 4.5


def test_parse_website_already_has_scheme() -> None:
    html = '<html><body><a href="/go/?u=x">https://example.com/path</a></body></html>'
    assert parse_company_page(html, 9).website == "https://example.com/path"


def test_parse_only_telegram_no_website() -> None:
    html = '<html><body><a href="/go/?u=x">t.me/channel</a></body></html>'
    company = parse_company_page(html, 10)
    assert company.telegram == "https://t.me/channel"
    assert company.website is None


def test_parse_alt_names_no_sibling() -> None:
    html = "<html><body><h1>Компания</h1></body></html>"
    assert parse_company_page(html, 11).alt_names == []


def test_parse_building_no_street() -> None:
    html = "<html><body><a href='/city/?Id=296'>Ташкент</a></body></html>"
    assert parse_company_page(html, 12).building is None


def test_parse_years_on_site_various_forms() -> None:
    html = "<html><body><span>3 лет на сайте</span></body></html>"
    assert parse_company_page(html, 13).years_on_site == 3


# ---------------------------------------------------------------------------
# parse_phones
# ---------------------------------------------------------------------------

def test_parse_phones_ajax_response() -> None:
    html = (
        '<ul class="gp_phoneCom">'
        '<li><a href="tel:+998712270834">+998 71 227-08-34</a></li>'
        '<li><a href="tel:+998712000056">+998 71 200-00-56</a></li>'
        '<li><a href="tel:1347">1347</a></li>'
        "</ul>"
    )
    phones = parse_phones(html)
    assert phones == ["+998712270834", "+998712000056", "1347"]


def test_parse_phones_multiple_numbers() -> None:
    html = (
        '<ul>'
        '<li><a href="tel:+998901234567">...</a></li>'
        '<li><a href="tel:+998997654321">...</a></li>'
        '</ul>'
    )
    assert parse_phones(html) == ["+998901234567", "+998997654321"]


def test_parse_phones_skips_empty_href() -> None:
    html = '<a href="tel:">No number</a><a href="tel:+998901234567">OK</a>'
    assert parse_phones(html) == ["+998901234567"]


def test_parse_phones_empty() -> None:
    assert parse_phones("") == []


def test_parse_phones_no_tel_links() -> None:
    html = "<div><a href='/company/?Id=1'>Link</a></div>"
    assert parse_phones(html) == []
