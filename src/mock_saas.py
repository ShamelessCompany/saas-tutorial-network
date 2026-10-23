"""Local mock SaaS server for deterministic offline demos and testing."""
import http.server
import socketserver
import threading
from pathlib import Path

class QuietSimpleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence routine HTTP access logs
        pass

class MockSaaSServer:
    def __init__(self, directory: Path | str, host: str = "127.0.0.1", port: int = 8765):
        self.directory = str(Path(directory).resolve())
        self.host = host
        self.port = port
        self.server: socketserver.TCPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> str:
        handler = lambda *args, **kwargs: QuietSimpleHandler(
            *args, directory=self.directory, **kwargs
        )
        self.server = socketserver.TCPServer((self.host, self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://{self.host}:{self.port}"

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
