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

fpath = "~/www/lopezvelarde.edu.mx/public_html/wp-content/themes/divi-agentic-core/functions.php"

# Read current file
_, stdout, _ = client.exec_command(f"cat {fpath}", timeout=10)
content = stdout.read().decode("utf-8", errors="replace")

# Comment out the broken WP-CLI block
old = (
    "if ( defined( 'WP_CLI' ) && WP_CLI && ! class_exists( '\\\\DAC\\\\CLI\\\\Agentic_Command' ) ) {\n"
    "    \\\\DAC\\\\CLI\\\\Agentic_Command::register();\n"
    "}"
)
new = (
    "// [DAW] Disabled - Agentic_Command class mismatch\n"
    "// if ( defined( 'WP_CLI' ) && WP_CLI && ! class_exists( '\\\\DAC\\\\CLI\\\\Agentic_Command' ) ) {\n"
    "//     \\\\DAC\\\\CLI\\\\Agentic_Command::register();\n"
    "// }"
)

if old in content:
    content = content.replace(old, new)
    # Write back via SSH
    stdin, stdout, stderr = client.exec_command(
        f"cat > {fpath}", timeout=10
    )
    stdin.write(content)
    stdin.channel.shutdown_write()
    err = stderr.read().decode().strip()
    if err:
        print(f"Error: {err}")
    else:
        print("Fixed - WP-CLI block commented out")
else:
    print("Pattern not found or already modified")

client.close()
