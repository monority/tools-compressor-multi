<h1 align="center">
Compressor-Multi
</h1>


<p align="center">
  <img src="./logo-compressor.webp" width="200"/>
</p>

Multi-format file compressor with dynamic quality presets. Pure Python, zero external tools required.

## Features
- **PDF Priority**: Downsampling, font compression, PDF/A conversion via PyMuPDF
- **Images**: JPG/PNG/WebP/AVIF with quality adjustment and format conversion
- **Archives**: ZIP/7Z/TAR with compression levels
- **Documents**: DOCX/XLSX internal image compression
- **Interactive Menu**: `compress menu` for guided file selection
- **Batch Processing**: Concurrent workers, recursive directory scan
- **Reports**: Compression ratios, time, JSON export

## Interactive Menu
```bash
compress menu
```
Options:
1. Select and compress a single file
2. Compress all files in input directory
3. Compress files in a specific directory
4. Show supported formats
5. Exit

## Installation (Windows)
```powershell
# Prerequisite: Python 3.10+
cd C:\Users\ddva\Desktop\compressor-multi
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
```

## Usage
```bash
# Interactive menu mode
compress menu

# Compress single file (interactive prompts)
compress file.pdf

# With flags
compress file.pdf -q best -o output.pdf

# Batch directory
compress ./docs -b -q balanced -w 4

# Force interactive mode
compress --interactive
```

## Quality Levels
- `fast`: Quick compression, larger files
- `balanced`: Default tradeoff
- `best`: Maximum compression, slower
- `custom`: Define your own parameters

## Limitations
- No video/audio re-encoding (requires FFmpeg)
- No HEIC without `pillow-heif` addon
- PDF compression uses PyMuPDF (no Ghostscript needed)

## CI/CD
GitHub Actions runs tests on Python 3.10-3.12 with coverage reporting.
