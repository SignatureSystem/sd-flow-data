from flask import Flask, jsonify, request
from datetime import datetime
import os, json

app = Flask(__name__)

# ─── LICENSE KEYS — base licenses (always present even after redeploy) ──────────
BASE_LICENSES = {
    "69261123": {"expires": "2026-06-12", "plan": "ultra"},
}

# Keys exempt from device lock (can be used on any number of devices)
DEVICE_LOCK_EXEMPT = {"69261123"}

# ─── LICENSE PERSISTENCE ──────────────────────────────────────────────────────
LICENSE_FILE = os.path.join(DATA_DIR, 'sd_licenses.json')

def load_licenses():
    # Start with base licenses
    licenses = dict(BASE_LICENSES)
    # Overlay with persisted licenses (additions, changes, revocations)
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

# Load on startup — merges base + persisted
LICENSES = load_licenses()

# ─── DEVICE LOCK STORAGE ──────────────────────────────────────────────────────
# Storage strategy:
# 1. Railway Volume mount at /data (persistent across redeploys) — preferred
# 2. DEVICES_JSON env var — used to seed/restore after a redeploy
# 3. /tmp fallback — lost on restart, last resort
#
# HOW TO SET UP:
# - In Railway: Add a Volume mounted at /data
# - Set env var DEVICES_JSON={} initially
# - After devices accumulate, copy /admin/devices output into DEVICES_JSON env var
#   to restore after redeploys

DATA_DIR  = '/data' if os.path.isdir('/data') else '/tmp'
DEVICE_FILE = os.path.join(DATA_DIR, 'sd_devices.json')

