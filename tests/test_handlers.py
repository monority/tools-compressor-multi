import pytest
from pathlib import Path
import tarfile

def test_pdf_compress(tmp_path):
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    src = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World")
    doc.save(str(src))
    doc.close()
    from compressor.handlers.pdf import compress_pdf
    dst = tmp_path / "out.pdf"
    result = compress_pdf(src, dst, {"dpi": 72, "quality": "/screen"})
    assert result.exists()
    assert result.stat().st_size > 0


def test_pdf_compress_ignores_unsupported_linearization(tmp_path):
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    src = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World")
    doc.save(str(src))
    doc.close()
    from compressor.handlers.pdf import compress_pdf
    dst = tmp_path / "out.pdf"
    result = compress_pdf(src, dst, {"dpi": 72, "linearize": True})
    assert result.exists()
    assert result.stat().st_size > 0

def test_image_compress(tmp_path):
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")
    src = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(src, quality=95)
    from compressor.handlers.image import compress_image
    dst = tmp_path / "out.jpg"
    result = compress_image(src, dst, {"jpg_quality": 50})
    assert result.exists()
    assert result.stat().st_size > 0

def test_archive_compress(tmp_path):
    src = tmp_path / "test.txt"
    src.write_text("x" * 1000)
    from compressor.handlers.archive import compress_archive
    result = compress_archive(src, tmp_path / "out.zip", {"format": "zip", "level": 6})
    assert result.exists()
    assert result.stat().st_size < src.stat().st_size


def test_archive_tar_gz_contains_file(tmp_path):
    src = tmp_path / "test.txt"
    src.write_text("hello tar")
    from compressor.handlers.archive import compress_archive
    result = compress_archive(src, tmp_path / "out.tar.gz", {"format": "tar.gz", "level": 6})
    assert result.exists()
    with tarfile.open(result, "r:gz") as archive:
        names = archive.getnames()
    assert names == ["test.txt"]
