import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

READY = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global READY

        if self.path == "/healthz":
            self.send_json(200, {"status": "alive", "pod": socket.gethostname()})
        elif self.path == "/ready":
            self.send_json(200 if READY else 503, {"ready": READY, "pod": socket.gethostname()})
        elif self.path == "/toggle-readiness":
            READY = not READY
            self.send_json(200, {"ready": READY, "pod": socket.gethostname()})
        elif self.path == "/inventory":
            self.send_json(200, {
                "service": "inventory",
                "pod": socket.gethostname(),
                "items": [{"sku": "K8S-101", "name": "Kubernetes mug", "quantity": 12}],
            })
        else:
            self.send_json(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Inventory listening on :{port} as {socket.gethostname()}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
