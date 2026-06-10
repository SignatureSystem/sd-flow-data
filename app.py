from flask import Flask, jsonify, request
from datetime import datetime, date
import os, json, threading

app = Flask(__name__)

# ─── SHARED LICENSE FILE ──────────────────────────────────────────────────────
# Written by the bot; read here by the server.
# Both live on the same Railway Volume mounted at /data.
DATA_DIR      = '/data' if os.path.isdir('/data') else '/tmp'
LICENSE_FILE  = os.path.join(DATA_DIR, 'veo_licenses.json')

_file_lock    = threading.Lock()

def _load_all():
    """Load licenses, devices, and exempt list from the shared file."""
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
    """Write back to the shared file (used by admin endpoints)."""
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

    # Read cookies from shared file (bot writes them via !setcreds1)
    cookies_netscape = entry.get('cookies_netscape', '')
    if not cookies_netscape:
        # Fallback: read from a separate cookies field at root level
        try:
            with _file_lock:
                with open(LICENSE_FILE, 'r') as f:
                    root = json.load(f)
            cookies_netscape = root.get('cookies_netscape', '')
        except Exception:
            cookies_netscape = ''

    return jsonify({
        'licenses':         {key: entry},
        'cookies_netscape': cookies_netscape,
    })

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
    body = request.get_json(silent=True) or {}
    key  = body.get('key', '').strip()
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
        cur  = date.fromisoformat(licenses[key]['expires'])
        base = max(cur, date.today())
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

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
