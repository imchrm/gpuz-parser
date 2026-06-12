# TODO.md — goldenpages-scraper

## Статус: Фазы 0–5 завершены. Фаза 6 в процессе.

---

## Фаза 0 — Разведка и разблокировка ✅

- [x] **0.1** Проверить `robots.txt`.
      `/rubrics/`, `/company/`, `/city/` — разрешены.
      `/search/*` — заблокирован (`Disallow: */search/*`).
      Пагинация: `Clean-param: city&region&Page */rubrics/*` подтверждает параметр `Page`.

- [x] **0.2** [CRITICAL] Установить механизм пагинации рубрик.
      Серверная пагинация, GET-параметр `Page` (с заглавной буквы):
      `/rubrics/?Id=3473&Page=2`. Путь B (requests + BeautifulSoup) — достаточен.

- [x] **0.3** [CRITICAL] Исследовать кнопку "Скачать список".
      Требует авторизации. Путь A (excel_downloader) — отклонён.

- [x] **0.4** Установить параметры формы поиска.
      `/search/*` заблокирован в robots.txt. `keyword_collector` реализован,
      но **не должен использоваться** — нарушает robots.txt.

- [x] **0.5** Проверить получение телефонов.
      Открытый AJAX-эндпоинт: `GET /scripts/company_data/?cid={id}&ctype=phone&clang=ru`.
      Ответ — HTML с `<a href="tel:+998...">`. Номер берётся из `href`.
      FAQ-блок на странице содержит телефоны в schema.org JSON, но AJAX-путь надёжнее.

- [x] **0.6** Исследовать ссылки через `/go/?u=HASH`.
      Фактический URL находится в **тексте** ссылки (не в `title` и не в `href`).
      Тип ссылки определяется по `title`: `"Перейти на сайт"` = сайт,
      `"Telegram"` = Telegram (текст пустой — сохраняется редирект-URL).
      Ссылки без `title` — навигация сайта, игнорируются.

- [x] **0.7** Собрать таблицу ID городов и регионов.
      13 областей + 300+ городов в `src/config.py` (`REGION_IDS`, `CITY_IDS`, `ALL_LOCATIONS`).

---

## Фаза 1 — Структура проекта ✅

- [x] **1.1** Структура директорий создана.
- [x] **1.2** `pyproject.toml` с зависимостями (requests, bs4, lxml, pydantic, openpyxl, tenacity, rich).
- [x] **1.3** `src/models.py` — `WorkingHours`, `Company`, `SearchParams`, `ScraperResult`.
- [x] **1.4** `src/config.py` — константы, `BASE_URL`, задержки, все ID городов/регионов.

---

## Фаза 2 — HTTP-клиент и парсеры ✅

- [x] **2.1** `src/http_client.py`:
      `create_session()`, `fetch_page()` с tenacity-retry, `fetch_phones()`.

- [x] **2.2** `src/parsers/company_parser.py`:
      `parse_company_page()`, `parse_phones()`. Все поля модели Company.
      Исправлены 6 расхождений с реальным HTML (рабочие часы, рейтинг,
      отзывы, лет на сайте, рубрики, Telegram/сайт).

- [x] **2.3** `src/parsers/listing_parser.py`:
      `parse_company_ids()`, `get_total_count()`, `get_next_page_url()`.
      Исправлено: обход предков DOM в `get_total_count`.

---

## Фаза 3 — Альтернативный путь: Excel-экспорт

**Путь 3A (excel_downloader) — не реализован.** "Скачать список" требует авторизации.

---

## Фаза 3B — Сборщики через HTML-парсинг ✅

- [x] **3B.1** `src/collectors/rubric_collector.py` — `collect_rubric()`.
- [x] **3B.2** `src/collectors/city_collector.py` — `collect_city()`.
- [x] **3B.3** `src/collectors/keyword_collector.py` — `collect_keyword()`.
      ⚠️ Реализован, но использовать нельзя: `/search/*` в Disallow.
- [x] **3B.4** `src/collectors/multi_rubric_collector.py` — `collect_rubrics()` с дедупликацией.

---

## Фаза 4 — Экспорт ✅

- [x] **4.1** `src/exporters/csv_exporter.py` — `utf-8-sig`, разделитель `;`, списки через ` | `.
- [x] **4.2** `src/exporters/excel_exporter.py` — openpyxl, лист `Companies`, заморозка, автоширина.

---

## Фаза 5 — CLI-интерфейс ✅

- [x] **5.1** `main.py` — `--rubric`, `--city`, `--keyword`, `--output`, `--format`, `--limit`,
      `--delay-min`, `--delay-max`. Rich-вывод с fallback на print.

---

## Фаза 6 — Тестирование

- [x] **6.1** Fixture HTML сохранён: `tests/fixtures/veolia_energy_12988.htm`
      (реальная страница "VEOLIA ENERGY TASHKENT", id=12988).

- [x] **6.2** `tests/test_company_parser.py` — 35 тестов:
      синтетический FULL_COMPANY_HTML + 14 интеграционных на реальном fixture.
      Покрыты все поля Company, рабочие часы, телефоны, внешние ссылки.

- [x] **6.3** `tests/test_listing_parser.py` — 19 тестов:
      parse_company_ids (порядок, дедупликация, фильтрация), get_total_count
      (вложенный DOM, пробелы), get_next_page_url (primary + fallback пути).

- [ ] **6.4** Тестовый прогон на реальном сайте: `python main.py --rubric 3473 --limit 5`.
      Проверить CSV/Excel: корректность полей, кодировка, отсутствие артефактов.

**Итого: 69/69 тестов проходят.**

---

## Риски и открытые вопросы

| ID   | Вопрос / риск                                                            | Приоритет | Статус        |
|------|--------------------------------------------------------------------------|-----------|---------------|
| R-01 | Пагинация рубрик — механизм                                              | CRITICAL  | ✅ Серверная, `Page` |
| R-02 | "Скачать список" — доступность без авторизации                           | HIGH      | ✅ Требует авт. — отклонён |
| R-03 | Телефоны — стабильность механизма получения                              | HIGH      | ✅ AJAX-эндпоинт открыт |
| R-04 | robots.txt не прочитан                                                   | HIGH      | ✅ Проверен |
| R-05 | Параметры POST-формы поиска                                              | MEDIUM    | ⛔ /search/* заблокирован |
| R-06 | URL сайтов компаний скрыты за /go/?u=HASH                               | MEDIUM    | ✅ URL в тексте ссылки |
| R-07 | ID городов и регионов не собраны                                         | MEDIUM    | ✅ 300+ в config.py |
| R-08 | Если пагинация через JS — стек меняется на Playwright                    | HIGH      | ✅ Не нужен (серверная) |
