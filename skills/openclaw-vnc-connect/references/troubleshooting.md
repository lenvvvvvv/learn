# OpenClaw VNC Troubleshooting

## 1) Connection timeout / refused
- Verify OpenClaw service is running and listening on expected VNC port (`5900 + display`).
- Check firewall/security group allows path (or use SSH tunnel instead).
- Confirm host resolution: try IP first.

## 2) Authentication failed
- Re-enter password carefully (many viewers are case-sensitive and do not show characters).
- Confirm server-side VNC password was recently changed.
- If using SSO/enterprise gateway, verify gateway login first.

## 3) Black screen after login
- Remote desktop session may not be initialized. Restart desktop session (`xfce`, `gnome`, or OpenClaw desktop service).
- Check server has free memory/CPU.
- Try reconnecting with reduced color depth in viewer.

## 4) Keyboard/mouse lag
- Reduce image quality/compression level.
- Prefer LAN or closer region.
- Use SSH tunnel with compression if network is unstable.

## 5) Clipboard/file transfer not working
- Not all VNC clients support bi-directional clipboard/file transfer equally.
- Switch to TigerVNC or RealVNC and verify feature toggle is enabled.
