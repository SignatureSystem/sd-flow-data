from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LICENSE KEYS
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "1": {"expires": "2027-12-31", "plan": "ultra"},
    # "2": {"expires": "2027-12-31", "plan": "ultra"},
}

# ─────────────────────────────────────────────────────────────────────────────
# COOKIES — paste Cookie-Editor JSON export between the triple quotes
# Go to labs.google → Cookie-Editor → Export → Export as JSON
# Also add NID from google.com the same way
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_JSON = """
[
    {
        "domain": "labs.google",
        "expirationDate": 1783460227,
        "hostOnly": true,
        "httpOnly": false,
        "name": "EMAIL",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "%22taikhoan13%404g5t.9iq.net%22"
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
        "value": "f5a92251c47b7dccd4213085b46f349f91ccfd822bb0be5615d073c3c6443733%7C8d76a31400e8cd0d60ea73fe8385a77f769e93192189a15e20d6b809d79b88f1"
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
        "value": "https%3A%2F%2Flabs.google%2Ffx%2Ftools%2Fflow"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1783463368.083995,
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Secure-next-auth.session-token",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..ajQSMns4EoHyI16j.UF9K_ft5-aegiXstlwRZckgkv_QapzbHCSpqcqoBtoblku_rUkCQ-N2Gx9I_fcg1omPUUBINNd8BDxCBxvE3kQJO6hLITWCaoGUf_JluorleF9y1enBqob1EUUW-fC3ZXlTMCsCMT3tcIRAGQx3vF3PcUk9M31-EU1llLr_BAN_swRvzEZh_bcg3bfkQ3xkZvUdod_VnF9gIocB1Nhh0BOKu_CtnrJsW43eVQ6BziTl1_-Pq3ZKwYpJWzF4f_VSWjU9MVSXp8e8MDH8pc_BkaaUN0gE_sqOQ6L9loPEMSAcVv8n_vRM3ANxTYRYJVsklgYcpt9gS7t6nXdxtMY1tXmEsLAFYRuLDPkUIb_gLZE-EwPXwPjo_cPss3VXaouIez3h1jj9MC53qsrVghx2JAcatJA9zzH7bk1LdyhxfEgxfzmjqV3mFPlWoGWwrDAONWUs7yO2dhB2Q1lyb20r1MYfTq5TpOfHhoy-BDtzHgOj7aJGPXK_qXdz8ukrXZpWP4eCBHu2Z9glsB9t_vuLWx8VdB28QQlkBToc8O3esq0tR2N6zdCYFYpLPNWyECqDw3fKpCfL0yPjyvD2Z0yywFCtM47r02Ax-EEzeqRPZZqe2K-vVoao8KRcNKhOOkTFq5iAeRLZ9r3pH8f_H9_eBe3nYnA-ss1qcJeoZcacJL-1FTR1iVHrh7V9Op6pYndtvXxynSwvF9AYguwKjQ-YYk6WlUXCBqVpYm0dQvfx8EX2pSUmkIxUP-T2N5wrzurUDZCDV90bIfaOFOrqPdS3jrcVgaoX1umFGlEy-L9xCrzh9go_ML8rT_icc4MXh_j399E_2CY6wb_fJ2QTVMMvNBBkrJUmOh2xk_AiWHtDu3_QjFhZ7kQbxLjjLeIAHoPNLjI6UbAngmc_buO-WWYir8rmvspsY00pxoddLtWRgNcQ-Ea3AHvZ6w65gIdNT8OhcuHxp-0AdynIDBQmufvF9XnLejgN5gBNnTg.2jvKX2kFlwNLCcv051Qc4Q"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1815428977.009128,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GA1.1.1651406568.1780868025"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1815429145.143822,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga_X2GNH8R5NS",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GS2.1.s1780868024$o1$g1$t1780869145$j60$l0$h1271116482"
    },
    {
        "domain": "labs.google",
        "hostOnly": true,
        "httpOnly": true,
        "name": "email",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": true,
        "storeId": null,
        "value": "taikhoan13%404g5t.9iq.net"
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
