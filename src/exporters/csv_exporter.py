import csv
from pathlib import Path

from src.models import Company

HEADERS = [
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

_LIST_FIELDS = {"alt_names", "phones", "landmarks", "activity_types"}


def _cell(company: Company, field: str) -> str:
    value = getattr(company, field, None)
    if value is None:
        return ""
    if field in _LIST_FIELDS:
        return " | ".join(str(v) for v in value)
    return str(value)


def export_csv(companies: list[Company], path: str) -> str:
    output_path = Path(path).with_suffix(".csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([label for _, label in HEADERS])
        for company in companies:
            writer.writerow([_cell(company, field) for field, _ in HEADERS])

    return str(output_path)
