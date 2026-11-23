#!/usr/bin/env python3
"""Universal Android (Termux + Ubuntu) Antigravity A2A Bridge Server."""
import http.server
import json
import os
import shutil
import socket
import subprocess

PORT = int(os.environ.get("PHONE_BRIDGE_PORT", "18765"))
API_TOKEN = os.environ.get("AGY_A2A_TOKEN", "").strip()
AGY_BIN = os.environ.get("AGY_BIN") or shutil.which("agy") or "/root/.local/bin/agy"

class PhoneBridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[Phone-Bridge] {self.address_string()} - {format % args}", flush=True)

    def _auth_ok(self):
        return bool(API_TOKEN) and self.headers.get("Authorization", "") == f"Bearer {API_TOKEN}"

    def _json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._auth_ok():
            self._json({"error": "Unauthorized"}, 401)
            return
        if self.path == "/api/ping":
            self._json({"ok": True, "host": socket.gethostname(), "device": "phone", "agy": os.path.exists(AGY_BIN)})
        else:
            self._json({"error": "Not found"}, 404)

    def do_POST(self):
        if not self._auth_ok():
            self._json({"error": "Unauthorized"}, 401)
            return
        if self.path != "/api/ask":
            self._json({"error": "Not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        prompt = (body.get("prompt") or "").strip()
        cwd = body.get("cwd") or "/root"
        model = (body.get("model") or "").strip()
        if not prompt:
            self._json({"error": "prompt is required"}, 400)
            return
        if not os.path.isdir(cwd):
            cwd = "/root"
        cmd = [AGY_BIN, "--dangerously-skip-permissions"]
        if model:
            cmd += ["--model", model]
        cmd += ["-p", prompt]
        try:
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            self._json({
                "ok": res.returncode == 0,
                "returncode": res.returncode,
                "output": (res.stdout or "") + (("\n" + res.stderr) if res.stderr else ""),
            })
        except subprocess.TimeoutExpired:
            self._json({"ok": False, "error": "Execution timed out (300s)"}, 504)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

class ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    if not API_TOKEN:
        raise SystemExit("Please set AGY_A2A_TOKEN environment variable before starting.")
    print(f"[Phone-Bridge] Listening on http://0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), PhoneBridgeHandler).serve_forever()
