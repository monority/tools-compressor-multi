from pathlib import Path

import compressor.cli as cli


def test_compress_file_uses_output_path(tmp_path, monkeypatch):
    src = tmp_path / "file.txt"
    src.write_text("hello")
    output = tmp_path / "out.txt"
    seen = {}

    monkeypatch.setattr(cli, "compress_file", lambda *args, **kwargs: seen.update(dst=args[1]) or {"success": True})
    monkeypatch.setattr(cli, "print_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "write_report", lambda *args, **kwargs: None)

    cli.compress_impl(src, output=output)

    assert seen["dst"] == output


def test_compress_dir_uses_output_directory_and_root(tmp_path, monkeypatch):
    root = tmp_path / "input"
    nested = root / "sub"
    nested.mkdir(parents=True)
    src = nested / "file.txt"
    src.write_text("hello")
    output = tmp_path / "out"
    seen = {}

    monkeypatch.setattr(cli, "get_files_sorted", lambda path, recursive=False: [src])
    monkeypatch.setattr(cli, "compress_batch", lambda files, quality, workers, **kwargs: seen.update(kwargs) or [{"success": True, "dst": str(output / "sub" / "file.txt")}])
    monkeypatch.setattr(cli, "print_batch_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "write_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli.console, "print", lambda *args, **kwargs: None)

    cli.compress_impl(root, output=output, batch=True)

    assert seen["output_dir"] == output
    assert seen["root_dir"] == root


def test_compress_writes_report_json(tmp_path, monkeypatch):
    src = tmp_path / "file.txt"
    src.write_text("hello")
    report = tmp_path / "reports" / "out.json"
    seen = {}

    monkeypatch.setattr(cli, "compress_file", lambda *args, **kwargs: {"success": True, "dst": str(args[1]), "src": str(args[0])})
    monkeypatch.setattr(cli, "print_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "write_report", lambda report_json, results: seen.update(report_json=report_json, results=results))

    cli.compress_impl(src, output=tmp_path / "out.txt", report_json=report)

    assert seen["report_json"] == report
    assert seen["results"][0]["src"] == str(src)
