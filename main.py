import argparse
import logging
import sys

from src.collectors.city_collector import collect_city
from src.collectors.keyword_collector import collect_keyword
from src.collectors.multi_rubric_collector import collect_rubrics
from src.exporters.csv_exporter import export_csv
from src.exporters.excel_exporter import export_excel
from src.http_client import create_session
from src.models import ScraperResult, SearchParams

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scraper for goldenpages.uz")
    p.add_argument("--rubric", type=int, action="append", dest="rubrics", metavar="ID")
    p.add_argument("--city", type=int)
    p.add_argument("--keyword", type=str)
    p.add_argument("--output", default="output/result")
    p.add_argument("--format", choices=["csv", "xlsx", "both"], default="both")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay-min", type=float, default=1.5, dest="delay_min")
    p.add_argument("--delay-max", type=float, default=3.5, dest="delay_max")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if not args.rubrics and not args.city and not args.keyword:
        print("Error: specify at least one of --rubric, --city, --keyword", file=sys.stderr)
        sys.exit(1)

    params = SearchParams(
        rubric_ids=args.rubrics or [],
        city_id=args.city,
        keyword=args.keyword,
        output_path=args.output,
        output_format=args.format,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        limit=args.limit,
    )

    session = create_session()
    companies = []
    result = ScraperResult(total_found=0, total_exported=0, duplicates_removed=0)

    if args.rubrics:
        companies, result = collect_rubrics(session, args.rubrics, params)
    elif args.city:
        companies = collect_city(session, args.city, params)
        result = ScraperResult(
            total_found=len(companies),
            total_exported=len(companies),
            duplicates_removed=0,
        )
    elif args.keyword:
        companies = collect_keyword(session, args.keyword, params)
        result = ScraperResult(
            total_found=len(companies),
            total_exported=len(companies),
            duplicates_removed=0,
        )

    output_files: list[str] = []
    if args.format in ("csv", "both"):
        output_files.append(export_csv(companies, args.output))
    if args.format in ("xlsx", "both"):
        output_files.append(export_excel(companies, args.output))

    result.output_files = output_files

    print(f"\nДобавлено компаний: {result.total_found}")
    print(f"Экспортировано:      {result.total_exported}")
    print(f"Дубликатов удалено:  {result.duplicates_removed}")
    if result.errors:
        print(f"Ошибок:             {len(result.errors)}")
    for f in output_files:
        print(f"  -> {f}")


if __name__ == "__main__":
    main()
