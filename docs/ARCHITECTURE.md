# ARCHITECTURE.md — goldenpages-scraper

## Обзор

Консольный Python-инструмент для сбора данных о компаниях с
https://www.goldenpages.uz. Запускается разово из командной строки,
принимает параметры поиска, собирает данные, экспортирует в CSV/Excel.

Архитектурный принцип: **однонаправленный поток данных**.

```
CLI -> Collector -> HTTP Client -> Parser -> Model -> Exporter -> File
```

Каждый слой зависит только от следующего. Парсеры не знают об HTTP.
Экспортеры не знают о парсерах. Модели не зависят ни от чего.

### Выбранный путь реализации

```
Фаза 0 завершена
    |
    +-- "Скачать список" требует авторизации
    |       -> Путь A: отклонён
    |
    +-- Пагинация серверная (параметр Page)  ← выбрано
    |       -> Путь B: requests + BeautifulSoup ✅
    |
    +-- Пагинация клиентская (JavaScript)
            -> Путь C: Playwright — не нужен
```

---

## Структура директорий

```
gpuz-parser/
|
|-- docs/
|   |-- CONTEXT.md
|   |-- TODO.md
|   |-- ARCHITECTURE.md
|
|-- src/
|   |-- __init__.py
|   |-- config.py             # константы, ID городов/регионов (300+), задержки
|   |-- models.py             # Pydantic v2 модели данных
|   |-- http_client.py        # HTTP-запросы, retry, сессия, rate limiting
|   |
|   |-- parsers/
|   |   |-- __init__.py
|   |   |-- company_parser.py     # парсинг страницы одной компании
|   |   |-- listing_parser.py     # парсинг страницы списка (рубрика/город)
|   |
|   |-- collectors/
|   |   |-- __init__.py
|   |   |-- rubric_collector.py       # сбор по рубрике (?Id=N)
|   |   |-- city_collector.py         # сбор по городу (?Id=N)
|   |   |-- keyword_collector.py      # ⚠️ не использовать — /search/* в Disallow
|   |   |-- multi_rubric_collector.py # несколько рубрик + дедупликация
|   |
|   |-- exporters/
|   |   |-- __init__.py
|   |   |-- csv_exporter.py
|   |   |-- excel_exporter.py
|
|-- tests/
|   |-- fixtures/
|   |   |-- veolia_energy_12988.htm   # реальный HTML компании (id=12988)
|   |
|   |-- test_company_parser.py        # 35 тестов (синтетика + реальный fixture)
|   |-- test_listing_parser.py        # 19 тестов
|
|-- output/                   # выходные файлы (в .gitignore)
|
|-- main.py                   # точка входа CLI
|-- pyproject.toml
|-- .gitignore
|-- CLAUDE.md
```

---

## Модели данных (`src/models.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class WorkingHours(BaseModel):
    day: str                         # "Пн", "Вт-Пт", ...
    open_time: Optional[str] = None  # "09:00" (нормализовано из "09.00")
    close_time: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    is_day_off: bool = False


class Company(BaseModel):
    company_id: int
    url: str

    name: Optional[str] = None
    alt_names: list[str] = Field(default_factory=list)

    phones: list[str] = Field(default_factory=list)
    website: Optional[str] = None      # URL из текста ссылки /go/?u=HASH
    telegram: Optional[str] = None     # редирект-URL если текст пустой

    postal_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    landmarks: list[str] = Field(default_factory=list)

    activity_types: list[str] = Field(default_factory=list)
    rubric_ids: list[int] = Field(default_factory=list)

    inn: Optional[str] = None          # частично маскируется сайтом
    years_on_site: Optional[int] = None
    last_updated: Optional[str] = None  # "дд.мм.гггг"
    rating: Optional[float] = None
    review_count: Optional[int] = None  # из "оценок: N"
    working_hours: list[WorkingHours] = Field(default_factory=list)

    source_rubric_id: Optional[int] = None


