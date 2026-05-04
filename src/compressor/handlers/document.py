from pathlib import Path
from typing import Any
import zipfile
import tempfile
import os

def compress_document(src: Path, dst: Path, opts: dict[str, Any]) -> Path:
    """Compress Office documents by optimizing internal images."""
    compress_imgs = opts.get("compress_images", True)
    img_quality = opts.get("image_quality", 50)
    remove_meta = opts.get("remove_metadata", False)
    suffix = src.suffix.lower()
    if suffix == ".docx":
        return _compress_docx(src, dst, compress_imgs, img_quality, remove_meta)
    elif suffix == ".xlsx":
        return _compress_xlsx(src, dst, compress_imgs, img_quality, remove_meta)
    raise ValueError(f"Unsupported document format: {suffix}")

def _compress_docx(src, dst, compress_imgs, quality, remove_meta):
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")
    out = dst.with_suffix(".docx") if dst.suffix != ".docx" else dst
    doc = Document(str(src))
    if remove_meta:
        core_props = doc.core_properties
        for prop in ['author', 'title', 'subject', 'keywords', 'comments']:
            try:
                setattr(core_props, prop, '')
            except:
                pass
    if compress_imgs and quality < 80:
        try:
            from PIL import Image
            import io
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    img_part = rel.target_part
                    img_bytes = img_part.blob
                    try:
                        img = Image.open(io.BytesIO(img_bytes))
                        buf = io.BytesIO()
                        img.save(buf, format=img.format or 'JPEG', quality=quality, optimize=True)
                        img_part._blob = buf.getvalue()
                    except:
                        pass
        except ImportError:
            pass
    doc.save(str(out))
    return out

def _compress_xlsx(src, dst, compress_imgs, quality, remove_meta):
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    out = dst.with_suffix(".xlsx") if dst.suffix != ".xlsx" else dst
    wb = load_workbook(str(src))
    if remove_meta:
        wb.properties.creator = ''
        wb.properties.title = ''
    if compress_imgs and quality < 80:
        try:
            from PIL import Image
            import io
            for sheet in wb.worksheets:
                for img in sheet._images:
                    try:
                        img_bytes = img.ref
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        buf = io.BytesIO()
                        pil_img.save(buf, format='JPEG', quality=quality, optimize=True)
                    except:
                        pass
        except ImportError:
            pass
    wb.save(str(out))
    return out
