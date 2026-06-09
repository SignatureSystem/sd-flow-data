from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LICENSE KEYS
# Key → { "expires": "YYYY-MM-DD", "plan": "ultra" }
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "1": {"expires": "2027-12-31", "plan": "ultra"},
    # "2": {"expires": "2027-12-31", "plan": "ultra"},
}

# ─────────────────────────────────────────────────────────────────────────────
# COOKIES — Netscape format
# HOW TO GET THESE:
#   1. Log in to the Google account on labs.google/fx/tools/flow
#   2. Open Chrome DevTools → Application → Cookies → labs.google
#      ALSO go to Cookies → .google.com (for NID)
#   3. Install "Cookie-Editor" extension
#   4. On labs.google page → Cookie-Editor → Export → Netscape → Copy
#   5. Separately: DevTools → Application → Cookies → google.com
#      Find "NID" cookie, note its: domain, expiry (Unix), value
#      Add it manually as first line after the header (see example below)
#   6. Paste full result below, replacing COOKIES_NETSCAPE
#
# REQUIRED COOKIES (must all be present):
#   From labs.google:
#     __Host-next-auth.csrf-token   (httpOnly)
#     __Secure-next-auth.callback-url (httpOnly)
#     __Secure-next-auth.session-token (httpOnly) ← MOST IMPORTANT
#     EMAIL
#     email
#     _ga
#     _ga_X2GNH8R5NS  (or whatever GA4 ID your account has)
#   From .google.com (add manually):
#     NID
#
# NOTE: Cookie-Editor exports #HttpOnly_ prefix for httpOnly cookies.
#       Keep it exactly as exported — the parser handles it correctly.
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_NETSCAPE = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

labs.google	FALSE	/	FALSE	0	EMAIL	%22taikhoan13%404g5t.9iq.net%22
.labs.google	TRUE	/	FALSE	0	_ga_X5V89YHGSH	GS2.1.s1781002864$o2$g0$t1781004071$j60$l0$h0
labs.google	FALSE	/	TRUE	0	__Host-next-auth.csrf-token	c3ad4d9a6a6c646ebed8bd33b2f76f36202eab106b6c3fc041fbbd1a851d5346%7Cdf1de7e00c67a5a5914aa11da0304da56f605bbaaf3df420d869171cd02037ea
.labs.google	TRUE	/	FALSE	1815582268	_ga	GA1.1.300102121.1780935043
.labs.google	TRUE	/	FALSE	1815582268	_ga_X2GNH8R5NS	GS2.1.s1781022264$o10$g1$t1781022268$j56$l0$h990588533
labs.google	FALSE	/	TRUE	0	__Secure-next-auth.callback-url	https%3A%2F%2Flabs.google%2Ffx%2Ftools%2Fflow
labs.google	FALSE	/	TRUE	1781023169	__Secure-next-auth.state	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..jAooH4CopS6n9dc0.J1smO7JXogoNK16Td-uUQr8Z8yVcDYl6yEM7DSyYwHmNqg9CPZrc2U-0iBl3Dtys0ltVwsQMV2YbNtce76Mqu7ljq0BAoFxcwxOOK4Z1NShBcOadUHwc52bACJBeFqvgr2m3givJ6JJY1BGLcFa0vhOb9UoQ7lgIfgI3UU4A0NCIAVw_CfY.Ks6qG4oJR1f52V9Rs-QlIQ
labs.google	FALSE	/	TRUE	1781023169	__Secure-next-auth.pkce.code_verifier	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..b3avq5BZEgS2wNtN.pWpiK6AMNREMPY4xauXUuMA44BvqoUoR2lzZits_Mmjq0-yH2zaXMvxDFFVdJ3auLM1K4Owsc-JpMXkcRe2dQBNksEZT6xisRdGtvUUWl5bF4UVaj4EmVtEFwp69GPpvkThiskg1klD5daMSiLnFW6VvM5nYtQ4wD3v6WRWoi6CtyfCAHWs.2eL6l_0ZI-kSwDq-rSqUoQ
labs.google	FALSE	/	TRUE	1783614317	__Secure-next-auth.session-token	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..V3ME-RqENvY0CA6n.Lh3vuS_YmOH-j70XHpwtzq5EqmwIPf2u_oBIa3R70LHrvXBRSBzEaVmVIhwbiSesc8oZWPctz3g5PKT7bUGv-GleyDtRgpxkWD6CCXxUa5amd57bQX5omMZy4PAolE7pzSHvkA6P416GpCTQ2LZn9_ChN4MjKSdG138HvYaXVWe17VM52M62D_vkfkCsOBM6QjuxpNqJsQ5PEB0t5SPFrqjpO1K7_cimS4igG2b4OpHdYOw8dKHPRMEJx8SWcuKH6YXttwdFotSumUFUTSm2iiIviu3BcHVey_MrdW_RWkWcso494T3FjFnD8V67Q7KZvCvFOGFuTfzEY8aGYT8QYqnMvKZ6nkZb2LhkS67WrGe2CzBCG08VRIc4ObUSeNafasZAmwJi-PvxOyaDzqbkwXVPvIZRrFvn9irDh_Srk7SzjE6gzvlqx0_jG0PExLQStGE4rPkFYqFMZLN_TviLKVWUUqaLjkE15cu1QLBR2haJm2TVprFqUkNKfhtSjhSF7OaaNKwj5eMeZ0e5vRM5cyJR5NoC5YEGiwxpYHxbh0Wgm25DpCLZYgRC-GsLyaavrQIaK8UB38fHl4ksUlEPzfNxZT9o6yQLT800uhnqOo8Al1AEHHPvZaJWiYQhh5Kd2crGbG-UQRIz8EWJBMzuPWP6Q6jmX38W-rWW9OpwD_aI1Z50lO8RIa6eJ3k0HXx5Ztgg8RYnb2XRdvPFfl-sbwhC8sD1qk7wKUrX4dL28bHkMtev-a4hyEShyMDR1iY4WcR8BDyVE3k6FKQOhxj5idrcPpczC6HDNeAFwERF_kM-18rU1IA-1Bsb2iSxpuzaNNSBTzPAFLYPEnSLKTrYMn7sFUniB5YMRbh7QNCtG6FNYJKE9JhBpnMKbCeXlxd3W0ot96YEnkYvtAoS38Ccrxe_LPHyk4Aw2V-qFa80fzThGISWVaHGwSEFrqFqynQjvZ1QKGt2udrfr7FhswpyHbemJSDgquKQOak.614VbSfPbKX2EMdzwna6yw

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
    # Returns JSON compatible with both the old extension and the new one
    return jsonify({
        "licenses":         LICENSES,
        "cookies_netscape": COOKIES_NETSCAPE,
    })

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
