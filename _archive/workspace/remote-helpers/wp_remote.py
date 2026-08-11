import os, sys, json, shlex
from pathlib import Path

ENV_PATH = Path(__file__).parents[2] / ".env"

env_vars = {}
with open(ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env_vars[k.strip()] = v.strip().strip("'\"")

host = env_vars.get("REMOTE_SSH_HOST")
user = env_vars.get("REMOTE_SSH_USER")
port = int(env_vars.get("REMOTE_SSH_PORT", "22"))
wp_path = env_vars.get("REMOTE_WP_PATH")
passphrase = env_vars.get("ADMIN_PASSWORD", "")

if not host or not user or not wp_path:
    print("[ERROR] Missing REMOTE_SSH_HOST / USER / WP_PATH in .env", file=sys.stderr)
    sys.exit(1)

KEY_SOURCE = Path(__file__).parents[2] / "info-server.txt"

key_text = []
with open(KEY_SOURCE) as f:
    lines = f.readlines()
    in_key = False
    for line in lines:
        if line.strip() == "-----BEGIN OPENSSH PRIVATE KEY-----":
            in_key = True
        if in_key:
            key_text.append(line.rstrip("\n"))
        if line.strip() == "-----END OPENSSH PRIVATE KEY-----" and in_key:
            break

key_pem = "\n".join(key_text)

from io import StringIO
import paramiko

try:
    pkey = paramiko.Ed25519Key.from_private_key(StringIO(key_pem), password=passphrase)
except paramiko.SSHException as e:
    print(f"[ERROR] Failed to load SSH key: {e}", file=sys.stderr)
    sys.exit(1)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(host, port=port, username=user, pkey=pkey, timeout=15)
except Exception as e:
    print(f"[ERROR] SSH connection failed: {e}", file=sys.stderr)
    sys.exit(1)

cmd = shlex.join(sys.argv[1:]) if len(sys.argv) > 1 else "menu list"
wp_cmd = f"wp --path={wp_path} {cmd}"

try:
    _, stdout, stderr = client.exec_command(wp_cmd, timeout=30)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if exit_code == 0:
        print(out)
    else:
        print(err or out, file=sys.stderr)
        sys.exit(exit_code)
except Exception as e:
    print(f"[ERROR] Command failed: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    client.close()
