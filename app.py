from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LICENSE KEYS
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "1": {"expires": "2027-12-31", "plan": "ultra"},
    # "SD-ULTRA-NAME-0002": {"expires": "2027-09-01", "plan": "ultra"},
}

# ─────────────────────────────────────────────────────────────────────────────
# COOKIES
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_JSON = """
[
  {
    "domain": ".google.com",
    "expirationDate": 1796555653,
    "hostOnly": false,
    "httpOnly": true,
    "name": "NID",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "532=dorXFIqjbAxRB3SnZloTFKcpacFTC84eKcbVHIdHvdinoxENeEygzh7QV4O7r1dKiJ0n0FrCE1gtBI9b9OAWlHpMLauUiE-sX3Ro4tIQVrSLPDVhTKtD9Eu3XTtwn_iwByU73PdH0ZlIB7uGYVNwMMg71HscDTp_HGLiI4g3Xa1b9KC35wLQbqtG2a4myaKdiD8vdWyAAAC62dtFDvDeZaa7ZCbUCOgDhEA"
  },
  {
    "domain": "labs.google",
    "expirationDate": 1780841622,
    "hostOnly": true,
    "httpOnly": true,
    "name": "__Secure-next-auth.pkce.code_verifier",
    "path": "/",
    "sameSite": "lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..C24tsv8flW4qymeo.GAdbEvKs65uTz3OcD-UYrI2TRuNvR9LY8Rc2ChrNC_3ePUXcXZXMglqAjUgleHanUfxKZoCSMBJfJCkwqMY8E-n-uPg-7Xw2AmZPm-M6sIbzQk-9YQcfkRrFjYxKtUQ1zH1k0zzw0nY719_dJ7DFhh6JKiV_L4W9VmNvTXxLN-JfbfRdoW4.Qsdrm7Kn5ocWKf003CF1qg"
  },
  {
    "domain": "labs.google",
    "expirationDate": 1780841622,
    "hostOnly": true,
    "httpOnly": true,
    "name": "__Host-next-auth.csrf-token",
    "path": "/",
    "sameSite": "lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "ab1c1bcecfe18f017ab6fa6e891376933672bf48541dc0df07fc1afb3764f95e%7C049e8c077e2a32a792380e19990e65f9fca1a7e6f3d587bfb6af7593b3af44d3"
  },
  {
    "domain": "labs.google",
    "expirationDate": 1780841622,
    "hostOnly": true,
    "httpOnly": true,
    "name": "__Secure-next-auth.callback-url",
    "path": "/",
    "sameSite": "lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "https%3A%2F%2Flabs.google"
  },
  {
    "domain": "labs.google",
    "expirationDate": 1783336423,
    "hostOnly": true,
    "httpOnly": true,
    "name": "__Secure-next-auth.session-token",
    "path": "/",
    "sameSite": "lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..DLKZRKeBYcITIu2a.4819JwuvPDeUBr8Mv2FXkR0EfXJ4RZGaP3jXJRgsV85bRV37XpAhn65EwFFbNVRe4Rs2tMI-FRNBYPWA__1_KivAhhZ4kA_sR8oaGBfuVcP6EjCTsFnW3Bk69RTVIA2XFHIpGrby9RWYgsWZD1DqOaAwOExnqD5mleY4ahP2wJ5oo82rXwzPX4l2ssFUMyCbtXjGRLRRA6yEWPOuJJBH-wvhQINue15WpRS3c58rC39Al487V-Od3-18OeapJSPEZHyvY3VsfB-h2teh0n6asjdUngOvlPaZuAX_TRUU4vG43odUJx64_iiZAB6A2eljma42p9devfvAi3Hj0JA6TFr6ayJjXFOFwi418K9Oa-kKTHDLSlEUS6aE6L0OlrP6nA6sfb_avVM1ZSxgTiaiKifpLwk8VFZhg_dMalivIs5WsbPJSmRTW5xDuncJtZTx2ViY9C2cwczNNxxJgdgVGRNkV7hk79j4Fyk5Rmpd7GT40_kFqfc4zjCsVCaE81L2Q3KADi28s6AqKQpU4B7YooEkmJHWLGufgFwp8ZnDw4jXuJtPH2A-VfcirwJd2xJoGMVrDBQ7J3LdClB_B-XhBdBMAAbkS9aWmb5wvfO_ihihzmYOrCwVRJn8d6bq1e_tVQHqivTXOSUre4GA40kOPS5LM8XsdJDrDYmX6cGMOSzImm9yoGJJ6UqB0kzlKQXRTHt9aODMgvkOxuAxZM3tiy35ao3UHZTCqmitRXcUVB9slX1kjCPxbzuXAJVxB1zKrvMrgoF5S2fbN8wusrtGpqF65Rmjj8QDQnJtjrNmunlGYpaz1-VXOXU3Eo8Z7U1p9UcGDo-oV8-QSRraCP-P8xQauqvcMF1zTnkHx0PVJIROcw1A0OOGAX_EA1l-0X4fWr9rMsUgVJy23VdOzisBNOQf55xCIzcq5CJFGOj4oUkJcZgVZxmnqRI4bPpjjmKqw8FI7IqiWsntnI48bcH4kagjIA.z-zSaj2hOyIPaCJ7tycOZQ"
  },
  {
    "domain": "labs.google",
    "expirationDate": 1780841622,
    "hostOnly": true,
    "httpOnly": true,
    "name": "__Secure-next-auth.state",
    "path": "/",
    "sameSite": "lax",
    "secure": true,
    "session": false,
    "storeId": null,
    "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..dx-92KVfzNTZa7-y.WwmP98NR4kx4SroqoWqRAwtuNQ6iYQg4Q4ZwnuMysTF8IJ3PEuEolsjR79kXA0l6B20x3kVErvIYRA5mRt837yroiK0SkEVnPojuxzqDwyfIgHKTYxspIqyTSx50SCYe2KIypvtds2oeyrPyKFZldyNSA4l5LlkZ39tN7jm21VgzUdQTLFE.e3qYEOu1zpH2k0_HxrOWQA"
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
