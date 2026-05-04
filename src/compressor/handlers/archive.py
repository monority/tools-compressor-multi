from pathlib import Path
from typing import Any
import zipfile
import tarfile

def compress_archive(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress using std lib or zstandard/py7zr."""
    fmt = opts.get("format", "zip")
    level = opts.get("level", 6)
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
        import gzip
        with open(src, 'rb') as f_in:
            with gzip.open(out, 'wb', compresslevel=level) as f_out:
                f_out.write(f_in.read())
        return out
    raise ValueError(f"Unsupported archive format: {fmt}")
