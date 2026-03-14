# OpenClaw VNC 技能使用说明（中文）

本文说明如何在 OpenClaw 中使用 `openclaw-vnc-connect` 技能，快速生成 VNC 连接步骤（直连或 SSH 隧道）。

## 1. 这个技能能做什么
- 帮你整理连接 OpenClaw 桌面需要的参数。
- 自动给出推荐连接方式（优先 SSH 隧道）。
- 生成可以直接复制执行的命令。
- 提供常见故障排查思路（黑屏、认证失败、超时等）。

## 2. 在 OpenClaw 中如何触发
在 OpenClaw 对话中，输入类似下面的话：
- `帮我连接 OpenClaw 的 VNC 桌面`
- `给我一套 VNC SSH 隧道连接命令`
- `VNC 黑屏了，帮我排查`

建议明确补充参数：
- VNC 主机/IP
- VNC 端口（如 5901）
- SSH 主机/用户名/端口（如果走隧道）

## 3. 推荐交互模板（可直接复制到 OpenClaw）
```text
请用 openclaw-vnc-connect 技能帮我生成连接命令。
参数如下：
- VNC_HOST=10.0.0.12
- VNC_PORT=5901
- SSH_HOST=openclaw.example.com
- SSH_USER=ubuntu
- SSH_PORT=22
请优先用 SSH 隧道模式输出：
1) 我还缺少哪些参数
2) 可直接执行的命令
3) VNC 客户端里要填的地址
4) 失败排查下一步
```

## 4. 两种连接方式

### 4.1 直连模式（仅内网可信场景）
```bash
bash skills/openclaw-vnc-connect/scripts/connect_vnc.sh direct --host 10.0.0.12 --port 5901
```
VNC 客户端连接地址：
- `10.0.0.12:5901`
- 或 `vnc://10.0.0.12:5901`

### 4.2 SSH 隧道模式（推荐）
```bash
bash skills/openclaw-vnc-connect/scripts/connect_vnc.sh tunnel \
  --ssh-user ubuntu \
  --ssh-host openclaw.example.com \
  --ssh-port 22 \
  --remote-vnc-host 127.0.0.1 \
  --remote-vnc-port 5901 \
  --local-port 59011
```
先保持 SSH 隧道命令运行，再在 VNC 客户端连接：
- `127.0.0.1:59011`
- 或 `vnc://127.0.0.1:59011`

## 5. 常见问题
- **连接超时/拒绝**：确认端口监听、防火墙和地址是否正确。
- **认证失败**：确认 VNC 密码是否更新、大小写是否正确。
- **登录后黑屏**：检查远程桌面会话是否启动，必要时重启桌面服务。

详细排查见：`skills/openclaw-vnc-connect/references/troubleshooting.md`

## 6. 安全建议
- 不要将 VNC 端口直接暴露到公网。
- 优先使用 SSH 隧道 + 强口令/密钥认证。
- 临时共享后及时修改 VNC 密码。
