"""
Local stub package for `mcp` to satisfy imports during tests.
This is a minimal placeholder — replace with real package if available.
"""
__all__ = ["server", "shared", "types"]

__version__ = "0.0.0-stub"

try:
    # expose a simple attribute to indicate stub
    STUB = True
except Exception:
    STUB = True
