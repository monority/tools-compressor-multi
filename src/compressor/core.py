import concurrent.futures
import hashlib
import os
import time
from pathlib import Path
from typing import Callable, Type
import puremagic

from compressor.config import load_config, get_preset

HandlerFn = Callable[[Path, Path, dict], Path]

_handler_cache: dict[str, HandlerFn] = {}

MIME_MAP = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/avif": "image",
    "application/zip": "archive",
    "application/x-7z-compressed": "archive",
    "application/x-tar": "archive",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "document",
    "text/plain": "generic",
    "text/x-python": "generic",
    "application/javascript": "generic",
}

def detect_format(filepath: Path) -> str | None:
    """Detect file format from MIME type."""
    try:
        mime = puremagic.from_file(str(filepath), mime=True)
        return MIME_MAP.get(mime)
    except Exception:
        return None

def get_handler(fmt: str) -> HandlerFn | None:
    """Lazy-load handler for format."""
    if fmt in _handler_cache:
        return _handler_cache[fmt]
    try:
        if fmt == "pdf":
            from compressor.handlers.pdf import compress_pdf
            _handler_cache[fmt] = compress_pdf
        elif fmt == "image":
            from compressor.handlers.image import compress_image
            _handler_cache[fmt] = compress_image
        elif fmt == "archive":
            from compressor.handlers.archive import compress_archive
            _handler_cache[fmt] = compress_archive
        elif fmt == "document":
            from compressor.handlers.document import compress_document
            _handler_cache[fmt] = compress_document
    except ImportError:
        return None
    return _handler_cache.get(fmt)

def file_hash(filepath: Path, algo: str = "sha256") -> bytes:
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def compress_file(
    src: Path,
    dst: Path | None = None,
    quality: str = "balanced",
    config_path: Path | None = None,
    **kwargs,
) -> dict:
    """Compress single file, return result dict."""
    fmt = detect_format(src)
    if not fmt:
        fmt = "generic"
    if fmt == "generic":
        import gzip, shutil
        dst = dst or src.with_suffix(src.suffix + ".gz")
        try:
            import time
            start = time.perf_counter()
            with open(src, 'rb') as f_in:
                with gzip.open(dst, 'wb', compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            elapsed = time.perf_counter() - start
            orig_size = src.stat().st_size
            new_size = dst.stat().st_size
            return {
                "src": str(src),
                "dst": str(dst),
                "format": "generic",
                "quality": quality,
                "original_size": orig_size,
                "compressed_size": new_size,
                "ratio": round((1 - new_size / orig_size) * 100, 2) if orig_size else 0,
                "time": elapsed,
                "success": True,
            }
        except Exception as e:
            return {"src": str(src), "error": str(e), "success": False}
    handler = get_handler(fmt)
    if not handler:
        return {"src": str(src), "error": "Handler not available", "success": False}
    config = load_config(config_path)
    preset = get_preset(config, fmt, quality)
    preset.update(kwargs)
    dst = dst or src.with_stem(src.stem + "_compressed").with_suffix(src.suffix)
    try:
        import time
        start = time.perf_counter()
        result_path = handler(src, dst, preset)
        elapsed = time.perf_counter() - start
        orig_size = src.stat().st_size
        new_size = result_path.stat().st_size if result_path.exists() else 0
        return {
            "src": str(src),
            "dst": str(result_path),
            "format": fmt,
            "quality": quality,
            "original_size": orig_size,
            "compressed_size": new_size,
            "ratio": round((1 - new_size / orig_size) * 100, 2) if orig_size else 0,
            "time": elapsed,
            "success": True,
        }
    except Exception as e:
        return {"src": str(src), "error": str(e), "success": False}

def compress_batch(
    files: list[Path],
    quality: str = "balanced",
    workers: int = 0,
    **kwargs,
) -> list[dict]:
    """Compress multiple files concurrently."""
    workers = workers or os.cpu_count() or 1
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(compress_file, f, None, quality, None, **kwargs): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results
