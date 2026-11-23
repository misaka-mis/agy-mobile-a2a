#!/usr/bin/env python3
"""Universal Desktop -> Android Antigravity A2A Client."""
import json
import os
import sys
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_token.txt")

CFG = {}
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CFG = json.load(f)

PHONE_URL = (os.environ.get("AGY_PHONE_URL") or CFG.get("phone_url") or "").rstrip("/")
TOKEN = (os.environ.get("AGY_A2A_TOKEN") or CFG.get("token") or "").strip()
if (not TOKEN or TOKEN == "REPLACE_WITH_SHARED_SECRET_TOKEN") and os.path.isfile(TOKEN_FILE):
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        TOKEN = f.read().strip()

def req(path, payload=None):
    if not PHONE_URL:
        raise RuntimeError("Set phone_url in config.json or AGY_PHONE_URL env var.")
    if not TOKEN:
        raise RuntimeError("Set token in config.json, AGY_A2A_TOKEN env var, or scripts/bridge_token.txt.")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(PHONE_URL + path, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(r, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "ping":
        print(json.dumps(req("/api/ping"), ensure_ascii=False, indent=2))
    else:
        prompt = " ".join(sys.argv[1:])
        print(json.dumps(req("/api/ask", {"prompt": prompt}), ensure_ascii=False, indent=2))