class SearchParams(BaseModel):
    rubric_ids: list[int] = Field(default_factory=list)
    city_id: Optional[int] = None
    keyword: Optional[str] = None
    output_path: str = "output/result"
    output_format: str = "both"      # "csv" | "xlsx" | "both"
    delay_min: float = 1.5
    delay_max: float = 3.5
    limit: Optional[int] = None


class ScraperResult(BaseModel):
    total_found: int
    total_exported: int
    duplicates_removed: int
    errors: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
```

---

## Конфигурация (`src/config.py`)

```python
BASE_URL = "https://www.goldenpages.uz"
PHONE_API_URL = BASE_URL + "/scripts/company_data/"

REGION_IDS: dict[str, int] = {
    "tashkent_region": 328,
    "samarkand_region": 333,
    # ... 13 областей
}

CITY_IDS: dict[str, int] = {
    "tashkent": 296,
    "samarkand": 322,
    # ... ~50 основных городов
}

ALL_LOCATIONS: dict[int, tuple[str, int]] = {
    296: ("Ташкент", 328),
    # ... 300+ населённых пунктов
}

DEFAULT_DELAY_MIN: float = 1.5
DEFAULT_DELAY_MAX: float = 3.5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
```

---

## Слой HTTP (`src/http_client.py`)

- Одиночный `requests.Session` на весь запуск — сохраняет cookies/CSRF между запросами.
- Retry через `tenacity`: 3 попытки, `wait_exponential(multiplier=2, min=4, max=30)`.
- Случайная задержка: `time.sleep(random.uniform(delay_min, delay_max))`.
- Таймаут: `timeout=(10, 30)`.

```python
def create_session() -> requests.Session: ...

def fetch_page(
    session: requests.Session,
    url: str,
    delay_min: float = DEFAULT_DELAY_MIN,
    delay_max: float = DEFAULT_DELAY_MAX,
) -> str: ...

def fetch_phones(session: requests.Session, company_id: int) -> str:
    """GET /scripts/company_data/?cid={id}&ctype=phone&clang=ru"""
    ...
```

---

## Слой парсинга (`src/parsers/`)

### `company_parser.py`

```python
def parse_company_page(html: str, company_id: int) -> Company: ...
def parse_phones(html: str) -> list[str]: ...
```

**Телефоны** — AJAX-ответ содержит:
```html
<ul class="gp_phoneCom ...">
  <li><a href="tel:+998712270834">...</a></li>
</ul>
```
Номер берётся из атрибута `href` (после `tel:`).

**Рабочие часы** — НЕ таблица `<tr>/<td>`, а div-ы:
```html
<div class="gp_work_time">
  <div class="row gp_work_wrap fw-600"> <!-- заголовок, пропускать --> </div>
  <div class="row gp_work_wrap">
    <div>Пн:</div>              <!-- cols[0]: день -->
    <div>09.00 - 18.00</div>   <!-- cols[1]: время (dot-формат) -->
    <div>не указан</div>       <!-- cols[2]: обед -->
  </div>
  <div class="row gp_work_wrap gp_time_act">
    <div>Сегодня</div>         <!-- лишний первый col, пропускать -->
    <div>Пт:</div>
    ...
  </div>
  <div class="row gp_work_wrap">
    <div>Сб:</div>
    <div>выходной</div>
    <div>-</div>
  </div>
</div>
```
Время нормализуется: `09.00` → `09:00`.

**Внешние ссылки**:
```python
# title="Перейти на сайт" → сайт компании; URL в link.get_text()
# title="Telegram"        → Telegram; текст пустой, сохраняется /go/ редирект
# title=None              → навигация сайта, игнорировать
```

**Рейтинг**:
```html
<div class="review_all__count fw-600">2.33</div>
```

**Отзывы**:
```html
<span>оценок: 3 | отзывов: 2</span>
```
Поле `review_count` = значение `оценок:`.

**Рубрики** — только относительные URL:
```python
# Правильно: <a href="/rubrics/?Id=3093">
# Игнорировать: <a href="https://www.goldenpages.uz/rubrics/?Id=1441">
```

### `listing_parser.py`

```python
def parse_company_ids(html: str) -> list[int]:
    """Извлекает ID из ссылок /company/?Id=N. Дедуплицирует, сохраняет порядок."""
    ...

