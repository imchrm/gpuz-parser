# CHANGELOG.md — goldenpages-scraper

Все значимые изменения в проекте. Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [Unreleased]

### Ожидается
- 6.4 — Тестовый прогон на реальном сайте: `python main.py --rubric 3473 --limit 5`

---

## [0.6.0] — 2026-06-12 — Документация актуализирована

### Изменено
- `CLAUDE.md` — удалён несуществующий `excel_downloader.py`, добавлены реальные HTML-особенности сайта, таблица статусов фаз 1–6
- `docs/TODO.md` — все задачи 0.0–6.3 отмечены выполненными; убраны открытые вопросы
- `docs/CONTEXT.md` — убраны "не установлено"/"требует проверки"; задокументированы реальные структуры HTML для рабочих часов, телефонов, ссылок и рейтинга
- `docs/ARCHITECTURE.md` — структура директорий, примеры кода и описания приведены в соответствие с реализацией

---

## [0.5.0] — 2026-06-12 — Реальный HTML-fixture и исправление 6 багов парсера

### Добавлено
- `tests/fixtures/veolia_energy_12988.htm` — реальная страница компании "VEOLIA ENERGY TASHKENT" (id=12988)
- 14 интеграционных тестов на реальном fixture: имя, альтернативные названия, адрес, рубрики, ИНН, рейтинг, рабочие часы, веб-сайт, Telegram

### Исправлено (баги, найденные через реальный HTML)
- **Рабочие часы** — парсер ожидал `<tr>/<td>`, реальный сайт использует `<div class="gp_work_wrap">`; время в формате `09.00` нормализуется к `09:00`; строка с классом `fw-600` — заголовок, пропускается; текущий день содержит лишний элемент `"Сегодня"`
- **Лет на сайте** — regex расширен: обрабатывает все формы (`лет`, `год`, `года`)
- **Рейтинг** — искал класс `rating|stars`, реальный класс `review_all__count`
- **Количество отзывов** — парсит паттерн `"оценок: N | отзывов: N"` вместо текста-заголовка "Отзывы" без числа
- **Рубрики** — regex заякорен на `^/rubrics/` чтобы исключить абсолютные URL навигационных рубрик
- **Внешние ссылки** — детектирование по `title="Перейти на сайт"` / `title="Telegram"` вместо текста; ссылки без `title` (навигация сайта) игнорируются; Telegram-ссылки с пустым текстом сохраняют `/go/`-редирект

### Изменено
- `tests/test_company_parser.py` — синтетический fixture обновлён под новую логику title-детектирования; добавлены тесты для `год`/`года`; итого 50 тестов вместо 35

---

## [0.4.0] — 2026-06-12 — Расширение тест-сюита и исправление listing_parser

### Добавлено
- `tests/test_company_parser.py` расширен с 6 до 35 тестов: все поля Company, рабочие часы (обычный день, с обедом, выходной), телефоны (edge cases), внешние ссылки, пустой HTML
- `tests/test_listing_parser.py` расширен с 8 до 19 тестов: порядок ID, фильтрация ненужных ссылок, невалидные ID, большие числа, вложенный DOM, последняя страница, fallback-пагинация, абсолютные href

### Исправлено
- `listing_parser.get_total_count` — обходит цепочку предков DOM вместо одного родителя; корректно работает когда число и текст `"Найдено организаций:"` разделены по разным тегам

---

## [0.3.0] — 2026-06-12 — Задача 0.6: резолвинг внешних ссылок

### Изменено
- `src/parsers/company_parser._parse_external_links` — URL компании берётся из текста ссылки (`link.get_text()`), не из href-редиректа; Telegram определяется по тексту (`t.me/`, `telegram`)

---

## [0.2.0] — 2026-06-12 — Фаза 0 завершена: robots.txt и ID городов

### Добавлено
- `src/config.py` — полная таблица 13 областей (`REGION_IDS`), ~50 городов (`CITY_IDS`), 300+ населённых пунктов (`ALL_LOCATIONS`)
- `CLAUDE.md` обновлён: результаты robots.txt, подтверждён параметр `Page` (заглавная)

### Изменено
- `src/collectors/keyword_collector.py` — добавлено предупреждение ⚠️: `/search/*` в Disallow robots.txt, коллектор не должен использоваться
- `src/parsers/listing_parser.py` — добавлена заметка о параметре `Page` с заглавной буквы

---

## [0.1.0] — 2026-06-12 — Реализация фаз 1–5 (полный scaffold)

### Добавлено
- `pyproject.toml` — зависимости: requests, beautifulsoup4, lxml, pydantic v2, openpyxl, tenacity, rich, pytest
- `src/models.py` — Pydantic v2 модели: `WorkingHours`, `Company`, `SearchParams`, `ScraperResult`
- `src/config.py` — `BASE_URL`, `PHONE_API_URL`, задержки, User-Agent
- `src/http_client.py` — `create_session()`, `fetch_page()` с tenacity-retry (3 попытки, exponential backoff), `fetch_phones()`
- `src/parsers/company_parser.py` — `parse_company_page()`, `parse_phones()`; все поля модели Company
- `src/parsers/listing_parser.py` — `parse_company_ids()`, `get_total_count()`, `get_next_page_url()`
- `src/collectors/rubric_collector.py` — `collect_rubric()` с пагинацией
- `src/collectors/city_collector.py` — `collect_city()`
- `src/collectors/keyword_collector.py` — `collect_keyword()` (не использовать — /search/* запрещён)
- `src/collectors/multi_rubric_collector.py` — `collect_rubrics()` с дедупликацией по `company_id`
- `src/exporters/csv_exporter.py` — utf-8-sig, разделитель `;`, списки через ` | `
- `src/exporters/excel_exporter.py` — openpyxl, 16 колонок, заморозка первой строки, автоширина
- `main.py` — CLI: `--rubric`, `--city`, `--keyword`, `--output`, `--format`, `--limit`, `--delay-min`, `--delay-max`
- `tests/test_company_parser.py` — 6 базовых тестов
- `tests/test_listing_parser.py` — 8 базовых тестов
- `.gitignore` — `output/`, `.claude/`, `__pycache__/`, `.venv/`, и др.

---

## [0.0.1] — 2026-06-12 — Инициализация проекта

### Добавлено
- `docs/CONTEXT.md` — описание целевого сайта, структуры URL, данных компании
- `docs/TODO.md` — план по фазам 0–6
- `docs/ARCHITECTURE.md` — однонаправленный поток данных, три возможных пути (A/B/C)
- `CLAUDE.md` — краткий справочник для разработки
