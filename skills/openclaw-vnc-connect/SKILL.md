---
name: openclaw-vnc-connect
description: Connect to OpenClaw remote desktops over VNC with secure defaults, including direct LAN connections, SSH tunnel mode, credential collection, troubleshooting black screen/auth errors, and copy-paste-ready commands for Linux/macOS/Windows. Use when users ask to access an OpenClaw desktop, diagnose failed VNC login/session issues, or automate VNC connection steps.
---

# OpenClaw VNC Connect

## Overview
Use this skill to reliably connect to an OpenClaw desktop via VNC, with preference for secure SSH tunneling when the endpoint is not inside a trusted LAN.

## Connection workflow
1. Collect required parameters:
   - `VNC_HOST` (OpenClaw server IP/domain)
   - `VNC_PORT` (default usually `5900`)
   - `DISPLAY_NUM` (if user provides `:1`, port is often `5901`)
   - `VNC_PASSWORD` (or whether cert/SSO is used)
   - Whether SSH is available (`SSH_HOST`, `SSH_USER`, `SSH_PORT`)
2. Decide mode:
   - Prefer **SSH tunnel mode** if exposed over Internet/untrusted network.
   - Use **direct mode** only for trusted internal networks.
3. Generate exact commands using `scripts/connect_vnc.sh`.
4. Tell user how to launch viewer and what to enter.
5. If connection fails, follow `references/troubleshooting.md`.

## Quick command templates

### 1) Direct mode (trusted LAN)
```bash
bash scripts/connect_vnc.sh direct --host 10.0.0.12 --port 5901
```
Then open viewer with one of:
- `10.0.0.12:5901`
- `10.0.0.12:1` (viewer-dependent)

### 2) SSH tunnel mode (recommended)
```bash
bash scripts/connect_vnc.sh tunnel \
  --ssh-user ubuntu \
  --ssh-host openclaw.example.com \
  --ssh-port 22 \
  --remote-vnc-host 127.0.0.1 \
  --remote-vnc-port 5901 \
  --local-port 59011
```
Then connect viewer to:
- `127.0.0.1:59011`

## Client suggestions by OS
- Linux: `tigervnc-viewer`, `remmina`
- macOS: built-in Screen Sharing (`vnc://host:port`) or TigerVNC
- Windows: RealVNC Viewer / TigerVNC Viewer

## Security rules
- Never post raw VNC service directly to public Internet unless strictly required.
- Prefer SSH tunnel + strong SSH authentication.
- Rotate VNC password when sharing temporary access.
- Mask secrets in chat output (`******`).

## Output format for user-facing responses
When assisting users, respond in this order:
1. **你需要提供的参数** (host/port/user/password/tunnel info)
2. **推荐连接方式** (direct or tunnel + reason)
3. **可直接执行的命令**
4. **客户端里要填写的地址**
5. **失败排查下一步**


## Packaging and GitHub submission
- Keep `skills/openclaw-vnc-connect/` as the source of truth in Git.
- Do not commit generated `*.skill` archives to the repository.
- Build the archive only for distribution/upload outside Git when needed.

## Resources
- Use `scripts/connect_vnc.sh` to print ready-to-run commands for direct/tunnel modes.
- Use `references/troubleshooting.md` for auth/black-screen/timeout troubleshooting.
