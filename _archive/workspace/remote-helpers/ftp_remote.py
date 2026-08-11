import os, sys, ftplib, socket
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

host = env_vars.get("REMOTE_FTP_HOST")
user = env_vars.get("REMOTE_FTP_USER")
passwd = env_vars.get("REMOTE_FTP_PASSWORD")
port_str = env_vars.get("REMOTE_FTP_PORT", "21")

try:
    port = int(port_str)
except ValueError:
    port = 21

if not host or not user or not passwd:
    print("[ERROR] Missing REMOTE_FTP_HOST / USER / PASSWORD in .env")
    sys.exit(1)

remote_dir = sys.argv[1] if len(sys.argv) > 1 else "/"

try:
    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=15)
    ftp.login(user, passwd)
except (socket.error, ftplib.all_errors) as e:
    print(f"[FTP ERROR] {e}")
    sys.exit(1)

try:
    ftp.cwd(remote_dir)
except ftplib.error_perm as e:
    print(f"[FTP ERROR] Cannot cd to '{remote_dir}': {e}")
    ftp.quit()
    sys.exit(1)

print(f"--- {host}:{port}{remote_dir} ---")
lines = []
ftp.retrlines("LIST", lines.append)
for line in lines:
    print(line)

if any("wp-config.php" in line for line in lines):
    print(f"\n[OK] WordPress detected in {remote_dir}")

ftp.quit()
