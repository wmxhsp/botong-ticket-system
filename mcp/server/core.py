"""Core Server implementation for stub package."""

class Server:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return None

    def stop(self):
        return None

class ServerSession:
    pass
