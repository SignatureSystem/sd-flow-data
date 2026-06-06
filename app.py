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
# COOKIES — Export from Cookie-Editor as JSON (not Netscape)
# On labs.google → Cookie-Editor → Export → Export as JSON
# Paste the entire JSON array below between the triple quotes
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_JSON = """
[
    {
        "domain": ".labs.google",
        "expirationDate": 1815297804.518073,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga_X5V89YHGSH",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GS2.1.s1780737804$o2$g0$t1780737804$j60$l0$h0"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1780840053,
        "hostOnly": true,
        "httpOnly": false,
        "name": "EMAIL",
        "path": "/",
        "sameSite": "lax",
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "%22marlenkunze63%40gmail.com%22"
    },
    {
        "domain": "labs.google",
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Host-next-auth.csrf-token",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": true,
        "storeId": null,
        "value": "7dc6a434f7163934d70c7dfe089a8300e850f0ac99799331a588d02d0f43038a%7Cbf6d37196ec46d2e8778f522a2efbaba9736d4333b08420fab61ea18defa8579"
    },
    {
        "domain": "labs.google",
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Secure-next-auth.callback-url",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": true,
        "storeId": null,
        "value": "https%3A%2F%2Flabs.google"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1783334855.928762,
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Secure-next-auth.session-token",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..P0TmkN9Z8TnUaEVa._75eIonV_PJUgmvOeLEzMP0qz4YH4fdSyDY1XnB_PfWAn-QIXwCF_bjGjlWqtl3Di8ItJ12y5eNIxqWQkg_Ew-R29LwLayVToSyR6Ik2N0s8JCgAPuBCvfKPFbeJIuUnH9v6Fn2-lwYYMc0mSwv3UVSsov_gXKmibLglPNihFUoXw09qpcqD_KrRWJLoVM5INOgivo1XLRfGazmOF6JcBP0xOqC85RGYkwsBEzkTWjq_yjnlxlFjmZ_cxl17QrIacWm28yAjXVivXlDkjaZrsykl1lcPi9T-1VHM2ZJ2rF2pEw63ZqkJVcTxCF1Qzf3ktGywdJKDnP1ZvRraE3jQUxAKI7tEEY7j5fCzFnmvgioSAG9QoR33dKMYkYvkOZbVikJEeOlwt6hP6Qbm6gYDL2xUOm_GRni5Azm9oNIAPknq-vlOLWSTqJrlqjVYOhBemY192OHd05BJ5qRT5bO-Lr7kjWtxUg2xs9dvQ7zUE9MMtrWVLVQIxA1yHftaOaAEbGKoOgU4AiHDYn1LcwdgL_83RoinkDTQfzX8SP9pxmdnLlHN1BTG9GC-kVB34QSucxgnKT79aTbKuZuKSsALhG2HOIQMR3ntOBVW0KXmnc5yPq3BFi6utV12cXbJEUM-BrQNblu3DdILefWbKN93OUDNeXhwGFBsHay707EuOQ2bdNHygsaioubBVlUj0NHioIL4_f_Sm6xU8gC-MJrhJ1dGBTgEuNyVHBkZ0tBap0csQ2RNG1Qw1FV2HuZuS4RlPsIA0UTZRa_Y3RJuS0cwllC0_9vUDf9V1_KF_x5g-B3FFWqNLOmJfnLOkYEtZ-XBV3J_RwUSA1jdzrysf4R2B7gOR37XyNliYOQImdDqchFxLXTB9LDNugbotu26h_vBVtTgO5RV2RrL2IsBK9cvsMFQKb9VQS7-hsQ4Tzdal0SC3bbNul-76xNMr4tOkO3-h9M0sE8_RQcI5GvuXFphxvrnxj18sFcfBA.5vmAfIHruknL_mvivX8jJw"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1780840053,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga",
        "path": "/",
        "sameSite": "lax",
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GA1.1.2088551338.1780457807"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1780840053,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga_X2GNH8R5NS",
        "path": "/",
        "sameSite": "lax",
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GS2.1.s1780720581$o5$g1$t1780720589$j52$l0$h1051652884"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1780840053,
        "hostOnly": true,
        "httpOnly": true,
        "name": "email",
        "path": "/",
        "sameSite": "lax",
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "marlenkunze63%40gmail.com"
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
