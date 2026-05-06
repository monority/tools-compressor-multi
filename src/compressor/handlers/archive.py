from pathlib import Path
from typing import Any
import gzip
import tarfile
import zipfile

def compress_archive(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress using std lib or py7zr."""
    fmt = str(opts.get("format", "zip")).lower()
    level = opts.get("level", 6)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "7z":
        try:
            import py7zr
        except ImportError:
            raise RuntimeError("py7zr not installed. Run: pip install py7zr")
        out = dst.with_suffix(".7z")
        with py7zr.SevenZipFile(out, 'w', filters=py7zr.FILTER_LZMA2) as sz:
            sz.write(src, arcname=src.name)
        return out
    elif fmt == "zip":
        out = dst.with_suffix(".zip")
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=level) as zf:
            zf.write(src, arcname=src.name)
        return out
    elif fmt in ("tar.gz", "tgz"):
        out = dst.with_suffix(".tar.gz")
        with gzip.open(out, 'wb', compresslevel=level) as f_out:
            with tarfile.open(fileobj=f_out, mode='w') as tf:
                tf.add(src, arcname=src.name)
        return out
    raise ValueError(f"Unsupported archive format: {fmt}")
