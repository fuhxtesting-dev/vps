#!/usr/bin/env python3
"""
FX HOSTING - Ultimate VPS Management Panel
Version: 3.0.1 - Railway Optimized
"""

import os
import sys
import signal
import subprocess
import threading
import time
import shutil
import zipfile
import py7zr
import psutil
import json
import hashlib
import secrets
import re
import platform
import socket
import datetime
import base64
import math
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, abort
from functools import wraps
from pathlib import Path

app = Flask(__name__)

# Railway-optimized secret key
import random
import string
SECRET_KEY_FILE = 'secret_key.txt'
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = secrets.token_hex(32)
    with open(SECRET_KEY_FILE, 'w') as f:
        f.write(app.secret_key)

# Railway session fix - use filesystem based session
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Railway uses HTTP internally
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=1)
)

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'user_files')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
DB_FILE = 'servers_db.json'
CONFIG_FILE = 'config.json'
ACTIVITY_LOG = 'activity_log.json'
SCHEDULER_FILE = 'scheduler.json'
START_TIME = time.time()

# Create directories
for folder in [STATIC_FOLDER, UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Default icon
DEFAULT_ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 24 24' fill='%2300ff00'%3E%3Cpath d='M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM4 18V6h16v12H4z'/%3E%3Cpath d='M6 8h12v2H6zm0 4h8v2H6z' opacity='.5'/%3E%3C/svg%3E"

# 20 Beautiful Themes
THEMES = {
    "matrix": {"name": "Matrix Green", "primary": "#00ff00", "secondary": "#00cc00", "accent": "#00ff80", "bg": "#050505", "card_bg": "#0a0f0a", "text": "#e0ffe0", "danger": "#ff3333", "warning": "#ffaa00", "info": "#00ccff"},
    "night": {"name": "Night Blue", "primary": "#4d88ff", "secondary": "#3366cc", "accent": "#aa88ff", "bg": "#050510", "card_bg": "#0a0a1a", "text": "#e0e8ff", "danger": "#ff4d4d", "warning": "#ffaa00", "info": "#00ccff"},
    "ocean": {"name": "Ocean Blue", "primary": "#3399ff", "secondary": "#0066cc", "accent": "#ff99cc", "bg": "#050a15", "card_bg": "#0a1525", "text": "#e0f0ff", "danger": "#ff4d4d", "warning": "#ffaa00", "info": "#00ccff"},
    "sunset": {"name": "Sunset Orange", "primary": "#ff9933", "secondary": "#cc6600", "accent": "#ff66b3", "bg": "#150a05", "card_bg": "#1f120a", "text": "#fff0e0", "danger": "#ff3333", "warning": "#ffcc00", "info": "#00ccff"},
    "blood": {"name": "Blood Red", "primary": "#ff4d4d", "secondary": "#cc0000", "accent": "#ff80bf", "bg": "#150505", "card_bg": "#1f0a0a", "text": "#ffe0e0", "danger": "#ff0000", "warning": "#ffaa00", "info": "#00ccff"},
    "neon": {"name": "Neon Purple", "primary": "#cc66ff", "secondary": "#9933cc", "accent": "#ffff80", "bg": "#0a0515", "card_bg": "#120a1f", "text": "#f0e0ff", "danger": "#ff4d4d", "warning": "#ffaa00", "info": "#00ccff"},
    "cyber": {"name": "Cyber Cyan", "primary": "#33ffff", "secondary": "#00cccc", "accent": "#ff80ff", "bg": "#051015", "card_bg": "#0a1a1f", "text": "#e0ffff", "danger": "#ff4d4d", "warning": "#ffaa00", "info": "#0088ff"},
    "vapor": {"name": "Vapor Pink", "primary": "#ff99cc", "secondary": "#cc6699", "accent": "#80ffff", "bg": "#150510", "card_bg": "#1f0a1a", "text": "#ffe0f0", "danger": "#ff3333", "warning": "#ffcc00", "info": "#00ccff"},
    "gold": {"name": "Royal Gold", "primary": "#ffcc66", "secondary": "#cc9933", "accent": "#ffb380", "bg": "#151005", "card_bg": "#1f1a0a", "text": "#fff8e0", "danger": "#ff3333", "warning": "#ffaa00", "info": "#00ccff"},
    "silver": {"name": "Silver Grey", "primary": "#b3b3b3", "secondary": "#808080", "accent": "#cccccc", "bg": "#0a0a0a", "card_bg": "#151515", "text": "#f0f0f0", "danger": "#ff4d4d", "warning": "#ffaa00", "info": "#00ccff"},
    "midnight": {"name": "Midnight", "primary": "#7c4dff", "secondary": "#512da8", "accent": "#ff6e40", "bg": "#080510", "card_bg": "#110d1f", "text": "#f0ecff", "danger": "#ff5252", "warning": "#ffd740", "info": "#40c4ff"},
    "emerald": {"name": "Emerald", "primary": "#00e676", "secondary": "#00c853", "accent": "#69f0ae", "bg": "#05150a", "card_bg": "#0a1f12", "text": "#e0ffec", "danger": "#ff5252", "warning": "#ffd740", "info": "#40c4ff"},
    "ruby": {"name": "Ruby", "primary": "#ff1744", "secondary": "#d50000", "accent": "#ff8a80", "bg": "#150508", "card_bg": "#1f0a0f", "text": "#ffe0e8", "danger": "#ff5252", "warning": "#ffd740", "info": "#40c4ff"},
    "sapphire": {"name": "Sapphire", "primary": "#2979ff", "secondary": "#2962ff", "accent": "#82b1ff", "bg": "#050a15", "card_bg": "#0a1025", "text": "#e0ecff", "danger": "#ff5252", "warning": "#ffd740", "info": "#00b0ff"},
    "amber": {"name": "Amber", "primary": "#ffab00", "secondary": "#ff6d00", "accent": "#ffe57f", "bg": "#151005", "card_bg": "#1f1808", "text": "#fff8e0", "danger": "#ff5252", "warning": "#ffcc00", "info": "#00b0ff"},
    "amethyst": {"name": "Amethyst", "primary": "#e040fb", "secondary": "#aa00ff", "accent": "#ea80fc", "bg": "#120515", "card_bg": "#1c0a1f", "text": "#f8e0ff", "danger": "#ff5252", "warning": "#ffd740", "info": "#00b0ff"},
    "tokyo": {"name": "Tokyo Night", "primary": "#7aa2f7", "secondary": "#565f89", "accent": "#bb9af7", "bg": "#06080f", "card_bg": "#0d111f", "text": "#c0caf5", "danger": "#f7768e", "warning": "#e0af68", "info": "#7dcfff"},
    "dracula": {"name": "Dracula", "primary": "#ff79c6", "secondary": "#bd93f9", "accent": "#8be9fd", "bg": "#0d0d14", "card_bg": "#161620", "text": "#f8f8f2", "danger": "#ff5555", "warning": "#f1fa8c", "info": "#8be9fd"},
    "monokai": {"name": "Monokai", "primary": "#a6e22e", "secondary": "#f92672", "accent": "#66d9ef", "bg": "#0d0d0d", "card_bg": "#1a1a1a", "text": "#f8f8f0", "danger": "#f92672", "warning": "#e6db74", "info": "#66d9ef"},
    "nord": {"name": "Nord", "primary": "#88c0d0", "secondary": "#81a1c1", "accent": "#b48ead", "bg": "#0d1117", "card_bg": "#161b22", "text": "#d8dee9", "danger": "#bf616a", "warning": "#ebcb8b", "info": "#81a1c1"}
}

DEFAULT_CONFIG = {
    "site_title": "FX HOSTING | Ultimate VPS Panel",
    "site_header": "FX HOSTING",
    "icon_url": DEFAULT_ICON,
    "theme": "matrix",
    "font_family": "terminal",
    "terminal_height": 300,
    "auto_refresh": True,
    "notifications": True,
    "show_system_stats": True,
    "session_timeout": 60,
    "max_log_lines": 2000,
    "backup_auto": False,
    "backup_interval": "24h",
    "passwords": {
        "secret": hashlib.sha256("FXFUHXFFKING".encode()).hexdigest(),
        "user": hashlib.sha256("admin".encode()).hexdigest()
    }
}

# =============================================================================
# DATA PERSISTENCE
# =============================================================================

def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def load_config():
    config = load_json(CONFIG_FILE, DEFAULT_CONFIG.copy())
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
    if 'passwords' not in config:
        config['passwords'] = DEFAULT_CONFIG['passwords']
    return config

CONFIG = load_config()
SERVERS = {}
SCHEDULED_TASKS = {}

def log_activity(action, details=""):
    logs = load_json(ACTIVITY_LOG, [])
    logs.append({
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "action": action,
        "details": details
    })
    if len(logs) > 500:
        logs = logs[-400:]
    save_json(ACTIVITY_LOG, logs)

def save_servers():
    try:
        data = {}
        for sid, s in SERVERS.items():
            data[sid] = {
                'cmd': s.get('cmd', ''),
                'cwd': s.get('cwd', ''),
                'path': s.get('path', ''),
                'auto_restart': s.get('auto_restart', False),
                'restart_interval': s.get('restart_interval', '1h'),
                'status': s.get('status', 'stopped'),
                'last_start_time': s.get('last_start_time', 0),
                'created_at': s.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S')),
                'notes': s.get('notes', ''),
                'group': s.get('group', 'default'),
                'tags': s.get('tags', []),
                'env_vars': s.get('env_vars', {})
            }
        save_json(DB_FILE, data)
    except Exception as e:
        print(f"Error saving servers: {e}")

def load_servers():
    global SERVERS
    saved = load_json(DB_FILE, {})
    for sid, s in saved.items():
        SERVERS[sid] = {
            'process': None,
            'cmd': s.get('cmd', ''),
            'cwd': s.get('cwd', ''),
            'auto_restart': s.get('auto_restart', False),
            'restart_interval': s.get('restart_interval', '1h'),
            'logs': [f">>> Server '{sid}' loaded at {time.strftime('%Y-%m-%d %H:%M:%S')}"],
            'status': 'stopped',
            'path': s.get('path', ''),
            'last_start_time': 0,
            'created_at': s.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S')),
            'notes': s.get('notes', ''),
            'group': s.get('group', 'default'),
            'tags': s.get('tags', []),
            'env_vars': s.get('env_vars', {})
        }
    log_activity("System", "Servers loaded from database")

load_servers()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        boot_time = psutil.boot_time()
        uptime = int(time.time() - boot_time)
        return {
            'cpu': cpu,
            'ram_used': round(ram.used / (1024**3), 2),
            'ram_total': round(ram.total / (1024**3), 2),
            'ram_percent': ram.percent,
            'disk_used': round(disk.used / (1024**3), 2),
            'disk_total': round(disk.total / (1024**3), 2),
            'disk_percent': round(disk.percent, 1),
            'net_sent': round(net.bytes_sent / (1024**2), 2),
            'net_recv': round(net.bytes_recv / (1024**2), 2),
            'load_avg': [round(x, 2) for x in load_avg],
            'uptime': uptime,
            'processes': len(psutil.pids()),
            'connections': len(psutil.net_connections())
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {'cpu': 0, 'ram_used': 0, 'ram_total': 0, 'ram_percent': 0, 'disk_used': 0, 'disk_total': 0, 'disk_percent': 0, 'net_sent': 0, 'net_recv': 0, 'load_avg': [0,0,0], 'uptime': 0, 'processes': 0, 'connections': 0}

def get_network_info():
    try:
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
        except:
            ip = "127.0.0.1"
        interfaces = {}
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces[name] = {'ip': addr.address, 'netmask': addr.netmask}
        return {'hostname': hostname, 'ip': ip, 'interfaces': interfaces}
    except:
        return {'hostname': 'unknown', 'ip': '127.0.0.1', 'interfaces': {}}

def format_uptime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)

def kill_process_completely(proc):
    try:
        if proc is None:
            return
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)
        for child in children:
            try: child.terminate()
            except: pass
        gone, alive = psutil.wait_procs(children, timeout=3)
        for child in alive:
            try: child.kill()
            except: pass
        try:
            parent.terminate()
            parent.wait(timeout=3)
        except:
            try: parent.kill()
            except: pass
    except Exception as e:
        print(f"Error killing process: {e}")

