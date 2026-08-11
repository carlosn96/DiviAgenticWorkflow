from io import StringIO
from pathlib import Path
import paramiko

def get_env():
    env = {}
    with open(Path(__file__).parents[2] / ".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip("'\"")
    return env

env = get_env()

key_text = []
with open(Path(__file__).parents[2] / "info-server.txt") as f:
    lines = f.readlines()
    in_key = False
    for line in lines:
        if "BEGIN OPENSSH PRIVATE KEY" in line:
            in_key = True
        if in_key:
            key_text.append(line.rstrip())
        if "END OPENSSH PRIVATE KEY" in line and in_key:
            break

pkey = paramiko.Ed25519Key.from_private_key(
    StringIO("\n".join(key_text)),
    password=env.get("ADMIN_PASSWORD", ""),
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    env["REMOTE_SSH_HOST"],
    port=int(env.get("REMOTE_SSH_PORT", "22")),
    username=env["REMOTE_SSH_USER"],
    pkey=pkey,
    timeout=15,
)

_, stdout, _ = client.exec_command(
    'echo HOME=$HOME; echo PWD=$(pwd); ls -la ~/www/ 2>/dev/null; '
    'find ~/www -name wp-config.php 2>/dev/null; echo DONE',
    timeout=15,
)
print(stdout.read().decode())
client.close()
