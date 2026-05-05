import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
from typing import Optional

from compressor.core import detect_format, compress_file, compress_batch
from compressor.models import MenuAction

app = typer.Typer(help="Multi-format file compressor")
console = Console()


def get_output_dir() -> Path:
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_input_dir() -> Path:
    default_input = Path.cwd() / "input"
    return default_input if default_input.exists() and default_input.is_dir() else Path.cwd()


def get_files_sorted(path: Path, recursive: bool = False) -> list[Path]:
    files = list(path.rglob("*")) if recursive else list(path.glob("*"))
    return [f for f in files if f.is_file()]


def print_compression_result(result: dict) -> None:
    table = Table(title="Compression Result")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for key, value in result.items():
        if key != "success":
            table.add_row(key, str(value))
    console.print(table)


def print_batch_report(results: list[dict]) -> None:
    table = Table(title="Batch Compression Report")
    for col in ["src", "format", "ratio", "time"]:
        table.add_column(col)
    
    total_original = total_compressed = 0
    for r in results:
        if r.get("success"):
            table.add_row(
                r.get("src", ""), r.get("format", ""),
                f"{r.get('ratio', 0)}%", f"{r.get('time', 0):.2f}s"
            )
            total_original += r.get("original_size", 0)
            total_compressed += r.get("compressed_size", 0)
        else:
            table.add_row(r.get("src", ""), "ERROR", r.get("error", ""), "")
    
    console.print(table)
    if total_original:
        saved = total_original - total_compressed
        console.print(f"[bold green]Total savings: {saved:,} bytes ({saved/total_original*100:.1f}%)[/bold green]")


def print_supported_formats() -> None:
    formats = [
        ("PDF", "application/pdf"),
        ("Images", "JPEG, PNG, WebP, AVIF"),
        ("Archives", "ZIP, 7Z, TAR"),
        ("Documents", "DOCX, XLSX"),
        ("Generic", "Any file (gzip)"),
    ]
    table = Table(title="Supported Formats")
    table.add_column("Category", style="cyan")
    table.add_column("Formats", style="green")
    for category, fmt in formats:
        table.add_row(category, fmt)
    console.print(table)


def compress_single_file(src: Path, quality: str, output_dir: Path) -> dict:
    dst = output_dir / src.name
    return compress_file(src, dst, quality, None)


def compress_directory_files(input_dir: Path, output_dir: Path, quality: str, recursive: bool = False) -> list[dict]:
    files = get_files_sorted(input_dir, recursive)
    if not files:
        console.print("[yellow]No files found[/yellow]")
        return []
    
    console.print(f"Found {len(files)} files in [cyan]{input_dir}[/cyan]")
    for f in files:
        console.print(f"  - {f.name}")
    
    if not Confirm.ask("Proceed?", default=True):
        return []
    
    results = []
    for f in files:
        dst = output_dir / f.name
        results.append(compress_file(f, dst, quality, None))
    return results


def run_menu_action(action: MenuAction, input_dir: Path, output_dir: Path) -> Optional[str]:
    match action:
        case MenuAction.SHOW_FORMATS:
            print_supported_formats()
        case MenuAction.EXIT:
            return "exit"
        case _:
            quality = Prompt.ask("Quality level", choices=["fast", "balanced", "best", "custom"], default="balanced")
            
            if action == MenuAction.COMPRESS_FILE:
                src = Path(Prompt.ask("Enter file path", default=str(input_dir)))
                if not src.exists():
                    console.print(f"[red]Error: {src} does not exist[/red]")
                    return None
                if not src.is_file():
                    console.print("[red]Error: Not a file[/red]")
                    return None
                result = compress_single_file(src, quality, output_dir)
                print_compression_result(result)
            
            elif action == MenuAction.COMPRESS_CURRENT_DIR:
                results = compress_directory_files(input_dir, output_dir, quality)
                if results:
                    print_batch_report(results)
            
            elif action == MenuAction.COMPRESS_DIRECTORY:
                dir_path = Path(Prompt.ask("Enter directory path", default=str(input_dir)))
                if not dir_path.exists() or not dir_path.is_dir():
                    console.print("[red]Error: Invalid directory[/red]")
                    return None
                
                recursive = Confirm.ask("Process subdirectories recursively?", default=False)
                results = compress_directory_files(dir_path, output_dir, quality, recursive)
                if results:
                    print_batch_report(results)
    
    return None


@app.command()
def menu() -> None:
    """Interactive menu-driven compression interface."""
    input_dir = get_input_dir()
    output_dir = get_output_dir()
    
    actions = {action.value: action for action in MenuAction}
    
    while True:
        console.print("\n[bold cyan]=== Compressor Menu ===[/bold cyan]")
        console.print("1. Select and compress a single file")
        console.print("2. Compress all files in input directory")
        console.print("3. Compress files in a specific directory")
        console.print("4. Show supported formats")
        console.print("5. Exit")
        
        choice = Prompt.ask("Choose an option", choices=list(actions.keys()), default=MenuAction.EXIT.value)
        
        if run_menu_action(actions[choice], input_dir, output_dir) == "exit":
            console.print("[green]Goodbye![/green]")
            break


@app.command()
def compress(
    input_path: Optional[Path] = typer.Argument(None, help="Input file or directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    quality: str = typer.Option("balanced", "--quality", "-q", help="fast|balanced|best|custom"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Output format"),
    batch: bool = typer.Option(False, "--batch", "-b", help="Process directory recursively"),
    workers: int = typer.Option(0, "--workers", "-w", help="Parallel workers (0=auto)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Force interactive prompts"),
) -> None:
    """Compress files with dynamic quality presets."""
    if not input_path or interactive:
        input_path = Path(Prompt.ask("Input file or directory", default=str(input_path) if input_path else "."))
        if not quality or quality == "balanced" or interactive:
            quality = Prompt.ask("Quality level", choices=["fast", "balanced", "best", "custom"], default="balanced")
        if not format and interactive:
            fmt = detect_format(input_path) if input_path.is_file() else None
            if fmt:
                convert = Confirm.ask("Convert to another format?", default=False)
                if convert:
                    format = Prompt.ask("Target format", default="pdf" if fmt == "pdf" else "webp")
    
    if not input_path.exists():
        console.print(f"[red]Error: {input_path} does not exist[/red]")
        raise typer.Exit(1)
    
    if input_path.is_file():
        result = compress_file(input_path, output, quality, None, **({"convert": format} if format else {}))
        print_compression_result(result)
    elif input_path.is_dir():
        files = get_files_sorted(input_path, batch)
        console.print(f"Found {len(files)} files to process")
        results = compress_batch(files, quality, workers, **({"convert": format} if format else {}))
        print_batch_report(results)
    else:
        console.print("[red]Invalid input path[/red]")


if __name__ == "__main__":
    app()