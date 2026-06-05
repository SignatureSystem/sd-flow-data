from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# YOUR DATA
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "SD-ULTRA-TEST-0001": {"expires": "2025-12-31", "plan": "ultra"},
}

COOKIES_NETSCAPE = """# Netscape HTTP Cookie File
# Paste your Cookie-Editor export here
"""

# ─────────────────────────────────────────────────────────────────────────────

def cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.after_request
def add_cors(resp):
    return cors(resp)

@app.route('/sd-flow-data', methods=['GET', 'OPTIONS'])
def flow_data():
    if request.method == 'OPTIONS':
        return cors(app.response_class(status=204))
    return jsonify({
        "licenses": LICENSES,
        "cookies_netscape": COOKIES_NETSCAPE,
    })

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
