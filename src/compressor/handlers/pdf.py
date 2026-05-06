import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def compress_pdf(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress PDF using PyMuPDF with image optimization."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dpi = opts.get("dpi", 150)
    compress_fonts = opts.get("compress_fonts", True)
    linearize = opts.get("linearize", False)
    doc = fitz.open(str(src))
    try:
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue
                    from PIL import Image
                    import io

                    with Image.open(io.BytesIO(base_image["image"])) as pil_img:
                        new_size = (int(pil_img.width * dpi / 300), int(pil_img.height * dpi / 300))
                        if new_size[0] <= 0 or new_size[1] <= 0:
                            continue
                        resized = pil_img.resize(new_size, Image.LANCZOS)
                        buf = io.BytesIO()
                        resized.save(buf, format="JPEG", quality=60, optimize=True)
                        doc.replace_image(xref, buf.getvalue())
                except (AttributeError, KeyError, OSError, ValueError, TypeError, RuntimeError) as exc:
                    logger.debug("PDF image optimization skipped for xref %s: %s", xref, exc)

        save_kwargs = {"garbage": 3, "deflate": True, "clean": True}
        if linearize:
            save_kwargs["linear"] = True
        try:
            try:
                doc.save(str(dst), **save_kwargs, deflate_images=True, deflate_fonts=compress_fonts)
            except TypeError:
                doc.save(str(dst), **save_kwargs)
        except Exception as exc:
            if not linearize or "Linearisation is no longer supported" not in str(exc):
                raise
            logger.debug("PDF linearization unsupported by this PyMuPDF version; saving without it")
            if dst.exists():
                dst.unlink()
            save_kwargs.pop("linear", None)
            try:
                doc.save(str(dst), **save_kwargs, deflate_images=True, deflate_fonts=compress_fonts)
            except TypeError:
                doc.save(str(dst), **save_kwargs)
    finally:
        doc.close()
    if not dst.exists():
        raise FileNotFoundError(f"Compression failed: {dst} not created")
    return dst
