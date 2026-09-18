import hashlib
import json
import secrets
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
HOST = "0.0.0.0"
PORT = int(__import__("os").environ.get("PORT", "8000"))
USERNAME = "Al3xandre"
PASSWORD_HASH = hashlib.sha256("Reis19223!".encode()).hexdigest()
SESSIONS = set()
LOCK = threading.Lock()


def load_data():
    if not DATA_FILE.exists():
        return {"appointments": []}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"appointments": []}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


class BarberHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def authorized(self):
        token = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        return token in SESSIONS

    def do_OPTIONS(self):
        json_response(self, 204, {})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/appointments":
            appointments = load_data()["appointments"]
            public = [{"date": item["date"], "time": item["time"]} for item in appointments]
            json_response(self, 200, {"appointments": public})
            return
        if path == "/api/barber/appointments":
            if not self.authorized():
                json_response(self, 401, {"error": "Não autorizado"})
                return
            json_response(self, 200, load_data())
            return
        if path == "/api/health":
            json_response(self, 200, {"status": "ok"})
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
        except (json.JSONDecodeError, ValueError):
            json_response(self, 400, {"error": "JSON inválido"})
            return

        if path == "/api/login":
            password_hash = hashlib.sha256(str(payload.get("password", "")).encode()).hexdigest()
            if payload.get("username") != USERNAME or password_hash != PASSWORD_HASH:
                json_response(self, 401, {"error": "Usuário ou senha incorretos"})
                return
            token = secrets.token_urlsafe(32)
            SESSIONS.add(token)
            json_response(self, 200, {"token": token})
            return

        if path == "/api/appointments":
            required = ("date", "time", "service", "name", "phone", "email")
            if any(not str(payload.get(key, "")).strip() for key in required):
                json_response(self, 400, {"error": "Preencha todos os campos"})
                return
            with LOCK:
                data = load_data()
                if any(item["date"] == payload["date"] and item["time"] == payload["time"] for item in data["appointments"]):
                    json_response(self, 409, {"error": "Horário já reservado"})
                    return
                appointment = {"id": secrets.token_hex(8), "createdAt": datetime.now().isoformat(timespec="seconds"), **{key: payload[key].strip() for key in required}}
                data["appointments"].append(appointment)
                save_data(data)
            json_response(self, 201, {"appointment": appointment})
            return

        json_response(self, 404, {"error": "Rota não encontrada"})

    def do_DELETE(self):
        path = urlparse(self.path).path
        if not self.authorized():
            json_response(self, 401, {"error": "Não autorizado"})
            return
        if path.startswith("/api/barber/appointments/"):
            appointment_id = path.rsplit("/", 1)[-1]
            with LOCK:
                data = load_data()
                data["appointments"] = [item for item in data["appointments"] if item["id"] != appointment_id]
                save_data(data)
            json_response(self, 200, {"ok": True})
            return
        json_response(self, 404, {"error": "Rota não encontrada"})


if __name__ == "__main__":
    print(f"Reis Barber em http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), BarberHandler).serve_forever()
