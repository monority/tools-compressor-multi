from pathlib import Path

from compressor.core import compress_file


def sample_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "test_samples" / name


def test_real_text_sample_compress(tmp_path):
    src = sample_path("test.txt")
    result = compress_file(src, tmp_path / "sample.txt.gz")
    assert result["success"] is True
    assert Path(result["dst"]).exists()
    assert result["format"] == "generic"


def test_real_image_sample_compress_to_webp(tmp_path):
    src = sample_path("test.jpg")
    result = compress_file(src, tmp_path / "sample.webp", **{"format": "webp"})
    assert result["success"] is True
    assert Path(result["dst"]).exists()
    assert Path(result["dst"]).suffix == ".webp"


def test_real_pdf_sample_compress(tmp_path):
    src = sample_path("test.pdf")
    result = compress_file(src, tmp_path / "sample.pdf")
    assert result["success"] is True
    assert Path(result["dst"]).exists()
    assert result["format"] == "pdf"
