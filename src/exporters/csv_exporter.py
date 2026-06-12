from __future__ import annotations

import csv
from pathlib import Path

from src.models import Company

COLUMNS: list[tuple[str, str]] = [
    ("name", "Название"),
    ("alt_names", "Доп. названия"),
    ("phones", "Телефоны"),
    ("website", "Сайт"),
    ("telegram", "Telegram"),
    ("city", "Город"),
    ("region", "Регион"),
    ("district", "Район"),
    ("street", "Улица"),
    ("building", "Дом/офис"),
    ("postal_code", "Индекс"),
    ("landmarks", "Ориентиры"),
    ("activity_types", "Виды деятельности"),
    ("inn", "ИНН"),
    ("last_updated", "Обновлено"),
    ("url", "URL"),
]


def _get_value(company: Company, field: str) -> str:
    value = getattr(company, field, None)
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    return str(value)


def export_csv(companies: list[Company], output_path: str) -> str:
    path = Path(output_path).with_suffix(".csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([header for _, header in COLUMNS])
        for company in companies:
            writer.writerow([_get_value(company, field) for field, _ in COLUMNS])

    return str(path)
