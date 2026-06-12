# gpuz-parser

Консольный инструмент для сбора данных о компаниях с
[goldenpages.uz](https://www.goldenpages.uz) — узбекского бизнес-справочника
"Золотые Страницы". Экспортирует результаты в CSV и/или Excel.

## Требования

- Python 3.11+
- [Poetry](https://python-poetry.org/) (или `pip` + `venv`)

## Установка

```bash
git clone https://github.com/<your-username>/gpuz-parser.git
cd gpuz-parser
poetry install
```

Или через `venv`:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

## Использование

```bash
# Одна рубрика
python main.py --rubric 3473

# Несколько рубрик с дедупликацией
python main.py --rubric 3473 --rubric 3778

# Все компании города
python main.py --city 296

# Поиск по ключевому слову в городе
python main.py --keyword "ресторан" --city 296

# Указать формат и путь вывода
python main.py --rubric 3473 --format xlsx --output output/restaurants

# Тестовый прогон (первые 10 компаний)
python main.py --rubric 3473 --limit 10
```

### Аргументы

| Аргумент      | Тип   | По умолчанию      | Описание                                  |
|---------------|-------|-------------------|-------------------------------------------|
| `--rubric`    | int   |                   | ID рубрики. Повторяется для нескольких    |
| `--city`      | int   |                   | ID города                                 |
| `--keyword`   | str   |                   | Ключевое слово для поиска                 |
| `--output`    | str   | `output/result`   | Путь к файлу вывода без расширения        |
| `--format`    | str   | `both`            | `csv`, `xlsx` или `both`                  |
| `--limit`     | int   |                   | Максимум компаний (для тестирования)      |
| `--delay-min` | float | `1.5`             | Мин. пауза между запросами, сек           |
| `--delay-max` | float | `3.5`             | Макс. пауза между запросами, сек          |

### Известные ID

Числовые ID используются во всех аргументах вместо текстовых названий.
Частичный список городов:

| Город     | `--city` |
|-----------|----------|
| Ташкент   | 296      |
| Самарканд | 322      |

ID рубрик берутся из URL на сайте: `goldenpages.uz/rubrics/?Id=<ID>`.

## Выходные данные

Результат записывается в `output/` (создаётся автоматически).
При `--format both` создаются два файла: `<name>.csv` и `<name>.xlsx`.

CSV использует кодировку UTF-8 с BOM и разделитель `;` — корректно
открывается в Excel на Windows без дополнительных настроек.

Поля в выходных файлах:

| Колонка           | Описание                                   |
|-------------------|--------------------------------------------|
| Название          | Основное название компании                 |
| Доп. названия     | Альтернативные и бывшие названия           |
| Телефоны          | Все телефоны, разделённые ` \| `           |
| Сайт              | URL сайта компании                         |
| Telegram          | Ссылка на Telegram                         |
| Город             | Город                                      |
| Регион            | Область                                    |
| Район             | Район (для Ташкента)                       |
| Улица             | Улица                                      |
| Дом/офис          | Номер дома или офиса                       |
| Индекс            | Почтовый индекс                            |
| Ориентиры         | Ориентиры рядом, разделённые ` \| `        |
| Виды деятельности | Категории компании, разделённые ` \| `     |
| ИНН               | ИНН (частично скрыт на сайте)              |
| Обновлено         | Дата последнего обновления на сайте        |
| URL               | Ссылка на страницу компании                |

## Структура проекта

```
gpuz-parser/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTEXT.md
│   └── TODO.md
├── src/
│   ├── config.py
│   ├── models.py
│   ├── http_client.py
│   ├── parsers/
│   │   ├── company_parser.py
│   │   └── listing_parser.py
│   ├── collectors/
│   │   ├── rubric_collector.py
│   │   ├── city_collector.py
│   │   ├── keyword_collector.py
│   │   └── multi_rubric_collector.py
│   └── exporters/
│       ├── csv_exporter.py
│       └── excel_exporter.py
├── tests/
│   └── fixtures/
├── output/
├── main.py
├── pyproject.toml
├── .gitignore
└── README.md
```

## Запуск тестов

```bash
poetry run pytest
```

## Примечания

- Между запросами выдерживается случайная пауза (по умолчанию 1.5–3.5 сек),
  чтобы не создавать избыточную нагрузку на сервер.
- Телефоны извлекаются из FAQ-блока в нижней части страницы компании —
  единственного места, где они присутствуют в HTML без JavaScript.
- Сайт не предоставляет публичного API.