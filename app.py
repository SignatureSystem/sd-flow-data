from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import os, json

app = Flask(__name__)

# ─── STORAGE PATHS (must be first — everything depends on DATA_DIR) ───────────
DATA_DIR    = '/data' if os.path.isdir('/data') else '/tmp'
DEVICE_FILE = os.path.join(DATA_DIR, 'sd_devices.json')
LICENSE_FILE = os.path.join(DATA_DIR, 'sd_licenses.json')
COOKIE_FILE = os.path.join(DATA_DIR, 'sd_cookies.txt')

# ─── LICENSE KEYS — base licenses (always present even after redeploy) ────────
BASE_LICENSES = {}

# Keys exempt from device lock (can be used on any number of devices)
DEVICE_LOCK_EXEMPT = {"69261123"}

# ─── VERSION CONTROL ──────────────────────────────────────────────────────────
MIN_VERSION = os.environ.get('FLOW_MIN_VERSION', '1.0.0')

def version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).split('.'))
    except:
        return (0, 0, 0)

def version_allowed(v):
    return version_tuple(v) >= version_tuple(MIN_VERSION)

# ─── DEVICE LOCK STORAGE ──────────────────────────────────────────────────────
def load_devices():
    try:
        if os.path.exists(DEVICE_FILE):
            with open(DEVICE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    raw = os.environ.get('DEVICES_JSON', '{}').strip()
    try:
        d = json.loads(raw)
        save_devices_to_file(d)
        return d
    except Exception:
        return {}

def save_devices_to_file(devices):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DEVICE_FILE, 'w') as f:
            json.dump(devices, f)
    except Exception:
        pass

def save_devices(devices):
    save_devices_to_file(devices)

DEVICES = load_devices()

# ─── LICENSE PERSISTENCE ──────────────────────────────────────────────────────
def load_licenses():
    licenses = dict(BASE_LICENSES)
    try:
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, 'r') as f:
                persisted = json.load(f)
                licenses.update(persisted)
    except Exception as e:
        print(f'[SDFlow] License file load error: {e}')
    return licenses

def save_licenses():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LICENSE_FILE, 'w') as f:
            json.dump(LICENSES, f, indent=2)
    except Exception as e:
        print(f'[SDFlow] License file save error: {e}')

LICENSES = load_licenses()

# ─── COOKIE OVERRIDE ─────────────────────────────────────────────────────────
_cookie_override = None

def load_cookie_override():
    global _cookie_override
    try:
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r') as f:
                _cookie_override = f.read()
            print('[SDFlow] Cookie override loaded from file')
    except Exception as e:
        print(f'[SDFlow] Cookie load error: {e}')

def save_cookie_override(text):
    global _cookie_override
    _cookie_override = text
    try:
        with open(COOKIE_FILE, 'w') as f:
            f.write(text)
    except Exception as e:
        print(f'[SDFlow] Cookie save error: {e}')

def get_active_cookies():
    return _cookie_override if _cookie_override else COOKIES_NETSCAPE

# ─── COOKIES ──────────────────────────────────────────────────────────────────
COOKIES_NETSCAPE = """\
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
"""

load_cookie_override()

# ─── CORS ─────────────────────────────────────────────────────────────────────
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS, POST'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.after_request
def after_request(resp):
    return add_cors(resp)

# ─── AUTH ─────────────────────────────────────────────────────────────────────
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'changeme123')

def check_secret(req):
    s = req.args.get('secret') or (req.get_json(silent=True) or {}).get('secret', '')
    return s == ADMIN_SECRET

# ─── MAIN ENDPOINT ────────────────────────────────────────────────────────────
@app.route('/sd-flow-data', methods=['GET', 'OPTIONS'])
def flow_data():
    if request.method == 'OPTIONS':
        return add_cors(app.response_class(status=204))

    key      = request.args.get('key', '').strip()
    deviceId = request.args.get('deviceId', '').strip()
    version  = request.args.get('v', '0.0.0').strip()

    if not version_allowed(version):
        return jsonify({'error': f'Extension version {version} is outdated. Please update to v{MIN_VERSION} or higher.'}), 426

    if not key:
        return jsonify({'error': 'missing key'}), 401

    entry = LICENSES.get(key)
    if not entry:
        return jsonify({'error': 'invalid key'}), 401

    try:
        expiry = datetime.strptime(entry['expires'], '%Y-%m-%d')
        if datetime.utcnow() > expiry:
            return jsonify({'error': 'license expired'}), 403
    except Exception:
        return jsonify({'error': 'server error'}), 500

    if key not in DEVICE_LOCK_EXEMPT and deviceId:
        registered = DEVICES.get(key)
        if registered is None:
            DEVICES[key] = deviceId
            save_devices(DEVICES)
        elif registered != deviceId:
            return jsonify({'error': 'Maximum device limit exceeded. This license is already active on another device. Contact +94 77 831 5058 to transfer.'}), 403

    return jsonify({
        "licenses":         {key: entry},
        "cookies_netscape": get_active_cookies(),
    })

# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────
@app.route('/admin/reset-device', methods=['GET'])
def reset_device():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    key = request.args.get('key', '').strip()
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    if key in DEVICES:
        del DEVICES[key]
        save_devices(DEVICES)
        return jsonify({'success': True, 'message': f'Device lock cleared for key {key}'})
    return jsonify({'success': True, 'message': 'No device registered for that key'})

@app.route('/admin/devices', methods=['GET'])
def list_devices():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    return jsonify(DEVICES)

@app.route('/admin/add-license', methods=['POST'])
def add_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data    = request.get_json(silent=True) or {}
    key     = data.get('key', '').strip()
    expires = data.get('expires', '').strip()
    plan    = data.get('plan', 'ultra').strip()
    if not key or not expires:
        return jsonify({'error': 'missing key or expires'}), 400
    LICENSES[key] = {'expires': expires, 'plan': plan}
    save_licenses()
    return jsonify({'success': True, 'key': key, 'expires': expires})

@app.route('/admin/revoke-license', methods=['POST'])
def revoke_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    key  = data.get('key', '').strip()
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    del LICENSES[key]
    save_licenses()
    if key in DEVICES:
        del DEVICES[key]
        save_devices(DEVICES)
    return jsonify({'success': True})

@app.route('/admin/extend-license', methods=['POST'])
def extend_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    key  = data.get('key', '').strip()
    days = int(data.get('days', 0))
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    try:
        current = datetime.strptime(LICENSES[key]['expires'], '%Y-%m-%d').date()
        if current < datetime.utcnow().date():
            current = datetime.utcnow().date()
        new_expiry = (current + timedelta(days=days)).strftime('%Y-%m-%d')
        LICENSES[key]['expires'] = new_expiry
        save_licenses()
        return jsonify({'success': True, 'expires': new_expiry})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reduce-license', methods=['POST'])
def reduce_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    key  = data.get('key', '').strip()
    days = int(data.get('days', 0))
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    try:
        current    = datetime.strptime(LICENSES[key]['expires'], '%Y-%m-%d').date()
        new_expiry = (current - timedelta(days=days)).strftime('%Y-%m-%d')
        LICENSES[key]['expires'] = new_expiry
        save_licenses()
        return jsonify({'success': True, 'expires': new_expiry})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/check-license', methods=['GET'])
def check_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    key = request.args.get('key', '').strip()
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    return jsonify({
        'key':    key,
        'entry':  LICENSES[key],
        'device': DEVICES.get(key),
        'exempt': key in DEVICE_LOCK_EXEMPT
    })

@app.route('/admin/licenses', methods=['GET'])
def list_licenses():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    return jsonify({
        'licenses': LICENSES,
        'devices':  DEVICES,
        'exempt':   list(DEVICE_LOCK_EXEMPT)
    })

@app.route('/admin/set-cookies', methods=['POST'])
def set_cookies():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data         = request.get_json(silent=True) or {}
    cookies_text = data.get('cookies', '').strip()
    if not cookies_text:
        return jsonify({'error': 'missing cookies'}), 400
    save_cookie_override(cookies_text)
    lines = [l for l in cookies_text.split('\n') if l.strip() and not l.startswith('#')]
    return jsonify({'success': True, 'cookie_lines': len(lines)})

@app.route('/admin/get-cookies', methods=['GET'])
def get_cookies_endpoint():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    active = get_active_cookies()
    lines  = [l for l in active.split('\n') if l.strip() and not l.startswith('#')]
    return jsonify({
        'source':       'override' if _cookie_override else 'hardcoded',
        'cookie_count': len(lines),
        'cookies':      active
    })

@app.route('/admin/version-info', methods=['GET'])
def version_info():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    return jsonify({
        'extension_version': '2.0.0',
        'min_version': MIN_VERSION
    })

@app.route('/admin/set-min-version', methods=['POST'])
def set_min_version():
    global MIN_VERSION
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    ver  = data.get('version', '').strip()
    if not ver:
        return jsonify({'error': 'missing version'}), 400
    MIN_VERSION = ver
    return jsonify({'success': True, 'min_version': MIN_VERSION})

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
