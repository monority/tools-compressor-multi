import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
from typing import Optional
from compressor.core import detect_format, compress_file, compress_batch, file_hash

app = typer.Typer(help="Multi-format file compressor")
console = Console()

@app.command()
def compress(
    input_path: Optional[Path] = typer.Argument(None, help="Input file or directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    quality: str = typer.Option("balanced", "--quality", "-q", help="fast|balanced|best|custom"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Output format"),
    batch: bool = typer.Option(False, "--batch", "-b", help="Process directory recursively"),
    workers: int = typer.Option(0, "--workers", "-w", help="Parallel workers (0=auto)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Force interactive prompts"),
):
    """Compress files with dynamic quality presets."""
    if not input_path or interactive:
        input_path = Path(Prompt.ask("Input file or directory", default=str(input_path) if input_path else "."))
        if not quality or quality == "balanced" or interactive:
            quality = Prompt.ask("Quality level", choices=["fast", "balanced", "best", "custom"], default="balanced")
        if not format and interactive:
            fmt = detect_format(input_path) if input_path.is_file() else None
            if fmt:
                convert = Confirm.ask(f"Convert to another format?", default=False)
                if convert:
                    format = Prompt.ask("Target format", default="pdf" if fmt == "pdf" else "webp")
    if not input_path.exists():
        console.print(f"[red]Error: {input_path} does not exist[/red]")
        raise typer.Exit(1)
    if input_path.is_file():
        result = compress_file(input_path, output, quality, None, **({"convert": format} if format else {}))
        _print_result(result)
    elif input_path.is_dir():
        files = list(input_path.rglob("*")) if batch else list(input_path.glob("*"))
        files = [f for f in files if f.is_file()]
        console.print(f"Found {len(files)} files to process")
        results = compress_batch(files, quality, workers, **({"convert": format} if format else {}))
        _print_report(results)
    else:
        console.print("[red]Invalid input path[/red]")

def _print_result(result: dict):
    table = Table(title="Compression Result")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for k, v in result.items():
        if k not in ("success",):
            table.add_row(k, str(v))
    console.print(table)

def _print_report(results: list[dict]):
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

if __name__ == "__main__":
    app()
