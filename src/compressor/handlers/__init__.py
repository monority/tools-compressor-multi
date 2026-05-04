"""
Auto-detect available handlers and list supported formats.
"""
SUPPORTED = {}

def _register():
    from compressor.core import MIME_MAP
    SUPPORTED.update(MIME_MAP)

_register()
