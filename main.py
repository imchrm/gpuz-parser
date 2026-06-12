from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from src.collectors.city_collector import collect_city
from src.collectors.keyword_collector import collect_keyword
from src.collectors.multi_rubric_collector import collect_rubrics
from src.exporters.csv_exporter import export_csv
from src.exporters.excel_exporter import export_excel
from src.http_client import create_session
from src.models import ScraperResult, SearchParams

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scraper for goldenpages.uz",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--rubric", type=int, action="append", dest="rubric_ids", metavar="ID")
    parser.add_argument("--city", type=int, dest="city_id", metavar="ID")
    parser.add_argument("--keyword", type=str)
    parser.add_argument("--output", type=str, default="output/result")
    parser.add_argument("--format", choices=["csv", "xlsx", "both"], default="both", dest="output_format")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay-min", type=float, default=1.5, dest="delay_min")
    parser.add_argument("--delay-max", type=float, default=3.5, dest="delay_max")
    return parser


def _print_result(result: ScraperResult, output_files: list[str]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Scraping Result")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total found", str(result.total_found))
        table.add_row("Total exported", str(result.total_exported))
        table.add_row("Duplicates removed", str(result.duplicates_removed))
        table.add_row("Errors", str(len(result.errors)))
        console.print(table)
        if output_files:
            console.print("[bold]Output files:[/bold]")
            for f in output_files:
                console.print(f"  {f}")
        if result.errors:
            console.print("[bold red]Errors:[/bold red]")
            for err in result.errors:
                console.print(f"  {err}")
    except ImportError:
        print(f"Total found: {result.total_found}")
        print(f"Total exported: {result.total_exported}")
        print(f"Duplicates removed: {result.duplicates_removed}")
        print(f"Errors: {len(result.errors)}")
        if output_files:
            print("Output files:")
            for f in output_files:
                print(f"  {f}")


def main() -> None:
    arg_parser = build_parser()
    args = arg_parser.parse_args()

    if not args.rubric_ids and args.city_id is None and not args.keyword:
        arg_parser.print_help()
        sys.exit(1)

    params = SearchParams(
        rubric_ids=args.rubric_ids or [],
        city_id=args.city_id,
        keyword=args.keyword,
        output_path=args.output,
        output_format=args.output_format,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        limit=args.limit,
    )

    session = create_session()
    result: Optional[ScraperResult] = None
    companies = []

    if args.rubric_ids:
        companies, result = collect_rubrics(session, args.rubric_ids, params)
    elif args.city_id is not None:
        companies = collect_city(session, args.city_id, params)
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

    if result is None:
        result = ScraperResult(total_found=0, total_exported=0, duplicates_removed=0)

    output_files: list[str] = []
    if companies:
        if params.output_format in ("csv", "both"):
            csv_path = export_csv(companies, params.output_path)
            output_files.append(csv_path)
            logger.info("CSV exported to %s", csv_path)

        if params.output_format in ("xlsx", "both"):
            xlsx_path = export_excel(companies, params.output_path)
            output_files.append(xlsx_path)
            logger.info("Excel exported to %s", xlsx_path)

    result.output_files = output_files
    _print_result(result, output_files)


if __name__ == "__main__":
    main()
