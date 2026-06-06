from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LICENSE KEYS
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "SD-ULTRA-TEST-0001": {"expires": "2025-12-31", "plan": "ultra"},
    # "SD-ULTRA-NAME-0002": {"expires": "2025-09-01", "plan": "ultra"},
}

# ─────────────────────────────────────────────────────────────────────────────
# COOKIES
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_JSON = """
[
  {
    "name": "NID",
    "value": "532=hlpvyCe4c-pXCkUuckxpgL56_mFMPqX9wMuEVJXqxqsJBB_8AfmIUNOI13YcW-5IjK0VlaCX-vbBbX62iRyNiJQ5Q9MteeCmAfM0Az4g_2rIZ_24swdtO0-o1Hdk9FJNy803yBPavvjtIx58Yg00YOOisyqn_0O8VI7f1rdJRGQFYfCGbYZWujvU4o98tMcGG47ae50",
    "domain": ".google.com",
    "hostOnly": false,
    "path": "/",
    "secure": false,
    "httpOnly": true,
    "sameSite": "no_restriction",
    "expirationDate": 1765000587
  },
  {
    "name": "__Host-next-auth.csrf-token",
    "value": "ab1c1bcecfe18f017ab6fa6e891376933672bf48541dc0df07fc1afb3764f95e%7C049e8c077e2a32a792380e19990e65f9fca1a7e6f3d587bfb6af7593b3af44d3",
    "domain": "labs.google",
    "hostOnly": true,
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expirationDate": 1783304053
  },
  {
    "name": "__Secure-next-auth.callback-url",
    "value": "https%3A%2F%2Flabs.google",
    "domain": "labs.google",
    "hostOnly": true,
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expirationDate": 1783304053
  },
  {
    "name": "__Secure-next-auth.pkce.code_verifier",
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..C24tsv8flW4qymeo.GAdbEvKs65uTz3OcD-UYrI2TRuNvR9LY8Rc2ChrNC_3ePUXcXZXMglqAjUgleHanUfxKZoCSMBJfJCkwqMY8E-n-uPg-7Xw2AmZPm-M6sIbzQk-9YQcfkRrFjYxKtUQ1zH1k0zzw0nY719_dJ7DFhh6JKiV_L4W9VmNvTXxLN-JfbfRdoW4.Qsdrm7Kn5ocWKf003CF1qg",
    "domain": "labs.google",
    "hostOnly": true,
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expirationDate": 1783304084
  },
  {
    "name": "__Secure-next-auth.session-token",
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..SE00BdhEHbGYbZh3.5ZVpmF6M946JDodumlH7AaH8hVtXgIkXwX66s6RK6NEBndlp8VQcQpoQh17syVbP5D8MdXHat4BfVp8dOl3HkJknTL5amM19KTMJ-VI9kUj2Bh2NWXv3GoZ_6HSoDIJb7wlEIbjpQKbn4-N42P2yZ2kM8EWn5LwVmDGkceMWKLth4swKI7iOsNBaLp_Jzz8wrydmBqbL_fKrMdiOPZNUIGf1qjOk8TB9Bkc1QFjms4YldAtLpSkXqNOHfi_rglBOx_KThD1sQe60yc-cB6p1tsO5ZfzZ3-kJFL2izW8GgnpS3mLUA9cK330JJhpFsoYPT61J03t1j4CFKvAIJgBcx8STV_MJGkzuR-mloM5GWXhTHQbzyJvD73vJV7yaa7neHLHbYF1jTtVTqgCF_331Okrwdx7xJUesEXEWyn_d_lKPNqv9ZPom5v_KSr8dM-SEKX2hPFgfkJKyVz8Q1_uTOpFa9W200mcjJBVv4R8Uz234dvXI1iMOCywABAUoV_HRqdEC6xjB_n8KxJgTrfWqkyU_61dwM8NXs6MhG6QAl3-_9JoXDWIhK1MsDp3Z6ETTFoOsrdYFI9cCFNV47sw3pPOI8WWo7IoAYqjR37HSPf8o1Zj6OJh4mTD7R-wPE0_Xzfrl-ptMBpAPwFfxSFc69TxiezPGLaG1exxTmmm6-VCsne_OpiY-kR_TrWHQREpE8G8AmeAnuVTj-Jl9nM-diLn8L8wW0JrCsi_nSs-MQPE1CdB7ZMwjgjWt0bPxsEW6feBXV40cjGHZ7FhgPYPk50n1d7yXNLuRyF9qdRgf5vD0ZQ9BL7t7Yzmz-aDBj7jED11-AI0NQ1C84cXKQidGmYln0FOMqvn0CSoxXBLQfrfWscwMjVKKt05_bF0Rc_uvcwT5SBqtXVLVcSdxTuFIR35tkxGxtdfX6pnWYvoHTu81DxF-VS7iXH--eNK8z53y2wFBno3OrL6R66m9mzgtp0J8QSxkUA.z8DtuTtIup1P1q7O2dfH_g",
    "domain": "labs.google",
    "hostOnly": true,
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expirationDate": 1783304114
  },
  {
    "name": "__Secure-next-auth.state",
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..dx-92KVfzNTZa7-y.WwmP98NR4kx4SroqoWqRAwtuNQ6iYQg4Q4ZwnuMysTF8IJ3PEuEolsjR79kXA0l6B20x3kVErvIYRA5mRt837yroiK0SkEVnPojuxzqDwyfIgHKTYxspIqyTSx50SCYe2KIypvtds2oeyrPyKFZldyNSA4l5LlkZ39tN7jm21VgzUdQTLFE.e3qYEOu1zpH2k0_HxrOWQA",
    "domain": "labs.google",
    "hostOnly": true,
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "Lax",
    "expirationDate": 1783304084
  }
]
"""

# ─────────────────────────────────────────────────────────────────────────────

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
    return jsonify({
        "licenses": LICENSES,
        "cookies":  json.loads(COOKIES_JSON),
    })

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
