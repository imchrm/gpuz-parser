# CLAUDE.md — goldenpages-scraper

Консольный Python-скрепер для сбора данных о компаниях с **https://www.goldenpages.uz** (узбекский бизнес-справочник). Одноразовый дамп, не мониторинг. Выходной формат: CSV и/или Excel (.xlsx).

---

## Архитектура

Однонаправленный поток данных:

```
CLI -> Collector -> HTTP Client -> Parser -> Model -> Exporter -> File
```

Каждый слой зависит только от следующего. Парсеры не знают об HTTP. Экспортеры не знают о парсерах.

### Структура проекта

```
goldenpages-scraper/
├── docs/
│   ├── CONTEXT.md
│   ├── TODO.md
│   └── ARCHITECTURE.md
├── src/
│   ├── config.py              # константы, BASE_URL, задержки, ID городов
│   ├── models.py              # Pydantic-модели: Company, SearchParams, ScraperResult
│   ├── http_client.py         # requests.Session, retry (tenacity), rate limiting
│   ├── parsers/
│   │   ├── company_parser.py  # парсинг страницы одной компании
│   │   └── listing_parser.py  # парсинг страницы-списка (рубрика/поиск)
│   ├── collectors/
│   │   ├── rubric_collector.py
│   │   ├── city_collector.py
│   │   ├── keyword_collector.py
│   │   ├── multi_rubric_collector.py
│   │   └── excel_downloader.py  # Путь A: Excel-экспорт с сайта
│   └── exporters/
│       ├── csv_exporter.py
│       └── excel_exporter.py
├── tests/
│   ├── fixtures/              # сохранённые HTML-страницы для тестов
│   ├── test_company_parser.py
│   └── test_listing_parser.py
├── output/                    # в .gitignore
├── main.py                    # точка входа CLI
└── pyproject.toml
```

---

## Целевой сайт

- **Стек:** классический серверный рендеринг (PHP/Yii). `requests` + `BeautifulSoup` работают без headless-браузера.
- **URL компании:** `/company/?Id=57473` (числовые ID, не slug)
- **URL рубрики:** `/rubrics/?Id=3473`
- **URL города:** `/city/?Id=296`
- **Языковая версия для парсинга:** русская (наиболее полная)

### Ключевые особенности

**Телефоны:** кнопка "Показать телефон" делает GET-запрос к открытому AJAX-эндпоинту — авторизация не нужна:
```
GET /scripts/company_data/?cid={company_id}&ctype=phone&clang=ru
```
Ответ — HTML-фрагмент со списком `<a href="tel:+998...">`. Номер берётся из атрибута `href` (чистый формат `+998XXXXXXXXX`).

**Внешние ссылки:** сайты компаний скрыты за редиректом `/go/?u=HASH`. Резолвинг через HEAD-запрос или `title`-атрибут ссылки.

**Пагинация рубрик:** классическая серверная — ссылки «1, 2, 3… / Следующая» (задача 0.2 закрыта, **Путь B**).

**Кнопка "Скачать список":** требует авторизации — **Путь A отклонён**.

---

## Известные ID

| Город     | city_id |
|-----------|---------|
| Ташкент   | 296     |
| Самарканд | 322     |

---

## Команды запуска

```bash
python main.py --rubric 3473 --rubric 3778 --format both
python main.py --city 296 --format xlsx --output output/tashkent
python main.py --keyword "ресторан" --city 296 --format csv
python main.py --rubric 3473 --limit 10   # тестовый прогон
```

| Аргумент      | Описание                                        |
|---------------|-------------------------------------------------|
| `--rubric`    | ID рубрики (повторяется для нескольких)         |
| `--city`      | ID города                                       |
| `--keyword`   | Ключевое слово для POST-поиска                  |
| `--output`    | Путь без расширения (default: `output/result`)  |
| `--format`    | `csv`, `xlsx` или `both` (default: `both`)      |
| `--limit`     | Максимум компаний (для тестирования)            |
| `--delay-min` | Мин. пауза в сек (default: 1.5)                 |
| `--delay-max` | Макс. пауза в сек (default: 3.5)                |

---

## Стандарты кода

- **Python 3.11+**, строгая аннотация типов везде, `mypy`-совместимость
- **Pydantic v2** для моделей данных
- Retry через `tenacity`: 3 попытки, `wait_exponential(multiplier=2, min=4, max=30)`
- Случайные паузы между запросами: `random.uniform(1.5, 3.5)` сек — обязательно
- Один `requests.Session` на весь запуск (сохранение cookies/CSRF)
- HTTP-ошибки логируются, не прерывают запуск; проблемные компании попадают в `ScraperResult.errors`
- Поля-списки в экспорте объединяются через ` | `
- CSV: кодировка `utf-8-sig` (UTF-8 с BOM для Windows Excel), разделитель `;`

### Зависимости

```toml
requests = "^2.32"
beautifulsoup4 = "^4.12"
lxml = "^5.2"
pydantic = "^2.7"
openpyxl = "^3.1"
tenacity = "^8.3"
rich = "^13.7"   # опционально
# playwright = "^1.44"  — только если пагинация через JS (Путь C)
```

---

## Статус проекта

Фаза 0 (разведка) завершена. **Реализуется Путь B.**

| ID   | Задача                                              | Приоритет | Статус               |
|------|-----------------------------------------------------|-----------|----------------------|
| 0.1  | Проверить `robots.txt`                              | HIGH      | Открыт               |
| 0.2  | Установить механизм пагинации рубрик                | CRITICAL  | ✅ Серверная (Путь B) |
| 0.3  | Проверить кнопку "Скачать список"                   | CRITICAL  | ✅ Требует авторизации — Путь A отклонён |
| 0.4  | Установить параметры POST-формы поиска              | MEDIUM    | Открыт               |
| 0.5  | Получение телефонов                                 | HIGH      | ✅ AJAX GET `/scripts/company_data/` |
| 0.6  | Исследовать резолвинг `/go/?u=HASH`                 | MEDIUM    | Открыт               |
| 0.7  | Собрать таблицу ID всех городов/регионов            | MEDIUM    | Открыт               |

### Выбранная архитектура

- **Путь B** (активен): серверная пагинация → `requests` + `BeautifulSoup`
- **Путь A** — отклонён: Excel требует авторизации
- **Путь C** — не нужен: пагинация серверная

---

## Ограничения

- Агрессивный парсинг недопустим — обязательны паузы между запросами
- Страница `/search/` имеет `meta-robots: noindex, nofollow`
- Внешние URL компаний не извлекаются напрямую из HTML
- Телефоны в верхней части страницы замаскированы и требуют JS
- Полный текст отзывов за "Показать ещё" недоступен без JS

Подробности: `docs/CONTEXT.md`, `docs/TODO.md`, `docs/ARCHITECTURE.md`.
