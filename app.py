from flask import Flask, jsonify, request
from datetime import datetime, date
import os, json, threading

app = Flask(__name__)

# ─── SHARED LICENSE FILE ──────────────────────────────────────────────────────
DATA_DIR      = '/data' if os.path.isdir('/data') else '/tmp'
LICENSE_FILE  = os.path.join(DATA_DIR, 'veo_licenses.json')
COOKIES_FILE  = os.path.join(DATA_DIR, 'veo_cookies.txt')

_file_lock    = threading.Lock()

# ─── COOKIES (in-memory + persisted to veo_cookies.txt) ──────────────────────
_cookies_netscape = ''
_cookies_lock     = threading.Lock()

def _load_cookies():
    global _cookies_netscape
    try:
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                _cookies_netscape = f.read()
            app.logger.info('Cookies loaded from ' + COOKIES_FILE)
    except Exception as e:
        app.logger.error('load_cookies error: ' + str(e))

def _save_cookies(text):
    global _cookies_netscape
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = COOKIES_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp, COOKIES_FILE)
        with _cookies_lock:
            _cookies_netscape = text
        app.logger.info('Cookies saved to ' + COOKIES_FILE)
        return True
    except Exception as e:
        app.logger.error('save_cookies error: ' + str(e))
        return False

# Load cookies on startup
_load_cookies()

# ─── LICENSE FILE HELPERS ─────────────────────────────────────────────────────
def _load_all():
    try:
        with _file_lock:
            with open(LICENSE_FILE, 'r') as f:
                d = json.load(f)
        return d.get('licenses', {}), d.get('devices', {}), d.get('exempt', [])
    except FileNotFoundError:
        return {}, {}, []
    except Exception as e:
        app.logger.error('veo_licenses load error: ' + str(e))
        return {}, {}, []

def _save_all(licenses, devices, exempt):
    try:
        payload = {'licenses': licenses, 'devices': devices, 'exempt': exempt}
        tmp = LICENSE_FILE + '.tmp'
        with _file_lock:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(tmp, 'w') as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, LICENSE_FILE)
    except Exception as e:
        app.logger.error('veo_licenses save error: ' + str(e))

# ─── ADMIN AUTH ───────────────────────────────────────────────────────────────
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'changeme123')

def _auth(req):
    s = req.args.get('secret') or (req.get_json(silent=True) or {}).get('secret', '')
    return s == ADMIN_SECRET

# ─── CORS ─────────────────────────────────────────────────────────────────────
@app.after_request
def _cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Cache-Control'] = 'no-store'
    return resp

# ─── PUBLIC: extension fetches license + cookies ─────────────────────────────
@app.route('/sd-flow-data', methods=['GET', 'OPTIONS'])
def flow_data():
    if request.method == 'OPTIONS':
        return app.response_class(status=204)

    key      = request.args.get('key', '').strip()
    deviceId = request.args.get('deviceId', '').strip()

    if not key:
        return jsonify({'error': 'missing key'}), 401

    licenses, devices, exempt = _load_all()

    entry = licenses.get(key)
    if not entry:
        return jsonify({'error': 'invalid key'}), 401

    # Expiry check
    try:
        expiry = date.fromisoformat(entry['expires'])
        if date.today() > expiry:
            return jsonify({'error': 'license expired'}), 403
    except Exception:
        return jsonify({'error': 'server error'}), 500

    # Device lock (skip for exempt keys)
    if key not in exempt and deviceId:
        registered = devices.get(key)
        if registered is None:
            devices[key] = deviceId
            _save_all(licenses, devices, exempt)
        elif registered != deviceId:
            return jsonify({'error': 'Maximum device limit exceeded. This license is already active on another device. Contact +94 77 831 5058 to transfer.'}), 403

    with _cookies_lock:
        cookies = _cookies_netscape

    return jsonify({
        'licenses':         {key: entry},
        'cookies_netscape': cookies,
    })

# ─── ADMIN: set cookies ───────────────────────────────────────────────────────
@app.route('/admin/set-cookies', methods=['POST'])
def set_cookies():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    body = request.get_json(silent=True) or {}
    text = body.get('cookies', '').strip()
    if not text:
        return jsonify({'error': 'cookies field required'}), 400
    ok = _save_cookies(text)
    if ok:
        return jsonify({'success': True, 'length': len(text)})
    return jsonify({'error': 'failed to save'}), 500

# ─── ADMIN: get cookies ───────────────────────────────────────────────────────
@app.route('/admin/get-cookies', methods=['GET'])
def get_cookies():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    with _cookies_lock:
        cookies = _cookies_netscape
    return jsonify({'cookies_netscape': cookies, 'length': len(cookies)})

