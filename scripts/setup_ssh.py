#!/usr/bin/env python3
"""Setup SSH key on remote server"""
import sys
from pathlib import Path

# Load config
env_file = Path(__file__).parent.parent / ".deploy.env"
if not env_file.exists():
    sys.exit(f"Error: {env_file} not found\nCopy .deploy.env.example to .deploy.env")

config = {}
with open(env_file, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            config[k.strip()] = v.strip()

for key in ['SERVER_IP', 'SERVER_USER', 'SERVER_PASS']:
    if not config.get(key):
        sys.exit(f"Error: Missing {key} in config")

# Get local public key
pubkey_file = Path.home() / ".ssh" / "id_rsa.pub"
if not pubkey_file.exists():
    sys.exit(f"Error: {pubkey_file} not found\nRun: ssh-keygen")

pubkey = pubkey_file.read_text().strip()

# Connect with paramiko
try:
    import paramiko
except ImportError:
    sys.exit("Error: paramiko required\npip install paramiko")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print(f"Connecting {config['SERVER_USER']}@{config['SERVER_IP']}...")
try:
    client.connect(config['SERVER_IP'], username=config['SERVER_USER'],
                  password=config['SERVER_PASS'], timeout=10)

    commands = [
        "mkdir -p ~/.ssh",
        f"echo '{pubkey}' >> ~/.ssh/authorized_keys",
        "chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
    ]

    for cmd in commands:
        _, stdout, _ = client.exec_command(cmd)
        stdout.read()

    print("[OK] SSH key configured")
except Exception as e:
    sys.exit(f"Error: {e}")
finally:
    client.close()
