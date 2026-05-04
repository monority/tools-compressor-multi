import pytest
from pathlib import Path
import tempfile
from compressor.core import detect_format, file_hash, compress_file
from compressor.config import load_config

def test_load_config():
    cfg = load_config()
    assert "presets" in cfg
    assert "pdf" in cfg["presets"]

def test_detect_format_pdf(tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")
    fmt = detect_format(pdf_file)
    assert fmt == "pdf"

def test_detect_format_image(tmp_path):
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(b"\xff\xd8\xff\xe0" + b"fake jpeg")
    fmt = detect_format(img_file)
    assert fmt == "image"

def test_file_hash(tmp_path):
    f = tmp_path / "hash_test.txt"
    f.write_text("hello")
    h = file_hash(f)
    assert len(h) == 64  # SHA256 hex length

def test_compress_file_unsupported(tmp_path):
    """Test that unsupported formats fallback to gzip compression."""
    bad = tmp_path / "test.xyz"
    bad.write_text("data")
    result = compress_file(bad)
    # Now unsupported formats get gzipped as fallback
    assert result["success"] is True
    assert result["format"] == "generic"
    assert Path(result["dst"]).exists()
