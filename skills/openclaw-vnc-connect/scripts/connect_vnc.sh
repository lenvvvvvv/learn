#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Generate OpenClaw VNC connection commands.

Usage:
  connect_vnc.sh direct --host <vnc-host> --port <vnc-port>
  connect_vnc.sh tunnel --ssh-user <user> --ssh-host <host> [--ssh-port 22] \
      --remote-vnc-host <host> --remote-vnc-port <port> --local-port <port>

Examples:
  connect_vnc.sh direct --host 10.0.0.12 --port 5901
  connect_vnc.sh tunnel --ssh-user ubuntu --ssh-host demo.example.com \
      --remote-vnc-host 127.0.0.1 --remote-vnc-port 5901 --local-port 59011
USAGE
}

require_arg() {
  local name="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[ERROR] Missing required argument: $name" >&2
    usage
    exit 1
  fi
}

mode="${1:-}"
if [[ -z "$mode" || "$mode" == "-h" || "$mode" == "--help" ]]; then
  usage
  exit 0
fi
shift || true

case "$mode" in
  direct)
    host=""
    port=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --host)
          host="${2:-}"
          shift 2
          ;;
        --port)
          port="${2:-}"
          shift 2
          ;;
        *)
          echo "[ERROR] Unknown argument for direct mode: $1" >&2
          usage
          exit 1
          ;;
      esac
    done

    require_arg "--host" "$host"
    require_arg "--port" "$port"

    echo "# Direct VNC mode (trusted LAN only)"
    echo "# In your VNC client, connect to: ${host}:${port}"
    echo "vnc://$host:$port"
    ;;

  tunnel)
    ssh_user=""
    ssh_host=""
    ssh_port="22"
    remote_vnc_host=""
    remote_vnc_port=""
    local_port=""

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --ssh-user)
          ssh_user="${2:-}"
          shift 2
          ;;
        --ssh-host)
          ssh_host="${2:-}"
          shift 2
          ;;
        --ssh-port)
          ssh_port="${2:-}"
          shift 2
          ;;
        --remote-vnc-host)
          remote_vnc_host="${2:-}"
          shift 2
          ;;
        --remote-vnc-port)
          remote_vnc_port="${2:-}"
          shift 2
          ;;
        --local-port)
          local_port="${2:-}"
          shift 2
          ;;
        *)
          echo "[ERROR] Unknown argument for tunnel mode: $1" >&2
          usage
          exit 1
          ;;
      esac
    done

    require_arg "--ssh-user" "$ssh_user"
    require_arg "--ssh-host" "$ssh_host"
    require_arg "--remote-vnc-host" "$remote_vnc_host"
    require_arg "--remote-vnc-port" "$remote_vnc_port"
    require_arg "--local-port" "$local_port"

    echo "# SSH tunnel mode (recommended)"
    echo "ssh -N -L ${local_port}:${remote_vnc_host}:${remote_vnc_port} -p ${ssh_port} ${ssh_user}@${ssh_host}"
    echo "# Then in your VNC client connect to: 127.0.0.1:${local_port}"
    echo "vnc://127.0.0.1:${local_port}"
    ;;

  *)
    echo "[ERROR] Unknown mode: $mode" >&2
    usage
    exit 1
    ;;
esac
