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

### Условное ветвление по итогам разведки (Фаза 0)

```
Фаза 0 завершена
    |
    +-- "Скачать список" работает без авторизации
    |       -> Путь A: ExcelDownloader (быстрый, минимум запросов)
    |
    +-- Пагинация серверная (GET-параметр)
    |       -> Путь B: requests + BeautifulSoup (стандартный)
    |
    +-- Пагинация клиентская (JavaScript)
            -> Путь C: Playwright (headless-браузер)
```

Документ описывает Путь B как базовый. Отклонения для A и C — отдельные
секции ниже.

---

## Структура директорий

```
goldenpages-scraper/
|
|-- docs/
|   |-- CONTEXT.md
|   |-- TODO.md
|   |-- ARCHITECTURE.md
|
|-- src/
|   |-- __init__.py
|   |-- config.py             # константы, ID городов/регионов, задержки
|   |-- models.py             # Pydantic-модели данных
|   |-- http_client.py        # HTTP-запросы, retry, сессия, rate limiting
|   |
|   |-- parsers/
|   |   |-- __init__.py
|   |   |-- company_parser.py     # парсинг страницы одной компании
|   |   |-- listing_parser.py     # парсинг страницы списка (рубрика/поиск)
|   |
|   |-- collectors/
|   |   |-- __init__.py
|   |   |-- rubric_collector.py       # сбор по рубрике (?Id=N)
|   |   |-- city_collector.py         # сбор по городу (?Id=N)
|   |   |-- keyword_collector.py      # сбор по ключевому слову (POST /search/)
|   |   |-- multi_rubric_collector.py # несколько рубрик + дедупликация
|   |   |-- excel_downloader.py       # Путь A: скачивание Excel с сайта
|   |
|   |-- exporters/
|   |   |-- __init__.py
|   |   |-- csv_exporter.py
|   |   |-- excel_exporter.py
|
|-- tests/
|   |-- fixtures/
|   |   |-- company_large.html        # HTML крупной компании с телефонами
|   |   |-- company_small.html        # HTML малой компании
|   |   |-- company_no_phone.html     # HTML компании без телефона
|   |   |-- rubric_page.html          # HTML страницы рубрики
|   |
|   |-- test_company_parser.py
|   |-- test_listing_parser.py
|
|-- output/                   # выходные файлы (в .gitignore)
|
|-- main.py                   # точка входа CLI
|-- pyproject.toml
|-- .gitignore
|-- README.md
```

---

## Модели данных (`src/models.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class WorkingHours(BaseModel):
    day: str                        # "Пн", "Вт", ...
    open_time: Optional[str] = None # "09.00"
    close_time: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    is_day_off: bool = False


class Company(BaseModel):
    # Идентификация
    company_id: int                    # числовой ID из URL /?Id=N
    url: str                           # полный URL страницы

    # Названия
    name: Optional[str] = None         # основное название из <h1>
    alt_names: list[str] = Field(default_factory=list)  # альтернативные

    # Контакты
    phones: list[str] = Field(default_factory=list)  # все телефоны из FAQ
    website: Optional[str] = None      # после резолвинга /go/?u=HASH
    telegram: Optional[str] = None

    # Адрес
    postal_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None    # район (для Ташкента)
    street: Optional[str] = None
    building: Optional[str] = None
    landmarks: list[str] = Field(default_factory=list)  # ориентиры

    # Категоризация
    activity_types: list[str] = Field(default_factory=list)  # виды деятельности
    rubric_ids: list[int] = Field(default_factory=list)       # ID рубрик

    # Метаданные
    inn: Optional[str] = None          # ИНН (частично скрыт на сайте)
    years_on_site: Optional[int] = None
    last_updated: Optional[str] = None  # "дд.мм.гггг"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    working_hours: list[WorkingHours] = Field(default_factory=list)

    # Служебные поля
    source_rubric_id: Optional[int] = None   # через какую рубрику найдена


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

# Известные ID городов (дополнить по итогам задачи 0.7)
CITY_IDS: dict[str, int] = {
    "tashkent": 296,
    "samarkand": 322,
    # ...
}

