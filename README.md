# agy-mobile-a2a

Universal **Desktop ↔ Android (Termux + Ubuntu)** Antigravity bidirectional **A2A (Agent-to-Agent)** plugin over Tailscale — with **zero Android VPN conflicts** using userspace `tailscaled`.

## Features
- **Bidirectional A2A**: Delegate tasks from Desktop Antigravity to your Android phone's Antigravity agent (`ask_phone.py`), and from your phone back to your Desktop (`pc_agy_bridge.py`).
- **Desktop Session Sync**: Exposes `/api/pc-sessions` and `/api/pc-session/<id>` so mobile Web UIs (like `antigravity-web`) can browse desktop conversation history.
- **Zero VPN Conflict on Android**: Runs `tailscaled --tun=userspace-networking` inside the Termux/Ubuntu container so your existing Android proxy VPN stays active uninterrupted.
- **Standard Antigravity Plugin**: Drop directly into `~/.gemini/config/plugins/agy-mobile-a2a`.

## Quick Start

### 1. Install as an Antigravity Plugin (Desktop)
```bash
git clone https://github.com/misaka-mis/agy-mobile-a2a.git ~/.gemini/config/plugins/agy-mobile-a2a
cd ~/.gemini/config/plugins/agy-mobile-a2a
cp config.example.json config.json
```
Edit `config.json` with your Tailscale IPs (`pc_url`, `phone_url`) and a shared secret `token`, then start the desktop bridge:
```bash
python scripts/pc_agy_bridge.py
```

### 2. Setup on Android (Termux + proot-distro Ubuntu)
Inside Ubuntu (`proot-distro login ubuntu`):
```bash
# Start userspace Tailscale (does not take over Android's VPN slot)
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 --outbound-http-proxy-listen=localhost:1056 &
tailscale up

# Start the phone A2A bridge
export AGY_A2A_TOKEN="your-shared-secret-token"
python3 phone_agy_bridge.py &
```

### 3. Verify Connectivity
From Desktop:
```bash
python scripts/ask_phone.py ping
python scripts/ask_phone.py "List files in /sdcard/Download"
```

## Security
- All endpoints require `Authorization: Bearer <token>`.
- `config.json` and `bridge_token.txt` are git-ignored by default — never commit your real tokens or private IPs.
