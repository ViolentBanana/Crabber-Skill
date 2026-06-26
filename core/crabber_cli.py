#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import socket
import subprocess
import argparse
import urllib.request
import urllib.error
from pathlib import Path

CRABBER_HOME = Path(os.path.expanduser("~/.crabber"))
DB_PATH = CRABBER_HOME / "db.json"
CONFIG_PATH = CRABBER_HOME / "config.json"
SHARE_DIR = CRABBER_HOME / "public" / "share"
LOG_FILE = CRABBER_HOME / "server.log"
UVICORN_BIN = CRABBER_HOME / "venv" / "bin" / "uvicorn"

def get_local_ip():
    """Gets the local IP address (usually en0/wifi)."""
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        valid_ips = []
        for ip in ips:
            if ip.startswith("127.") or ip.startswith("198.18.") or ip.startswith("169.254."):
                continue
            valid_ips.append(ip)
        
        if valid_ips:
            # Prioritize standard home/office LAN subnets (192.168.*)
            # then generic private subnets, filtering virtual machine subnets (like Parallels)
            valid_ips.sort(key=lambda x: (
                0 if x.startswith("192.168.") else
                1 if x.startswith("172.") else
                2 if (x.startswith("10.") and not (x.startswith("10.211.") or x.startswith("10.37."))) else
                3
            ))
            return valid_ips[0]
    except Exception:
        pass

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        if ip.startswith("198.18.") or ip.startswith("127."):
            raise ValueError("Proxy or loopback IP returned")
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def is_crabber_server_running(port):
    """Checks if our Crabber server is running and responding on a given port."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/files", timeout=1) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return isinstance(data, dict) and "files" in data
    except Exception:
        pass
    return False

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
    if source_path.is_dir():
        print(f"Error: Sharing directories is not supported directly. Please compress/zip the folder '{source_path.name}' first.")
        sys.exit(1)
        
    config = load_config()
    target_port = config.get("port", 8888)
    
    # Verify if Crabber is already running on the configured port.
    # If not running or occupied by another app, find a new port.
    if not is_crabber_server_running(target_port):
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