# Известные ID регионов (дополнить по итогам задачи 0.7)
REGION_IDS: dict[str, int] = {
    "tashkent_region": ...,
    "samarkand_region": 333,
    # ...
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

**Ключевые требования:**

- Одиночный `requests.Session` на весь запуск — сайт использует CSRF-сессию,
  cookies должны сохраняться между запросами
- Первый запрос — GET главной страницы для инициализации сессии и получения
  CSRF-токена (если нужен для POST)
- Retry через `tenacity`: 3 попытки, `wait_exponential(multiplier=2, min=4, max=30)`
- Случайная задержка: `time.sleep(random.uniform(delay_min, delay_max))`
- Таймаут: `timeout=(10, 30)`

```python
def create_session() -> requests.Session: ...

def fetch_page(
    session: requests.Session,
    url: str,
    delay_min: float = DEFAULT_DELAY_MIN,
    delay_max: float = DEFAULT_DELAY_MAX,
) -> str: ...

def post_search(
    session: requests.Session,
    params: dict[str, str],
) -> str: ...
```

---

## Слой парсинга (`src/parsers/`)

### `company_parser.py`

```python
def parse_company_page(html: str, company_id: int) -> Company:
    """
    Извлекает все данные компании из HTML.
    Не бросает исключений для отсутствующих полей — возвращает None/[].
    """
    ...
```

**Логика извлечения телефонов (приоритетный путь):**

Найти в HTML секцию FAQ с паттерном "Номер телефона ... -":
```python
# Ожидаемый текст:
# "Номер телефона "НАЗВАНИЕ" ООО - 71 2270834; 71 2000056; 1347"
import re
pattern = re.compile(r'Номер телефона .+? - ([\d\s;]+)')
match = pattern.search(html)
if match:
    raw = match.group(1)
    phones = [p.strip() for p in raw.split(';') if p.strip()]
```

**Логика резолвинга сайта компании:**

```python
# В HTML: <a href="/go/?u=5ff4299f95409f623df4fada1776713b" title="Перейти на сайт">
# Вариант 1: извлечь title атрибута (если содержит URL)
# Вариант 2: HEAD-запрос к /go/?u=HASH и читать Location заголовок
# Выбрать по итогам задачи 0.6
```

**Логика парсинга рабочих часов:**

```python
# Таблица дней: <td>Пн:</td><td>09.00 - 18.00</td><td>не указан</td>
# Статус "выходной" -> WorkingHours(day="Сб", is_day_off=True)
```

### `listing_parser.py`

```python
def parse_company_ids(html: str) -> list[int]:
    """
    Извлекает числовые ID из ссылок /company/?Id=N.
    """
    ...

def get_total_count(html: str) -> int:
    """
    Парсит 'Найдено организаций: N'. Возвращает 0 если не найдено.
    """
    ...

def get_next_page_url(html: str, current_url: str) -> str | None:
    """
    После установления механизма пагинации (задача 0.2).
    """
    ...
```

---

## Путь A: Excel-экспорт с сайта (`src/collectors/excel_downloader.py`)

Применяется если задача 0.3 подтвердила: кнопка "Скачать список" возвращает
файл без авторизации.

```python
def download_rubric_excel(
    session: requests.Session,
    rubric_id: int,
) -> list[Company]:
    """
    Скачивает Excel-файл списка рубрики, парсит через openpyxl,
    маппирует колонки на модель Company.
    """
    ...
```

Преимущество: один запрос вместо N запросов (по одному на компанию).
Недостаток: поля могут быть ограничены (телефоны могут отсутствовать).

---

## Путь C: Playwright (если пагинация через JS)

Если задача 0.2 выявила, что пагинация реализована через JavaScript:

- Заменить `requests` + `BeautifulSoup` на `playwright` (async)
- `page.goto(url)` + `page.wait_for_selector('.company-list')`
- Для пагинации: `page.click('button.load-more')` или перехват XHR
- Телефоны могут стать доступны через `page.click('button.show-phone')`
  и считывание появившегося DOM-элемента

Playwright следует рассматривать как запасной вариант — он значительно
сложнее в rate-limiting и требует больше ресурсов.

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
| 10| `building`           | Дом/офис                |
| 11| `postal_code`        | Индекс                  |
| 12| `landmarks`          | Ориентиры               |
| 13| `activity_types`     | Виды деятельности       |
| 14| `inn`                | ИНН                     |
| 15| `last_updated`       | Обновлено               |
| 16| `url`                | URL                     |

Поля-списки (`phones`, `alt_names`, `landmarks`, `activity_types`)
объединяются через ` | ` в обоих форматах.

### CSV: кодировка `utf-8-sig`, разделитель `;`
### Excel: `openpyxl`, лист `Companies`, заморозка первой строки

---

## CLI (`main.py`)

```
python main.py --rubric 3473 --rubric 3778 --format both
python main.py --city 296 --format xlsx --output output/tashkent
python main.py --keyword "ресторан" --city 296 --format csv
python main.py --rubric 3473 --limit 10
```

| Аргумент      | Тип   | Описание                                         |
|---------------|-------|--------------------------------------------------|
| `--rubric`    | int   | ID рубрики. Повторяется для нескольких           |
| `--city`      | int   | ID города                                        |
| `--keyword`   | str   | Ключевое слово для поиска                        |
| `--output`    | str   | Путь без расширения (default: `output/result`)   |
| `--format`    | str   | `csv`, `xlsx` или `both` (default: `both`)       |
| `--limit`     | int   | Максимум компаний (для тестирования)             |
| `--delay-min` | float | Мин. пауза в сек (default: 1.5)                  |
| `--delay-max` | float | Макс. пауза в сек (default: 3.5)                 |

---

## Обработка ошибок

- HTTP-ошибки логируются, не прерывают запуск
- Компания с ошибкой парсинга пропускается, ID в `ScraperResult.errors`
- По завершении выводится итоговая статистика
- Логирование через `logging` (уровень INFO по умолчанию)

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
rich = "^13.7"           # опционально

# Только если Путь C (пагинация через JS):
# playwright = "^1.44"
```

---

## Что намеренно исключено из MVP

- Асинхронный HTTP (`httpx`) — добавить только если Путь C (Playwright),
  где async обязателен
- База данных — CSV/Excel покрывает требования
- Регулярный запуск / планировщик
- Резолвинг координат из карты (сложно, нет очевидного источника)
- Полный текст отзывов (за "Показать ещё" — требует JS)