# ─── ADMIN: reset device lock ─────────────────────────────────────────────────
@app.route('/admin/reset-device', methods=['GET'])
def reset_device():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    key = request.args.get('key', '').strip()
    licenses, devices, exempt = _load_all()
    if key not in licenses:
        return jsonify({'error': 'key not found'}), 404
    removed = devices.pop(key, None)
    _save_all(licenses, devices, exempt)
    msg = 'Device lock cleared for ' + key if removed else 'No device registered for that key'
    return jsonify({'success': True, 'message': msg})

# ─── ADMIN: list all devices ──────────────────────────────────────────────────
@app.route('/admin/devices', methods=['GET'])
def list_devices():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    _, devices, _ = _load_all()
    return jsonify(devices)

# ─── ADMIN: list all licenses ─────────────────────────────────────────────────
@app.route('/admin/licenses', methods=['GET'])
def list_licenses():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    licenses, devices, exempt = _load_all()
    return jsonify({'licenses': licenses, 'devices': devices, 'exempt': exempt})

# ─── ADMIN: add license ───────────────────────────────────────────────────────
@app.route('/admin/add-license', methods=['POST'])
def add_license():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    body    = request.get_json(silent=True) or {}
    key     = body.get('key', '').strip()
    expires = body.get('expires', '').strip()
    plan    = body.get('plan', 'ultra')
    if not key or not expires:
        return jsonify({'error': 'key and expires required'}), 400
    licenses, devices, exempt = _load_all()
    licenses[key] = {'expires': expires, 'plan': plan}
    _save_all(licenses, devices, exempt)
    return jsonify({'success': True, 'key': key, 'expires': expires})

# ─── ADMIN: revoke license ────────────────────────────────────────────────────
@app.route('/admin/revoke-license', methods=['POST'])
def revoke_license():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    body = request.get_json(silent=True) or {}
    key  = body.get('key', '').strip()
    licenses, devices, exempt = _load_all()
    if key not in licenses:
        return jsonify({'error': 'key not found'}), 404
    del licenses[key]
    devices.pop(key, None)
    if key in exempt:
        exempt.remove(key)
    _save_all(licenses, devices, exempt)
    return jsonify({'success': True})

# ─── ADMIN: extend license ────────────────────────────────────────────────────
@app.route('/admin/extend-license', methods=['POST'])
def extend_license():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    from datetime import timedelta
    body = request.get_json(silent=True) or {}
    key  = body.get('key', '').strip()
    days = body.get('days', 0)
    licenses, devices, exempt = _load_all()
    if key not in licenses:
        return jsonify({'error': 'key not found'}), 404
    try:
        cur     = date.fromisoformat(licenses[key]['expires'])
        base    = max(cur, date.today())
        new_exp = (base + timedelta(days=int(days))).isoformat()
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    licenses[key]['expires'] = new_exp
    _save_all(licenses, devices, exempt)
    return jsonify({'success': True, 'expires': new_exp})

# ─── ADMIN: reduce license ────────────────────────────────────────────────────
@app.route('/admin/reduce-license', methods=['POST'])
def reduce_license():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    from datetime import timedelta
    body = request.get_json(silent=True) or {}
    key  = body.get('key', '').strip()
    days = body.get('days', 0)
    licenses, devices, exempt = _load_all()
    if key not in licenses:
        return jsonify({'error': 'key not found'}), 404
    try:
        cur     = date.fromisoformat(licenses[key]['expires'])
        new_exp = (cur - timedelta(days=int(days))).isoformat()
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    licenses[key]['expires'] = new_exp
    _save_all(licenses, devices, exempt)
    return jsonify({'success': True, 'expires': new_exp})

# ─── ADMIN: check license ─────────────────────────────────────────────────────
@app.route('/admin/check-license', methods=['GET'])
def check_license():
    if not _auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    key = request.args.get('key', '').strip()
    licenses, devices, exempt = _load_all()
    if key not in licenses:
        return jsonify({'error': 'key not found'}), 404
    return jsonify({
        'entry':  licenses[key],
        'device': devices.get(key),
        'exempt': key in exempt,
    })

# ─── DEBUG ────────────────────────────────────────────────────────────────────
@app.route('/debug', methods=['GET'])
def debug():
    file_exists     = os.path.exists(LICENSE_FILE)
    cookies_exists  = os.path.exists(COOKIES_FILE)
    data_dir_files  = os.listdir(DATA_DIR) if os.path.isdir(DATA_DIR) else []
    licenses, devices, exempt = _load_all()
    with _cookies_lock:
        cookies_len = len(_cookies_netscape)
    return jsonify({
        'DATA_DIR':        DATA_DIR,
        'LICENSE_FILE':    LICENSE_FILE,
        'file_exists':     file_exists,
        'cookies_exists':  cookies_exists,
        'cookies_length':  cookies_len,
        'data_dir_files':  data_dir_files,
        'license_count':   len(licenses),
        'license_keys':    list(licenses.keys()),
        'exempt':          exempt,
    })

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
