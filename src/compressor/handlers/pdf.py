import subprocess
import sys
from pathlib import Path
from typing import Any

def compress_pdf(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress PDF using PyMuPDF with image optimization."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")
    dpi = opts.get("dpi", 150)
    compress_fonts = opts.get("compress_fonts", True)
    doc = fitz.open(str(src))
    for page in doc:
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image:
                    from PIL import Image
                    import io
                    pil_img = Image.open(io.BytesIO(base_image["image"]))
                    new_size = (int(pil_img.width * dpi / 300), int(pil_img.height * dpi / 300))
                    pil_img = pil_img.resize(new_size, Image.LANCZOS)
                    buf = io.BytesIO()
                    pil_img.save(buf, format='JPEG', quality=60, optimize=True)
                    doc.replace_image(xref, buf.getvalue())
            except Exception:
                pass
    doc.save(str(dst), garbage=3, deflate=True)
    doc.close()
    if not dst.exists():
        raise FileNotFoundError(f"Compression failed: {dst} not created")
    return dst
