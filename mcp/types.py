"""Stub types for mcp package used by mcp-servers tests.

These are minimal placeholders to satisfy imports during local testing.
"""
from typing import Any, Dict, List, Optional


class Tool:
    def __init__(self, name: str = "stub", description: str = "", inputSchema: Any = None, annotations: Any = None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema
        self.annotations = annotations


class ToolAnnotations:
    def __init__(self, readOnlyHint: bool = False, destructiveHint: bool = False,
                 idempotentHint: bool = False, openWorldHint: bool = False):
        self.readOnlyHint = readOnlyHint
        self.destructiveHint = destructiveHint
        self.idempotentHint = idempotentHint
        self.openWorldHint = openWorldHint


class TextContent:
    def __init__(self, type: str = "text", text: str = ""):
        self.type = type
        self.text = text


class ImageContent:
    def __init__(self, url: str = ""):
        self.url = url


class EmbeddedResource:
    def __init__(self, data: Any = None):
        self.data = data


class ErrorData:
    def __init__(self, code: int = 0, message: str = ""):
        self.code = code
        self.message = message


class PromptArgument:
    def __init__(self, name: str, description: str = "", required: bool = False):
        self.name = name
        self.description = description
        self.required = required


class Prompt:
    def __init__(self, name: str, description: str = "", arguments: Optional[List[PromptArgument]] = None):
        self.name = name
        self.description = description
        self.arguments = arguments or []


class PromptMessage:
    def __init__(self, role: str = "user", content: Any = None):
        self.role = role
        self.content = content


class GetPromptResult:
    def __init__(self, description: str = "", messages: Optional[List[PromptMessage]] = None):
        self.description = description
        self.messages = messages or []


class RootEntry:
    def __init__(self, uri: Any):
        self.uri = uri


class ListRootsResult:
    def __init__(self, roots: Optional[List[RootEntry]] = None):
        self.roots = roots or []


class RootsCapability:
    def __init__(self):
        pass


class ClientCapabilities:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

__all__ = [
    "Tool", "ToolAnnotations", "TextContent", "ImageContent",
    "EmbeddedResource", "ErrorData", "PromptArgument", "Prompt",
    "PromptMessage", "GetPromptResult", "RootEntry", "ListRootsResult",
    "RootsCapability", "ClientCapabilities", "INVALID_PARAMS", "INTERNAL_ERROR",
]
