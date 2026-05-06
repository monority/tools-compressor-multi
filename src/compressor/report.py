from pathlib import Path
import json

from rich.console import Console
from rich.table import Table


def print_result(result: dict, console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Compression Result")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for key, value in result.items():
        if key != "success":
            table.add_row(key, str(value))
    console.print(table)


def print_batch_report(results: list[dict], console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Batch Compression Report")
    for col in ["src", "format", "ratio", "time"]:
        table.add_column(col)

    total_original = 0
    total_compressed = 0
    for result in results:
        if result.get("success"):
            table.add_row(
                result.get("src", ""),
                result.get("format", ""),
                f"{result.get('ratio', 0)}%",
                f"{result.get('time', 0):.2f}s",
            )
            total_original += result.get("original_size", 0)
            total_compressed += result.get("compressed_size", 0)
        else:
            table.add_row(result.get("src", ""), "ERROR", result.get("error", ""), "")

    console.print(table)
    if total_original:
        saved = total_original - total_compressed
        console.print(f"[bold green]Total savings: {saved:,} bytes ({saved/total_original*100:.1f}%)[/bold green]")


def export_json(results: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
