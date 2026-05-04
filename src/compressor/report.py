from rich.table import Table
from rich.console import Console
from pathlib import Path
import json

def print_result(result: dict, console: Console = None):
    console = console or Console()
    table = Table(title="Compression Result")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for k, v in result.items():
        if k not in ("success",):
            table.add_row(k, str(v))
    console.print(table)

def print_batch_report(results: list[dict], console: Console = None):
    console = console or Console()
    table = Table(title="Batch Compression Report")
    for col in ["src", "format", "ratio", "time"]:
        table.add_column(col)
    total_original = total_compressed = 0
    for r in results:
        if r.get("success"):
            table.add_row(r.get("src", ""), r.get("format", ""), f"{r.get('ratio', 0)}%", f"{r.get('time', 0):.2f}s")
            total_original += r.get("original_size", 0)
            total_compressed += r.get("compressed_size", 0)
        else:
            table.add_row(r.get("src", ""), "ERROR", r.get("error", ""), "")
    console.print(table)
    if total_original:
        saved = total_original - total_compressed
        console.print(f"[bold green]Total savings: {saved:,} bytes ({saved/total_original*100:.1f}%)[/bold green]")

def export_json(results: list[dict], path: Path):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
