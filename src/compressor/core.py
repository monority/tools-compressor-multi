import concurrent.futures
import gzip
import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Callable

import puremagic

from compressor.config import load_config, get_preset

HandlerFn = Callable[[Path, Path, dict], Path]

_handler_cache: dict[str, HandlerFn] = {}

MIME_MAP: dict[str, str] = {
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

_HANDLER_MODULES: dict[str, str] = {
    "pdf": "compressor.handlers.pdf:compress_pdf",
    "image": "compressor.handlers.image:compress_image",
    "archive": "compressor.handlers.archive:compress_archive",
    "document": "compressor.handlers.document:compress_document",
}


def detect_format(filepath: Path) -> str | None:
    try:
        mime = puremagic.from_file(str(filepath), mime=True)
        return MIME_MAP.get(mime)
    except Exception:
        return None


def get_handler(fmt: str) -> HandlerFn | None:
    if fmt in _handler_cache:
        return _handler_cache[fmt]
    
    module_path = _HANDLER_MODULES.get(fmt)
    if not module_path:
        return None
    
    try:
        module_name, attr = module_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[attr])
        handler = getattr(module, attr)
        _handler_cache[fmt] = handler
        return handler
    except (ImportError, AttributeError):
        return None


def file_hash(filepath: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _compress_generic(src: Path, dst: Path | None, quality: str) -> dict:
    dst = dst or src.with_suffix(src.suffix + ".gz")
    try:
        start = time.perf_counter()
        with open(src, "rb") as f_in:
            with gzip.open(dst, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        elapsed = time.perf_counter() - start
        orig_size = src.stat().st_size
        new_size = dst.stat().st_size
        return {
            "src": str(src), "dst": str(dst), "format": "generic",
            "quality": quality, "original_size": orig_size,
            "compressed_size": new_size,
            "ratio": round((1 - new_size / orig_size) * 100, 2) if orig_size else 0,
            "time": elapsed, "success": True,
        }
    except Exception as e:
        return {"src": str(src), "error": str(e), "success": False}


def compress_file(
    src: Path,
    dst: Path | None = None,
    quality: str = "balanced",
    config_path: Path | None = None,
    **kwargs,
) -> dict:
    fmt = detect_format(src) or "generic"
    
    if fmt == "generic":
        return _compress_generic(src, dst, quality)
    
    handler = get_handler(fmt)
    if not handler:
        return {"src": str(src), "error": "Handler not available", "success": False}
    
    config = load_config(config_path)
    preset = get_preset(config, fmt, quality)
    preset.update(kwargs)
    dst = dst or src.with_stem(src.stem + "_compressed").with_suffix(src.suffix)
    
    try:
        start = time.perf_counter()
        result_path = handler(src, dst, preset)
        elapsed = time.perf_counter() - start
        orig_size = src.stat().st_size
        new_size = result_path.stat().st_size if result_path.exists() else 0
        return {
            "src": str(src), "dst": str(result_path), "format": fmt,
            "quality": quality, "original_size": orig_size,
            "compressed_size": new_size,
            "ratio": round((1 - new_size / orig_size) * 100, 2) if orig_size else 0,
            "time": elapsed, "success": True,
        }
    except Exception as e:
        return {"src": str(src), "error": str(e), "success": False}


def compress_batch(
    files: list[Path],
    quality: str = "balanced",
    workers: int = 0,
    **kwargs,
) -> list[dict]:
    workers = workers or os.cpu_count() or 1
    results: list[dict] = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(compress_file, f, None, quality, None, **kwargs): f
            for f in files
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results