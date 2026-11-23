#!/usr/bin/env python3
"""Universal Desktop Antigravity A2A Bridge Server."""
import http.server
import json
import os
import secrets
import shutil
import socket
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_token.txt")

def load_config():
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

CFG = load_config()
PORT = int(os.environ.get("PC_BRIDGE_PORT") or CFG.get("port") or 18765)
AGY_BIN = (
    os.environ.get("AGY_BIN")
    or CFG.get("agy_bin")
    or shutil.which("agy")
    or os.path.expanduser(r"~\AppData\Local\agy\bin\agy.exe")
)
BRAIN_DIR = (
    os.environ.get("AGY_BRAIN_DIR")
    or CFG.get("brain_dir")
    or os.path.expanduser(os.path.join("~", ".gemini", "antigravity", "brain"))
)

def load_token():
    t = (os.environ.get("AGY_A2A_TOKEN") or CFG.get("token") or "").strip()
    if t and t != "REPLACE_WITH_SHARED_SECRET_TOKEN":
        return t
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    t = secrets.token_urlsafe(24)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(t)
    print(f"[PC-Bridge] Generated new token in {TOKEN_FILE}", flush=True)
    return t

API_TOKEN = load_token()

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[PC-Bridge] {self.address_string()} - {format % args}", flush=True)

    def _auth_ok(self):
        return self.headers.get("Authorization", "") == f"Bearer {API_TOKEN}"

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
            self._json({"ok": True, "host": socket.gethostname(), "device": "pc", "agy": os.path.exists(AGY_BIN)})
        elif self.path == "/api/pc-sessions":
            sessions = []
            if os.path.isdir(BRAIN_DIR):
                for name in os.listdir(BRAIN_DIR):
                    tpath = os.path.join(BRAIN_DIR, name, ".system_generated", "logs", "transcript.jsonl")
                    if not os.path.isfile(tpath):
                        continue
                    mtime = os.path.getmtime(tpath)
                    title = name[:8]
                    try:
                        with open(tpath, "r", encoding="utf-8", errors="replace") as f:
                            for line in f:
                                obj = json.loads(line)
                                if obj.get("type") == "USER_INPUT" and (obj.get("content") or "").strip():
                                    title = obj["content"].strip().replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").replace("\n", " ").strip()[:40]
                                    break
                    except Exception:
                        pass
                    sessions.append({"id": name, "title": title, "updated_at": int(mtime), "source": "pc"})
                sessions.sort(key=lambda x: x["updated_at"], reverse=True)
            self._json({"sessions": sessions[:30]})
        elif self.path.startswith("/api/pc-session/"):
            sid = self.path.split("/api/pc-session/", 1)[1].strip("/")
            tpath = os.path.join(BRAIN_DIR, sid, ".system_generated", "logs", "transcript.jsonl")
            if not os.path.isfile(tpath):
                self._json({"error": "Session not found"}, 404)
                return
            msgs = []
            try:
                with open(tpath, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        obj = json.loads(line)
                        t = obj.get("type")
                        c = (obj.get("content") or "").strip()
                        if t == "USER_INPUT" and c:
                            msgs.append({"role": "user", "content": c})
                        elif t == "PLANNER_RESPONSE" and c:
                            msgs.append({"role": "assistant", "content": c})
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            self._json({"id": sid, "messages": msgs})
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
        cwd = body.get("cwd") or os.path.expanduser("~")
        model = (body.get("model") or "").strip()
        if not prompt:
            self._json({"error": "prompt is required"}, 400)
            return
        if not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")

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
    print(f"[PC-Bridge] Listening on http://0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), BridgeHandler).serve_forever()