def log_monitor(server_id, proc_obj):
    server = SERVERS.get(server_id)
    if not server:
        return
    try:
        for line in iter(proc_obj.stdout.readline, ''):
            if server_id not in SERVERS or SERVERS[server_id].get('process') != proc_obj:
                break
            if line:
                cleaned = line.strip()
                if cleaned:
                    max_lines = CONFIG.get('max_log_lines', 2000)
                    if len(SERVERS[server_id]['logs']) > max_lines:
                        SERVERS[server_id]['logs'] = SERVERS[server_id]['logs'][-int(max_lines*0.9):]
                    SERVERS[server_id]['logs'].append(cleaned)
    except Exception as e:
        print(f"Log monitor error: {e}")
    finally:
        try: proc_obj.stdout.close()
        except: pass
    if server_id in SERVERS and SERVERS[server_id].get('process') == proc_obj:
        SERVERS[server_id]['status'] = 'stopped'
        SERVERS[server_id]['process'] = None
        SERVERS[server_id]['logs'].append(">>> [FX HOSTING] Process terminated.")
        save_servers()

def start_server_internal(server_id, server):
    if server['status'] == 'running':
        return True
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Add custom env vars
    for k, v in server.get('env_vars', {}).items():
        env[k] = v
    work_dir = os.path.join(server['path'], server.get('cwd', ''))
    if not os.path.exists(work_dir):
        work_dir = server['path']
    try:
        if not server['cmd'] or server['cmd'].strip() == '':
            server['logs'].append(">>> [FX HOSTING] Error: No start command specified")
            return False
        if not os.path.exists(work_dir):
            server['logs'].append(f">>> [FX HOSTING] Error: Working directory not found: {work_dir}")
            return False
        proc = subprocess.Popen(
            server['cmd'], shell=True, cwd=work_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE, text=True, bufsize=1,
            universal_newlines=True, env=env,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        server['process'] = proc
        server['status'] = 'running'
        server['last_start_time'] = time.time()
        server['logs'].append(f">>> [FX HOSTING] Server started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        threading.Thread(target=log_monitor, args=(server_id, proc), daemon=True).start()
        save_servers()
        log_activity("Server Start", f"Server '{server_id}' started")
        return True
    except Exception as e:
        server['logs'].append(f">>> [FX HOSTING] Failed to start: {str(e)}")
        return False

def auto_restarter():
    while True:
        time.sleep(10)
        current_time = time.time()
        for server_id, server in list(SERVERS.items()):
            try:
                if server.get('status') == 'running' and server.get('auto_restart'):
                    interval_str = server.get('restart_interval', '1h')
                    interval_map = {
                        '30s': 30, '1m': 60, '5m': 300, '10m': 600, '15m': 900,
                        '20m': 1200, '25m': 1500, '30m': 1800, '1h': 3600,
                        '2h': 7200, '3h': 10800, '6h': 21600, '12h': 43200, '24h': 86400
                    }
                    interval_sec = interval_map.get(interval_str, 3600)
                    last_start = server.get('last_start_time', current_time)
                    if current_time - last_start >= interval_sec:
                        server['logs'].append(f">>> [FX HOSTING] Auto-restarting (Interval: {interval_str})...")
                        if server.get('process'):
                            kill_process_completely(server['process'])
                            server['process'] = None
                        server['status'] = 'stopped'
                        start_server_internal(server_id, server)
            except Exception as e:
                print(f"Auto-restart error for {server_id}: {e}")

threading.Thread(target=auto_restarter, daemon=True).start()

# =============================================================================
# AUTH ROUTES
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if hashed == CONFIG['passwords']['secret']:
            session['logged_in'] = True
            session['is_secret'] = True
            session['login_time'] = time.time()
            log_activity("Login", "Secret user logged in")
            return redirect(url_for('index'))
        elif hashed == CONFIG['passwords']['user']:
            session['logged_in'] = True
            session['is_secret'] = False
            session['login_time'] = time.time()
            log_activity("Login", "Regular user logged in")
            return redirect(url_for('index'))
        else:
            log_activity("Login Failed", "Invalid password attempt")
            return render_template('login.html', error="Access Denied: Invalid credentials", config=CONFIG, themes=THEMES)
    return render_template('login.html', config=CONFIG, themes=THEMES)

@app.route('/logout')
def logout():
    log_activity("Logout", "User logged out")
    session.clear()
    return redirect(url_for('login'))

# =============================================================================
# MAIN ROUTES
# =============================================================================

@app.route('/')
@login_required
def index():
    stats = get_system_stats()
    net_info = get_network_info()
    current_theme = THEMES.get(CONFIG.get('theme', 'matrix'), THEMES['matrix'])
    serializable_servers = {}
    groups = set()
    for sid, s in SERVERS.items():
        serializable_servers[sid] = {
            'cmd': s.get('cmd', ''),
            'cwd': s.get('cwd', ''),
            'auto_restart': s.get('auto_restart', False),
            'restart_interval': s.get('restart_interval', '1h'),
            'status': s.get('status', 'stopped'),
            'path': s.get('path', ''),
            'last_start_time': s.get('last_start_time', 0),
            'created_at': s.get('created_at', 'Unknown'),
            'notes': s.get('notes', ''),
            'group': s.get('group', 'default'),
            'tags': s.get('tags', []),
            'uptime': format_uptime(int(time.time() - s.get('last_start_time', 0))) if s.get('status') == 'running' else '0m',
            'pid': s['process'].pid if s.get('process') else None
        }
        groups.add(s.get('group', 'default'))
    app_uptime = format_uptime(int(time.time() - START_TIME))
    return render_template('index.html',
                         servers=serializable_servers,
                         stats=stats,
                         net_info=net_info,
                         total_count=len(SERVERS),
                         running_count=sum(1 for s in SERVERS.values() if s['status'] == 'running'),
                         config=CONFIG,
                         theme=current_theme,
                         themes=THEMES,
                         is_secret=session.get('is_secret', False),
                         app_uptime=app_uptime,
                         start_date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(START_TIME)),
                         groups=sorted(groups))

# =============================================================================
# SERVER MANAGEMENT API
# =============================================================================

@app.route('/api/server/create', methods=['POST'])
@login_required
def create_server():
    try:
        data = request.get_json() or request.form
        server_name = data.get('server_name', '').strip().replace(' ', '_')
        start_command = data.get('start_command', '').strip()
        group = data.get('group', 'default').strip()
        notes = data.get('notes', '').strip()
        if not server_name:
            return jsonify({'error': 'Server name required'}), 400
        if server_name in SERVERS:
            return jsonify({'error': 'Server name already exists'}), 400
        server_path = os.path.join(UPLOAD_FOLDER, server_name)
        os.makedirs(server_path, exist_ok=True)
        SERVERS[server_name] = {
            'process': None, 'cmd': start_command, 'cwd': '',
            'logs': [f">>> [FX HOSTING] Server '{server_name}' created at {time.strftime('%Y-%m-%d %H:%M:%S')}"],
            'auto_restart': False, 'restart_interval': '1h', 'last_start_time': 0,
            'status': 'stopped', 'path': server_path,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'notes': notes, 'group': group, 'tags': [], 'env_vars': {}
        }
        save_servers()
        log_activity("Create Server", f"Created server '{server_name}'")
        return jsonify({'status': 'ok', 'server_id': server_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/upload', methods=['POST'])
@login_required
def upload_server_file():
    try:
        server_name = request.form.get('server_name', '').strip().replace(' ', '_')
        start_command = request.form.get('start_command', '').strip()
        group = request.form.get('group', 'default').strip()
        notes = request.form.get('notes', '').strip()
        if not server_name:
            return jsonify({'error': 'Server name required'}), 400
        if server_name in SERVERS:
            return jsonify({'error': 'Server name already exists'}), 400
        server_path = os.path.join(UPLOAD_FOLDER, server_name)
        os.makedirs(server_path, exist_ok=True)
        file = request.files.get('file')
        if file and file.filename:
            file_path = os.path.join(server_path, file.filename)
            file.save(file_path)
            if file.filename.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as z:
                    z.extractall(server_path)
            elif file.filename.lower().endswith('.7z'):
                with py7zr.SevenZipFile(file_path, mode='r') as z:
                    z.extractall(server_path)
        SERVERS[server_name] = {
            'process': None, 'cmd': start_command, 'cwd': '',
            'logs': [f">>> [FX HOSTING] Server '{server_name}' created with upload at {time.strftime('%Y-%m-%d %H:%M:%S')}"],
            'auto_restart': False, 'restart_interval': '1h', 'last_start_time': 0,
            'status': 'stopped', 'path': server_path,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'notes': notes, 'group': group, 'tags': [], 'env_vars': {}
        }
        save_servers()
        log_activity("Upload Server", f"Created server '{server_name}' with file upload")
        return jsonify({'status': 'ok', 'server_id': server_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/<server_id>/<action>', methods=['POST'])
@login_required
def server_action_api(server_id, action):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    server = SERVERS[server_id]
    try:
        if action == 'start':
            start_server_internal(server_id, server)
            log_activity("Start", f"Server '{server_id}' started")
            return jsonify({'status': 'ok'})
        elif action == 'stop':
            if server['process']:
                kill_process_completely(server['process'])
                server['process'] = None
            server['status'] = 'stopped'
            server['logs'].append(f">>> [FX HOSTING] Stopped at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            save_servers()
            log_activity("Stop", f"Server '{server_id}' stopped")
            return jsonify({'status': 'ok'})
        elif action == 'restart':
            if server['process']:
                kill_process_completely(server['process'])
                server['process'] = None
            server['status'] = 'stopped'
            server['logs'].append(">>> [FX HOSTING] Manual restart triggered...")
            time.sleep(0.5)
            start_server_internal(server_id, server)
            log_activity("Restart", f"Server '{server_id}' restarted")
            return jsonify({'status': 'ok'})
        elif action == 'delete':
            if server['process']:
                kill_process_completely(server['process'])
                server['process'] = None
            if os.path.exists(server['path']):
                shutil.rmtree(server['path'], ignore_errors=True)
            del SERVERS[server_id]
            save_servers()
            log_activity("Delete", f"Server '{server_id}' deleted")
            return jsonify({'status': 'ok'})
        elif action == 'clone':
            new_name = request.get_json().get('new_name', '').strip().replace(' ', '_') if request.get_json() else ''
            if not new_name or new_name in SERVERS:
                return jsonify({'error': 'Invalid clone name'}), 400
            new_path = os.path.join(UPLOAD_FOLDER, new_name)
            if os.path.exists(server['path']):
                shutil.copytree(server['path'], new_path)
            SERVERS[new_name] = {
                'process': None, 'cmd': server['cmd'], 'cwd': server.get('cwd', ''),
                'logs': [f">>> [FX HOSTING] Cloned from '{server_id}' at {time.strftime('%Y-%m-%d %H:%M:%S')}"],
                'auto_restart': False, 'restart_interval': '1h', 'last_start_time': 0,
                'status': 'stopped', 'path': new_path,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'notes': f"Cloned from {server_id}", 'group': server.get('group', 'default'),
                'tags': list(server.get('tags', [])), 'env_vars': dict(server.get('env_vars', {}))
            }
            save_servers()
            log_activity("Clone", f"Server '{server_id}' cloned to '{new_name}'")
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/<server_id>/config', methods=['GET', 'POST'])
@login_required
def server_config(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        SERVERS[server_id]['cmd'] = data.get('cmd', SERVERS[server_id]['cmd'])
        SERVERS[server_id]['cwd'] = data.get('cwd', SERVERS[server_id].get('cwd', ''))
        SERVERS[server_id]['auto_restart'] = data.get('auto_restart', SERVERS[server_id].get('auto_restart', False))
        SERVERS[server_id]['restart_interval'] = data.get('restart_interval', SERVERS[server_id].get('restart_interval', '1h'))
        SERVERS[server_id]['notes'] = data.get('notes', SERVERS[server_id].get('notes', ''))
        SERVERS[server_id]['group'] = data.get('group', SERVERS[server_id].get('group', 'default'))
        SERVERS[server_id]['env_vars'] = data.get('env_vars', SERVERS[server_id].get('env_vars', {}))
        save_servers()
        log_activity("Config Update", f"Server '{server_id}' configuration updated")
        return jsonify({'status': 'ok'})
    return jsonify({
        'cmd': SERVERS[server_id].get('cmd', ''),
        'cwd': SERVERS[server_id].get('cwd', ''),
        'auto_restart': SERVERS[server_id].get('auto_restart', False),
        'restart_interval': SERVERS[server_id].get('restart_interval', '1h'),
        'notes': SERVERS[server_id].get('notes', ''),
        'group': SERVERS[server_id].get('group', 'default'),
        'env_vars': SERVERS[server_id].get('env_vars', {}),
        'created_at': SERVERS[server_id].get('created_at', 'Unknown')
    })

@app.route('/api/server/<server_id>/logs')
@login_required
def get_server_logs(server_id):
    if server_id not in SERVERS:
        return jsonify({'logs': ''})
    return jsonify({'logs': '\n'.join(SERVERS[server_id]['logs'][-500:])})

@app.route('/api/server/<server_id>/input', methods=['POST'])
@login_required
def send_server_input(server_id):
    cmd = (request.get_json() or request.form).get('command', '')
    if not cmd or server_id not in SERVERS:
        return jsonify({'error': 'Invalid request'}), 400
    server = SERVERS[server_id]
    if not server['process']:
        return jsonify({'error': 'Process not running'}), 400
    try:
        proc = server['process']
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.write(cmd + '\n')
            proc.stdin.flush()
            server['logs'].append(f">>> [INPUT] {cmd}")
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'stdin closed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server/<server_id>/clear_logs', methods=['POST'])
@login_required
def clear_server_logs(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    SERVERS[server_id]['logs'] = [f">>> [FX HOSTING] Logs cleared at {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    save_servers()
    return jsonify({'status': 'ok'})

# =============================================================================
# FILE MANAGEMENT API
# =============================================================================

@app.route('/api/files/<server_id>')
@login_required
def list_files(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    subpath = request.args.get('path', '')
    base_path = SERVERS[server_id]['path']
    full_path = os.path.normpath(os.path.join(base_path, subpath)) if subpath else base_path
    if not os.path.realpath(full_path).startswith(os.path.realpath(base_path)):
        full_path = base_path
        subpath = ''
    if not os.path.exists(full_path):
        return jsonify({'files': [], 'current_path': '', 'total_size': '0 B'})
    files = []
    total_size = 0
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        is_file = os.path.isfile(item_path)
        size = os.path.getsize(item_path) if is_file else 0
        total_size += size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        elif size < 1024 ** 3:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size / (1024 ** 3):.1f} GB"
        files.append({
            'name': item, 'size': size_str, 'raw_size': size,
            'type': 'file' if is_file else 'dir',
            'ext': os.path.splitext(item)[1].lower() if is_file else '',
            'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(item_path)))
        })
    files.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
    if total_size < 1024:
        total_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_str = f"{total_size / 1024:.1f} KB"
    elif total_size < 1024 ** 3:
        total_str = f"{total_size / (1024 * 1024):.1f} MB"
    else:
        total_str = f"{total_size / (1024 ** 3):.1f} GB"
    return jsonify({'files': files, 'current_path': subpath, 'total_size': total_str})

@app.route('/api/files/<server_id>/content')
@login_required
def file_content(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    filename = request.args.get('filename', '')
    subpath = request.args.get('path', '')
    base_path = SERVERS[server_id]['path']
    file_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.realpath(file_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    if not os.path.isfile(file_path):
        return jsonify({'error': 'File not found'}), 404
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({'content': content, 'size': os.path.getsize(file_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<server_id>/save', methods=['POST'])
@login_required
def save_file_content(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    filename = data.get('filename', '')
    subpath = data.get('path', '')
    content = data.get('content', '')
    base_path = SERVERS[server_id]['path']
    file_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.realpath(file_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<server_id>/create', methods=['POST'])
@login_required
def create_file(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    filename = data.get('filename', '')
    subpath = data.get('path', '')
    content = data.get('content', '')
    base_path = SERVERS[server_id]['path']
    file_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.realpath(file_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    if os.path.exists(file_path):
        return jsonify({'error': 'File already exists'}), 400
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_activity("File Create", f"Created file '{filename}' in '{server_id}'")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<server_id>/mkdir', methods=['POST'])
@login_required
def create_folder(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    name = data.get('name', '')
    subpath = data.get('path', '')
    base_path = SERVERS[server_id]['path']
    target = os.path.normpath(os.path.join(base_path, subpath, name))
    if not os.path.realpath(target).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    os.makedirs(target, exist_ok=True)
    log_activity("Folder Create", f"Created folder '{name}' in '{server_id}'")
    return jsonify({'status': 'ok'})

@app.route('/api/files/<server_id>/rename', methods=['POST'])
@login_required
def rename_file(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    old_name = data.get('old_name', '')
    new_name = data.get('new_name', '')
    subpath = data.get('path', '')
    base_path = SERVERS[server_id]['path']
    old_path = os.path.normpath(os.path.join(base_path, subpath, old_name))
    new_path = os.path.normpath(os.path.join(base_path, subpath, new_name))
    if not os.path.realpath(old_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    if not os.path.exists(old_path):
        return jsonify({'error': 'File not found'}), 404
    os.rename(old_path, new_path)
    log_activity("Rename", f"Renamed '{old_name}' to '{new_name}' in '{server_id}'")
    return jsonify({'status': 'ok'})

@app.route('/api/files/<server_id>/delete', methods=['POST'])
@login_required
def delete_file(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    filename = data.get('filename', '')
    subpath = data.get('path', '')
    base_path = SERVERS[server_id]['path']
    file_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.realpath(file_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    if os.path.isdir(file_path):
        shutil.rmtree(file_path)
    else:
        os.remove(file_path)
    log_activity("Delete File", f"Deleted '{filename}' from '{server_id}'")
    return jsonify({'status': 'ok'})

@app.route('/api/files/<server_id>/upload', methods=['POST'])
@login_required
def upload_file(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    subpath = request.form.get('path', '')
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400
    base_path = SERVERS[server_id]['path']
    target_dir = os.path.normpath(os.path.join(base_path, subpath)) if subpath else base_path
    if not os.path.realpath(target_dir).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file.filename)
    file.save(file_path)
    msg = 'File uploaded successfully'
    if file.filename.lower().endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(target_dir)
        msg = 'ZIP extracted successfully'
    elif file.filename.lower().endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(target_dir)
        msg = '7Z extracted successfully'
    return jsonify({'status': 'ok', 'message': msg})

@app.route('/api/files/<server_id>/download')
@login_required
def download_file(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    import io
    filename = request.args.get('filename', '')
    subpath = request.args.get('path', '')
    base_path = SERVERS[server_id]['path']
    file_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.realpath(file_path).startswith(os.path.realpath(base_path)):
        return jsonify({'error': 'Invalid path'}), 400
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    if os.path.isdir(file_path):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(file_path):
                for f in files:
                    abs_path = os.path.join(root, f)
                    arcname = os.path.relpath(abs_path, os.path.dirname(file_path))
                    zf.write(abs_path, arcname)
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True,
                         download_name=filename + '.zip',
                         mimetype='application/zip')
    return send_file(file_path, as_attachment=True)

@app.route('/api/files/<server_id>/extract', methods=['POST'])
@login_required
def extract_archive(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    filename = data.get('filename', '')
    subpath = data.get('path', '')
    base_path = SERVERS[server_id]['path']
    archive_path = os.path.normpath(os.path.join(base_path, subpath, filename))
    if not os.path.exists(archive_path):
        return jsonify({'error': 'Archive not found'}), 404
    extract_to = os.path.dirname(archive_path)
    try:
        if filename.lower().endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(extract_to)
        elif filename.lower().endswith('.7z'):
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                z.extractall(extract_to)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# PACKAGE MANAGER API
# =============================================================================

@app.route('/api/packages/<server_id>/install', methods=['POST'])
@login_required
def install_package(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    pkg_type = data.get('type', 'pip')
    pkg_name = data.get('name', '').strip()
    if not pkg_name:
        return jsonify({'error': 'Package name required'}), 400
    commands = {
        'pip': f"pip install {pkg_name}",
        'npm': f"npm install {pkg_name}",
        'apt': f"apt install -y {pkg_name}",
        'pkg': f"pkg install -y {pkg_name}",
        'gem': f"gem install {pkg_name}"
    }
    cmd = commands.get(pkg_type, f"pip install {pkg_name}")
    SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Installing {pkg_name} via {pkg_type}...")
    def run_install():
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                if line:
                    SERVERS[server_id]['logs'].append(line.strip())
            SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Installation of {pkg_name} completed.")
        except Exception as e:
            SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Install error: {str(e)}")
    threading.Thread(target=run_install, daemon=True).start()
    log_activity("Package Install", f"Installed '{pkg_name}' ({pkg_type}) on '{server_id}'")
    return jsonify({'status': 'ok'})

@app.route('/api/packages/<server_id>/uninstall', methods=['POST'])
@login_required
def uninstall_package(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    pkg_type = data.get('type', 'pip')
    pkg_name = data.get('name', '').strip()
    if not pkg_name:
        return jsonify({'error': 'Package name required'}), 400
    commands = {
        'pip': f"pip uninstall -y {pkg_name}",
        'npm': f"npm uninstall {pkg_name}",
        'apt': f"apt remove -y {pkg_name}",
        'pkg': f"pkg uninstall -y {pkg_name}",
        'gem': f"gem uninstall {pkg_name}"
    }
    cmd = commands.get(pkg_type, f"pip uninstall -y {pkg_name}")
    SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Uninstalling {pkg_name} via {pkg_type}...")
    def run_uninstall():
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                if line:
                    SERVERS[server_id]['logs'].append(line.strip())
            SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Uninstallation of {pkg_name} completed.")
        except Exception as e:
            SERVERS[server_id]['logs'].append(f">>> [FX HOSTING] Uninstall error: {str(e)}")
    threading.Thread(target=run_uninstall, daemon=True).start()
    log_activity("Package Uninstall", f"Uninstalled '{pkg_name}' ({pkg_type}) from '{server_id}'")
    return jsonify({'status': 'ok'})

@app.route('/api/packages/<server_id>/list')
@login_required
def list_packages(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    pkg_type = request.args.get('type', 'pip')
    commands = {
        'pip': "pip list --format=json",
        'npm': "npm list --depth=0 --json",
        'apt': "apt list --installed 2>/dev/null | head -50",
        'pkg': "pkg list-installed 2>/dev/null | head -50"
    }
    cmd = commands.get(pkg_type, "pip list --format=json")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return jsonify({'output': result.stdout[:5000] or 'No packages found'})
    except:
        return jsonify({'output': 'Failed to list packages'})

# =============================================================================
# BACKUP MANAGER API
# =============================================================================

@app.route('/api/backup/<server_id>/create', methods=['POST'])
@login_required
def create_backup(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    try:
        backup_dir = os.path.join(BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_name = f"{server_id}_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_name)
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(SERVERS[server_id]['path']):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, SERVERS[server_id]['path'])
                    zf.write(file_path, arcname)
        log_activity("Backup", f"Created backup '{backup_name}' for '{server_id}'")
        return jsonify({'status': 'ok', 'backup_name': backup_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/<server_id>/restore', methods=['POST'])
@login_required
def restore_backup(server_id):
    if server_id not in SERVERS:
        return jsonify({'error': 'Server not found'}), 404
    data = request.get_json() or request.form
    backup_name = os.path.basename(data.get('backup_name', ''))
    backup_path = os.path.join(BASE_DIR, 'backups', backup_name)
    if not os.path.exists(backup_path):
        return jsonify({'error': 'Backup not found'}), 404
    try:
        # Stop server if running
        if SERVERS[server_id].get('status') == 'running' and SERVERS[server_id].get('process'):
            kill_process_completely(SERVERS[server_id]['process'])
            SERVERS[server_id]['process'] = None
            SERVERS[server_id]['status'] = 'stopped'
        # Clear existing files
        if os.path.exists(SERVERS[server_id]['path']):
            shutil.rmtree(SERVERS[server_id]['path'])
        os.makedirs(SERVERS[server_id]['path'], exist_ok=True)
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zf:
            zf.extractall(SERVERS[server_id]['path'])
        log_activity("Restore", f"Restored backup '{backup_name}' to '{server_id}'")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/list')
@login_required
def list_backups():
    backup_dir = os.path.join(BASE_DIR, 'backups')
    if not os.path.exists(backup_dir):
        return jsonify({'backups': []})
    backups = []
    for f in sorted(os.listdir(backup_dir), reverse=True):
        if f.endswith('.zip'):
            fpath = os.path.join(backup_dir, f)
            size = os.path.getsize(fpath)
            if size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            backups.append({
                'name': f,
                'size': size_str,
                'date': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(fpath)))
            })
    return jsonify({'backups': backups})

@app.route('/api/backup/delete', methods=['POST'])
@login_required
def delete_backup():
    data = request.get_json() or request.form
    backup_name = data.get('backup_name', '').replace('..', '')
    backup_path = os.path.join(BASE_DIR, 'backups', backup_name)
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Backup not found'}), 404

# =============================================================================
# PROCESS MONITOR API
# =============================================================================

@app.route('/api/system/processes')
@login_required
def get_processes():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            try:
                info = proc.info
                info['create_time'] = time.strftime('%H:%M:%S', time.localtime(info['create_time']))
                processes.append(info)
            except:
                pass
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return jsonify({'processes': processes[:100]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/kill_process', methods=['POST'])
@login_required
def kill_system_process():
    if not session.get('is_secret'):
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json() or request.form
    pid = data.get('pid')
    try:
        p = psutil.Process(int(pid))
        p.kill()
        log_activity("Process Kill", f"Killed system process PID {pid}")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# TERMINAL API
# =============================================================================

@app.route('/api/terminal/execute', methods=['POST'])
@login_required
def terminal_execute():
    if not session.get('is_secret'):
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json() or request.form
    command = data.get('command', '').strip()
    cwd = data.get('cwd', BASE_DIR)
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    # Security: block dangerous commands
    dangerous = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', ':(){:|:&};:', '> /dev/sda']
    for d in dangerous:
        if d in command:
            return jsonify({'error': f'Dangerous command blocked: {d}'}), 403
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return jsonify({'output': output[:10000], 'returncode': result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'output': 'Command timed out (30s)', 'returncode': -1})
    except Exception as e:
        return jsonify({'output': str(e), 'returncode': -1})

# =============================================================================
# PORT SCANNER API
# =============================================================================

@app.route('/api/system/ports')
@login_required
def get_ports():
    try:
        connections = psutil.net_connections()
        ports = []
        for conn in connections:
            if conn.laddr:
                try:
                    proc_name = psutil.Process(conn.pid).name() if conn.pid else ''
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = ''
                ports.append({
                    'port': conn.laddr.port,
                    'address': conn.laddr.ip,
                    'status': conn.status or '',
                    'pid': conn.pid,
                    'name': proc_name
                })
        ports.sort(key=lambda x: x['port'])
        return jsonify({'ports': ports[:200]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# SYSTEM INFO API
# =============================================================================

@app.route('/api/system/info')
@login_required
def system_info():
    try:
        info = {
            'platform': platform.platform(),
            'processor': platform.processor() or 'Unknown',
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            'total_ram': round(psutil.virtual_memory().total / (1024**3), 2),
            'swap': round(psutil.swap_memory().total / (1024**3), 2),
            'boot_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time())),
            'users': [u.name for u in psutil.users()]
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stats')
@login_required
def system_stats():
    return jsonify(get_system_stats())

# =============================================================================
# SETTINGS API
# =============================================================================

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def settings_api():
    global CONFIG
    if request.method == 'POST':
        data = request.get_json() or request.form
        CONFIG['site_title'] = data.get('site_title', CONFIG['site_title'])
        CONFIG['site_header'] = data.get('site_header', CONFIG['site_header'])
        CONFIG['icon_url'] = data.get('icon_url', CONFIG['icon_url'])
        CONFIG['theme'] = data.get('theme', CONFIG['theme'])
        CONFIG['font_family'] = data.get('font_family', CONFIG.get('font_family', 'terminal'))
        CONFIG['terminal_height'] = int(data.get('terminal_height', CONFIG.get('terminal_height', 300)))
        CONFIG['auto_refresh'] = data.get('auto_refresh', 'true') == 'true'
        CONFIG['notifications'] = data.get('notifications', 'true') == 'true'
        CONFIG['show_system_stats'] = data.get('show_system_stats', 'true') == 'true'
        save_json(CONFIG_FILE, CONFIG)
        log_activity("Settings", "Application settings updated")
        return jsonify({'status': 'ok'})
    return jsonify(CONFIG)

@app.route('/api/settings/password', methods=['POST'])
@login_required
def change_password_api():
    global CONFIG
    data = request.get_json() or request.form
    current = data.get('current', '')
    new_pass = data.get('new', '')
    hashed_current = hashlib.sha256(current.encode()).hexdigest()
    target = data.get('target', 'user')
    if target == 'secret' and not session.get('is_secret'):
        return jsonify({'error': 'Admin access required'}), 403
    if hashed_current != CONFIG['passwords'].get(target, ''):
        return jsonify({'error': 'Current password incorrect'}), 400
    CONFIG['passwords'][target] = hashlib.sha256(new_pass.encode()).hexdigest()
    save_json(CONFIG_FILE, CONFIG)
    log_activity("Password Change", f"{target} password changed")
    return jsonify({'status': 'ok'})

# =============================================================================
# ACTIVITY LOG API
# =============================================================================

@app.route('/api/activity')
@login_required
def get_activity():
    logs = load_json(ACTIVITY_LOG, [])
    return jsonify({'logs': list(reversed(logs))[:100]})

# =============================================================================
# TELEGRAM BOT API
# =============================================================================

@app.route('/api/telegram/deploy', methods=['POST'])
@login_required
def deploy_telegram_bot():
    data = request.get_json() or request.form
    bot_token = data.get('token', '').strip()
    bot_name = data.get('name', 'TelegramBot').strip().replace(' ', '_')
    if not bot_token or ':' not in bot_token:
        return jsonify({'error': 'Invalid bot token'}), 400
    if bot_name in SERVERS:
        return jsonify({'error': 'Server name already exists'}), 400
    server_path = os.path.join(UPLOAD_FOLDER, bot_name)
    os.makedirs(server_path, exist_ok=True)
    bot_code = f'''#!/usr/bin/env python3
"""Telegram Bot - Auto Generated by FX HOSTING"""
import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "{bot_token}"
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = """
<b>Welcome to FX HOSTING Bot!</b>

Available commands:
/start - Show this message
/help - Help & info
/ping - Check bot latency
/uptime - Server uptime
/status - System status
/info - Bot information
"""
    await message.answer(welcome, parse_mode=ParseMode.HTML)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
<b>FX HOSTING Bot Help</b>

/start - Start the bot
/help - This help message
/ping - Check response time
/uptime - Server uptime
/status - System resources
/info - About this bot

<i>Powered by FX HOSTING</i>
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    import time
    start = time.time()
    msg = await message.answer("Pinging...")
    elapsed = (time.time() - start) * 1000
    await msg.edit_text(f"<b>Pong!</b>\\nLatency: {{elapsed:.1f}}ms", parse_mode=ParseMode.HTML)

@router.message(Command("uptime"))
async def cmd_uptime(message: types.Message):
    import psutil
    uptime = datetime.now().timestamp() - psutil.boot_time()
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    await message.answer(f"<b>Server Uptime:</b> {{hours}}h {{minutes}}m", parse_mode=ParseMode.HTML)

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    import psutil
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    status = f"""
<b>System Status</b>
CPU: {{cpu}}%
RAM: {{ram}}%
Disk: {{disk}}%

<i>FX HOSTING Monitoring</i>
"""
    await message.answer(status, parse_mode=ParseMode.HTML)

@router.message(Command("info"))
async def cmd_info(message: types.Message):
    info = """
<b>FX HOSTING Bot</b>
Version: 3.0.0
Platform: AIogram 3.x

<i>Generated by FX HOSTING Panel</i>
"""
    await message.answer(info, parse_mode=ParseMode.HTML)

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''
    with open(os.path.join(server_path, 'bot.py'), 'w') as f:
        f.write(bot_code)
    SERVERS[bot_name] = {
        'process': None,
        'cmd': 'python3 bot.py',
        'cwd': '',
        'logs': [f">>> [FX HOSTING] Telegram bot '{bot_name}' created at {time.strftime('%Y-%m-%d %H:%M:%S')}"],
        'auto_restart': True,
        'restart_interval': '1h',
        'last_start_time': 0,
        'status': 'stopped',
        'path': server_path,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'notes': f'Telegram Bot - Token: {bot_token[:10]}...',
        'group': 'Telegram Bots',
        'tags': ['telegram', 'bot'],
        'env_vars': {}
    }
    save_servers()
    log_activity("Telegram Bot", f"Deployed bot '{bot_name}'")
    return jsonify({'status': 'ok', 'server_id': bot_name})

# =============================================================================
# STATIC FILES
# =============================================================================

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        return send_file(os.path.join(STATIC_FOLDER, filename))
    except:
        return "File not found", 404

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   ███████╗██╗  ██╗    ██╗  ██╗ ██████╗ ███████╗████████╗ ║
    ║   ██╔════╝╚██╗██╔╝    ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝ ║
    ║   █████╗   ╚███╔╝     ███████║██║   ██║███████╗   ██║    ║
    ║   ██╔══╝   ██╔██╗     ██╔══██║██║   ██║╚════██║   ██║    ║
    ║   ██║     ██╔╝ ██╗    ██║  ██║╚██████╔╝███████║   ██║    ║
    ║   ╚═╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝    ║
    ║                                                          ║
    ║   Ultimate VPS Management Panel v3.0.0                   ║
    ║   Optimized for Termux & Linux VPS                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    print(f"[FX HOSTING] Server started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("[FX HOSTING] Panel running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