def load_devices():
    # Try persistent file first
    try:
        if os.path.exists(DEVICE_FILE):
            with open(DEVICE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    # Fall back to env var seed (useful after fresh redeploy)
    raw = os.environ.get('DEVICES_JSON', '{}').strip()
    try:
        d = json.loads(raw)
        # Write to file so subsequent calls use file
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

# Load on startup
DEVICES = load_devices()

# ─── COOKIES ──────────────────────────────────────────────────────────────────
COOKIES_NETSCAPE = """\
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
labs.google	FALSE	/	FALSE	0	EMAIL	%22taikhoan13%404g5t.9iq.net%22
.labs.google	TRUE	/	FALSE	0	_ga_X5V89YHGSH	GS2.1.s1781002864$o2$g0$t1781004071$j60$l0$h0
labs.google	FALSE	/	TRUE	0	__Host-next-auth.csrf-token	c3ad4d9a6a6c646ebed8bd33b2f76f36202eab106b6c3fc041fbbd1a851d5346%7Cdf1de7e00c67a5a5914aa11da0304da56f605bbaaf3df420d869171cd02037ea
.labs.google	TRUE	/	FALSE	1815582268	_ga	GA1.1.300102121.1780935043
.labs.google	TRUE	/	FALSE	1815582268	_ga_X2GNH8R5NS	GS2.1.s1781022264$o10$g1$t1781022268$j56$l0$h990588533
labs.google	FALSE	/	TRUE	0	__Secure-next-auth.callback-url	https%3A%2F%2Flabs.google%2Ffx%2Ftools%2Fflow
labs.google	FALSE	/	TRUE	1783614317	__Secure-next-auth.session-token	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..V3ME-RqENvY0CA6n.Lh3vuS_YmOH-j70XHpwtzq5EqmwIPf2u_oBIa3R70LHrvXBRSBzEaVmVIhwbiSesc8oZWPctz3g5PKT7bUGv-GleyDtRgpxkWD6CCXxUa5amd57bQX5omMZy4PAolE7pzSHvkA6P416GpCTQ2LZn9_ChN4MjKSdG138HvYaXVWe17VM52M62D_vkfkCsOBM6QjuxpNqJsQ5PEB0t5SPFrqjpO1K7_cimS4igG2b4OpHdYOw8dKHPRMEJx8SWcuKH6YXttwdFotSumUFUTSm2iiIviu3BcHVey_MrdW_RWkWcso494T3FjFnD8V67Q7KZvCvFOGFuTfzEY8aGYT8QYqnMvKZ6nkZb2LhkS67WrGe2CzBCG08VRIc4ObUSeNafasZAmwJi-PvxOyaDzqbkwXVPvIZRrFvn9irDh_Srk7SzjE6gzvlqx0_jG0PExLQStGE4rPkFYqFMZLN_TviLKVWUUqaLjkE15cu1QLBR2haJm2TVprFqUkNKfhtSjhSF7OaaNKwj5eMeZ0e5vRM5cyJR5NoC5YEGiwxpYHxbh0Wgm25DpCLZYgRC-GsLyaavrQIaK8UB38fHl4ksUlEPzfNxZT9o6yQLT800uhnqOo8Al1AEHHPvZaJWiYQhh5Kd2crGbG-UQRIz8EWJBMzuPWP6Q6jmX38W-rWW9OpwD_aI1Z50lO8RIa6eJ3k0HXx5Ztgg8RYnb2XRdvPFfl-sbwhC8sD1qk7wKUrX4dL28bHkMtev-a4hyEShyMDR1iY4WcR8BDyVE3k6FKQOhxj5idrcPpczC6HDNeAFwERF_kM-18rU1IA-1Bsb2iSxpuzaNNSBTzPAFLYPEnSLKTrYMn7sFUniB5YMRbh7QNCtG6FNYJKE9JhBpnMKbCeXlxd3W0ot96YEnkYvtAoS38Ccrxe_LPHyk4Aw2V-qFa80fzThGISWVaHGwSEFrqFqynQjvZ1QKGt2udrfr7FhswpyHbemJSDgquKQOak.614VbSfPbKX2EMdzwna6yw
"""

def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.after_request
def after_request(resp):
    return add_cors(resp)

@app.route('/sd-flow-data', methods=['GET', 'OPTIONS'])
def flow_data():
    if request.method == 'OPTIONS':
        return add_cors(app.response_class(status=204))

    key      = request.args.get('key', '').strip()
    deviceId = request.args.get('deviceId', '').strip()

    if not key:
        return jsonify({'error': 'missing key'}), 401

    entry = LICENSES.get(key)
    if not entry:
        return jsonify({'error': 'invalid key'}), 401

    # Check expiry
    try:
        expiry = datetime.strptime(entry['expires'], '%Y-%m-%d')
        if datetime.utcnow() > expiry:
            return jsonify({'error': 'license expired'}), 403
    except Exception:
        return jsonify({'error': 'server error'}), 500

    # Device lock check (skip for exempt keys)
    if key not in DEVICE_LOCK_EXEMPT and deviceId:
        registered = DEVICES.get(key)
        if registered is None:
            # First activation — register this device
            DEVICES[key] = deviceId
            save_devices(DEVICES)
        elif registered != deviceId:
            return jsonify({'error': 'Maximum device limit exceeded. This license is already active on another device. Contact +94 77 831 5058 to transfer.'}), 403

    return jsonify({
        "licenses":         {key: entry},
        "cookies_netscape": COOKIES_NETSCAPE,
    })

# ─── Admin: reset device lock for a key ───────────────────────────────────────
# Usage: /admin/reset-device?secret=YOUR_SECRET&key=LICENSE_KEY
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'changeme123')

@app.route('/admin/reset-device', methods=['GET'])
def reset_device():
    secret = request.args.get('secret', '')
    key    = request.args.get('key', '').strip()
    if secret != ADMIN_SECRET:
        return jsonify({'error': 'unauthorized'}), 401
    if key not in LICENSES:
        return jsonify({'error': 'key not found'}), 404
    if key in DEVICES:
        del DEVICES[key]
        save_devices(DEVICES)
        return jsonify({'success': True, 'message': f'Device lock cleared for key {key}'})
    return jsonify({'success': True, 'message': 'No device registered for that key'})

@app.route('/admin/devices', methods=['GET'])
def list_devices():
    secret = request.args.get('secret', '')
    if secret != ADMIN_SECRET:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(DEVICES)

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ─── Admin endpoints called by VEO bot ────────────────────────────────────────

def check_secret(req):
    s = req.args.get('secret') or (req.get_json(silent=True) or {}).get('secret', '')
    return s == ADMIN_SECRET

@app.route('/admin/add-license', methods=['POST'])
def add_license():
    if not check_secret(request): return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
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
    key = data.get('key', '').strip()
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
