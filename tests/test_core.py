import pytest
from pathlib import Path
from compressor.core import detect_format, file_hash, compress_file, resolve_output_path
from compressor.config import load_config
from compressor.report import export_json
import json
import compressor.core as core

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


def test_export_json(tmp_path):
    out = tmp_path / "report.json"
    export_json([{"src": "a", "success": True}], out)
    data = json.loads(out.read_text())
    assert data[0]["src"] == "a"


def test_compress_batch_preserves_tree(tmp_path):
    from compressor.core import compress_batch

    root = tmp_path / "input"
    nested = root / "sub"
    nested.mkdir(parents=True)
    src = nested / "test.xyz"
    src.write_text("data")

    output_dir = tmp_path / "output"
    results = compress_batch([src], output_dir=output_dir, root_dir=root)
    assert results[0]["success"] is True
    assert Path(results[0]["dst"]) == output_dir / "sub" / "test.xyz.gz"


def test_resolve_output_path_preserves_tree(tmp_path):
    root = tmp_path / "input"
    src = root / "deep" / "file.txt"
    out = tmp_path / "out"
    resolved = resolve_output_path(src, out, root)
    assert resolved == out / "deep" / "file.txt"


def test_compress_file_fails_when_handler_creates_no_output(tmp_path, monkeypatch):
    src = tmp_path / "test.pdf"
    src.write_bytes(b"%PDF-1.4 fake pdf content")

    monkeypatch.setattr(core, "detect_format", lambda _path: "pdf")
    monkeypatch.setattr(core, "get_handler", lambda _fmt: lambda _src, dst, _opts: dst)
    monkeypatch.setattr(core, "load_config", lambda _path: {})
    monkeypatch.setattr(core, "get_preset", lambda _config, _fmt, _quality: {})

    result = core.compress_file(src, tmp_path / "out.pdf")
    assert result["success"] is False
    assert "missing output" in result["error"].lower()