def get_total_count(html: str) -> int:
    """Парсит 'Найдено организаций: N'. Обходит DOM вверх если число в отдельном теге."""
    ...

def get_next_page_url(html: str, current_url: str) -> str | None:
    """
    Primary: ищет ссылку с текстом 'Следующ...'.
    Fallback: ищет активную страницу в пагинаторе, берёт следующий сиблинг.
    """
    ...
```

---

## Слой экспорта

### Порядок и названия колонок

| # | Поле модели          | Заголовок колонки       |
|---|----------------------|-------------------------|
| 1 | `name`               | Название                |
| 2 | `alt_names`          | Доп. названия           |
| 3 | `phones`             | Телефоны                |
| 4 | `website`            | Сайт                    |
| 5 | `telegram`           | Telegram                |
| 6 | `city`               | Город                   |
| 7 | `region`             | Регион                  |
| 8 | `district`           | Район                   |
| 9 | `street`             | Улица                   |
| 10 | `building`          | Дом/офис                |
| 11 | `postal_code`       | Индекс                  |
| 12 | `landmarks`         | Ориентиры               |
| 13 | `activity_types`    | Виды деятельности       |
| 14 | `inn`               | ИНН                     |
| 15 | `last_updated`      | Обновлено               |
| 16 | `url`               | URL                     |

Поля-списки (`phones`, `alt_names`, `landmarks`, `activity_types`)
объединяются через ` | ` в обоих форматах.

**CSV:** кодировка `utf-8-sig` (UTF-8 с BOM для Windows Excel), разделитель `;`.

**Excel:** `openpyxl`, лист `Companies`, жирные заголовки, заморозка первой
строки (`freeze_panes="A2"`), автоширина колонок (max 50).

---

## CLI (`main.py`)

```
python main.py --rubric 3473 --rubric 3778 --format both
python main.py --city 296 --format xlsx --output output/tashkent
python main.py --rubric 3473 --limit 10
```

| Аргумент      | Тип   | Описание                                         |
|---------------|-------|--------------------------------------------------|
| `--rubric`    | int   | ID рубрики. Повторяется для нескольких           |
| `--city`      | int   | ID города                                        |
| `--keyword`   | str   | ⚠️ Не использовать — `/search/*` в Disallow      |
| `--output`    | str   | Путь без расширения (default: `output/result`)   |
| `--format`    | str   | `csv`, `xlsx` или `both` (default: `both`)       |
| `--limit`     | int   | Максимум компаний (для тестирования)             |
| `--delay-min` | float | Мин. пауза в сек (default: 1.5)                  |
| `--delay-max` | float | Макс. пауза в сек (default: 3.5)                 |

---

## Обработка ошибок

- HTTP-ошибки логируются, не прерывают запуск.
- Компания с ошибкой парсинга пропускается, ID в `ScraperResult.errors`.
- По завершении выводится итоговая статистика (rich-таблица с fallback на print).
- Логирование через `logging` (уровень INFO по умолчанию).

---

## Зависимости

```toml
[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.32"
beautifulsoup4 = "^4.12"
lxml = "^5.2"
pydantic = "^2.7"
openpyxl = "^3.1"
tenacity = "^8.3"
rich = "^13.7"
```

---

## Что намеренно исключено из MVP

- Асинхронный HTTP (`httpx`) — не нужен, пагинация серверная.
- База данных — CSV/Excel покрывает требования.
- Регулярный запуск / планировщик.
- Резолвинг координат из карты.
- Полный текст отзывов (за "Показать ещё" — требует JS).
- excel_downloader (Путь A) — "Скачать список" требует авторизации.
- Playwright (Путь C) — пагинация серверная, не нужен.
