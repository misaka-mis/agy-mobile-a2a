---
name: agy-mobile-a2a
description: Universal Desktop <-> Android (Termux/Ubuntu) Antigravity bidirectional A2A bridge skill. Use when delegating tasks to a paired mobile Antigravity agent, checking connectivity, or starting the local PC A2A bridge.
---

# Antigravity Mobile A2A

Bidirectional Agent-to-Agent (A2A) bridge between Desktop Antigravity and Android (Termux + Ubuntu) Antigravity over Tailscale (supporting userspace Tailscale on Android so existing proxy VPNs remain uninterrupted).

## Setup
1. Copy `config.example.json` to `config.json` in the plugin root and fill in your `phone_url`, `pc_url`, and shared `token` (or set `AGY_PHONE_URL` / `AGY_A2A_TOKEN` environment variables).
2. Run `scripts/pc_agy_bridge.py` on the desktop and `scripts/phone_agy_bridge.py` inside the Android Ubuntu container.

## Common Operations

### 1. Ping Mobile Agent
```bash
python scripts/ask_phone.py ping
```

### 2. Delegate a Task to Mobile Agent
```bash
python scripts/ask_phone.py "Your task description for the mobile agent"
```

### 3. Start Desktop A2A Bridge Server
```bash
python scripts/pc_agy_bridge.py
```

## Guardrails
- Never print or expose the raw shared token from `config.json` or `bridge_token.txt` in chat responses or logs.
- If `ask_phone.py ping` times out, check `tailscale status` and ensure the phone's `phone_agy_bridge.py` and userspace `tailscaled` are running.
