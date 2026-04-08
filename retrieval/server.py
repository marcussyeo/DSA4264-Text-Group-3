from __future__ import annotations

import json
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .index import MODEL_NAME
from .search import SearchService


class SearchHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "NUSRetrievalHTTP/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(
                status=HTTPStatus.OK,
                payload={"ok": True, "service": "retrieval"},
            )
            return
        self._send_json(
            status=HTTPStatus.NOT_FOUND,
            payload={"error": "Not found"},
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        try:
            payload = self._read_json()
        except ValueError as error:
            self._send_json(status=HTTPStatus.BAD_REQUEST, payload={"error": str(error)})
            return

        try:
            query = str(payload.get("query", "")).strip()
            top_k = int(payload.get("topK", 8))
            service = self.server.service

            if path == "/search/jobs":
                response = service.find_jobs(query=query, top_k=top_k)
            elif path == "/search/modules":
                response = service.find_modules(query=query, top_k=top_k)
            else:
                self._send_json(status=HTTPStatus.NOT_FOUND, payload={"error": "Not found"})
                return
        except FileNotFoundError as error:
            self._send_json(status=HTTPStatus.SERVICE_UNAVAILABLE, payload={"error": str(error)})
            return
        except Exception as error:  # pragma: no cover - defensive server boundary
            self._send_json(status=HTTPStatus.INTERNAL_SERVER_ERROR, payload={"error": str(error)})
            return

        self._send_json(status=HTTPStatus.OK, payload=response.to_dict())

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _read_json(self) -> dict:
        length = self.headers.get("Content-Length")
        if length is None:
            raise ValueError("Missing Content-Length header.")
        try:
            body = self.rfile.read(int(length))
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON body.") from error

    def _send_common_headers(self) -> None:
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self._send_common_headers()
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class SearchHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, service: SearchService) -> None:
        super().__init__(server_address, SearchHTTPRequestHandler)
        self.service = service


@lru_cache(maxsize=None)
def get_service(cache_dir: str, model_name: str) -> SearchService:
    return SearchService(cache_dir=Path(cache_dir), model_name=model_name)


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    cache_dir: str | Path = Path("notebooks/cache"),
    model_name: str = MODEL_NAME,
) -> None:
    service = get_service(str(cache_dir), model_name)
    httpd = SearchHTTPServer((host, port), service)
    print(f"Retrieval API listening on http://{host}:{port}")
    httpd.serve_forever()
