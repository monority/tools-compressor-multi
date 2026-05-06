from pathlib import Path
from typing import Any

def compress_image(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress images using Pillow (supports JPG/PNG/WebP/AVIF)."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow not installed. Run: pip install Pillow pillow-avif-plugin")
    dst.parent.mkdir(parents=True, exist_ok=True)
    quality = opts.get("jpg_quality", 60)
    convert_fmt = opts.get("convert") or opts.get("format")
    resize = opts.get("resize")
    with Image.open(src) as img:
        if resize:
            w, h = img.size
            scale = float(resize.strip("%")) / 100 if isinstance(resize, str) else resize
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        save_fmt = (convert_fmt or src.suffix.lstrip(".")).upper()
        save_fmt = "JPEG" if save_fmt == "JPG" else save_fmt
        params = {}
        if save_fmt in ("JPEG", "WEBP"):
            params["quality"] = quality
            params["optimize"] = True
        elif save_fmt == "PNG":
            params["optimize"] = True
        if save_fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out_ext = f".{save_fmt.lower() if save_fmt != 'JPEG' else 'jpg'}"
        out = dst.with_suffix(out_ext) if dst.suffix else src.with_suffix(out_ext)
        img.save(out, format=save_fmt, **params)
        return out
