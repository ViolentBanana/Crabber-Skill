#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import socket
import subprocess
import argparse
from pathlib import Path

CRABBER_HOME = Path(os.path.expanduser("~/.crabber"))
DB_PATH = CRABBER_HOME / "db.json"
CONFIG_PATH = CRABBER_HOME / "config.json"
SHARE_DIR = CRABBER_HOME / "public" / "share"
LOG_FILE = CRABBER_HOME / "server.log"
UVICORN_BIN = CRABBER_HOME / "venv" / "bin" / "uvicorn"

def get_local_ip():
    """Gets the local IP address (usually en0/wifi)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_available_port(start_port=8888):
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"port": 8888}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def load_db():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"files": []}

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

def ensure_server_running(port):
    if not is_port_in_use(port):
        # Start server as a daemon process
        # We assume this script is run from within the crabber environment
        # But to be safe, we use the absolute path to uvicorn
        cmd = [
            str(UVICORN_BIN),
            "core.server:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--app-dir", str(CRABBER_HOME)
        ]
        with open(LOG_FILE, "a") as log:
            subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                start_new_session=True # Detach from terminal
            )
        # Give it a second to start
        time.sleep(1)

def share_file(file_path, ttl=3600):
    source_path = Path(file_path).resolve()
    if not source_path.exists():
        print(f"Error: File does not exist at {source_path}")
        sys.exit(1)
        
    config = load_config()
    target_port = config.get("port", 8888)
    
    # Check if the configured port is actually our server or another app
    # If it's another app and our server isn't running, we need a new port
    # For simplicity, we assume if it's running, it's ours. If not, we find one.
    if not is_port_in_use(target_port):
        target_port = get_available_port(target_port)
        config["port"] = target_port
        save_config(config)
        
    ensure_server_running(target_port)
    
    # Ensure share dir exists
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create unique ID and symlink
    file_id = str(uuid.uuid4())
    filename = source_path.name
    symlink_path = SHARE_DIR / f"{file_id}_{filename}"
    
    try:
        os.symlink(source_path, symlink_path)
    except Exception as e:
        print(f"Error creating symlink: {e}")
        sys.exit(1)
        
    # Update DB
    db = load_db()
    file_info = {
        "id": file_id,
        "name": filename,
        "path": str(symlink_path),
        "size": source_path.stat().st_size,
        "created_at": time.time(),
        "ttl": ttl
    }
    db["files"].append(file_info)
    save_db(db)
    
    # Output the result
    ip = get_local_ip()
    url = f"http://{ip}:{target_port}/"
    print(f"✅ [Crabber] 文件已发布，请点击查看/下载：{url}")
    # We output the index URL instead of the direct download URL so the user sees the beautiful UI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crabber Skill CLI")
    parser.add_argument("file_path", help="Absolute path to the file to share")
    parser.add_argument("--ttl", type=int, default=3600, help="Time to live in seconds (default: 3600)")
    
    args = parser.parse_args()
    share_file(args.file_path, args.ttl)
