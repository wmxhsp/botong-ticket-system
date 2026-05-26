"""Stub exceptions for mcp.shared"""

class McpError(Exception):
    """Generic MCP error for tests

    If constructed with an `ErrorData`-like object (has `.message`), the
    string representation will use that message so tests can assert on it.
    """
    def __init__(self, error=None):
        super().__init__(error)
        self.error = error

    def __str__(self):
        if hasattr(self.error, "message") and self.error.message:
            return str(self.error.message)
        return super().__str__()
