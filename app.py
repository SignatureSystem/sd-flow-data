from flask import Flask, jsonify, request
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
# COOKIES — paste the full Netscape export between the triple quotes
# To update: go to labs.google → Cookie-Editor → Export → Netscape
# Also paste the NID cookie from google.com manually at the top
# ─────────────────────────────────────────────────────────────────────────────

COOKIES_NETSCAPE = """\
# Netscape HTTP Cookie File
.google.com	TRUE	/	TRUE	1796555653	NID	532=dorXFIqjbAxRB3SnZloTFKcpacFTC84eKcbVHIdHvdinoxENeEygzh7QV4O7r1dKiJ0n0FrCE1gtBI9b9OAWlHpMLauUiE-sX3Ro4tIQVrSLPDVhTKtD9Eu3XTtwn_iwByU73PdH0ZlIB7uGYVNwMMg71HscDTp_HGLiI4g3Xa1b9KC35wLQbqtG2a4myaKdiD8vdWyAAAC62dtFDvDeZaa7ZCbUCOgDhEA
#HttpOnly_labs.google	FALSE	/	TRUE	1780841622	__Secure-next-auth.pkce.code_verifier	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..C24tsv8flW4qymeo.GAdbEvKs65uTz3OcD-UYrI2TRuNvR9LY8Rc2ChrNC_3ePUXcXZXMglqAjUgleHanUfxKZoCSMBJfJCkwqMY8E-n-uPg-7Xw2AmZPm-M6sIbzQk-9YQcfkRrFjYxKtUQ1zH1k0zzw0nY719_dJ7DFhh6JKiV_L4W9VmNvTXxLN-JfbfRdoW4.Qsdrm7Kn5ocWKf003CF1qg
#HttpOnly_labs.google	FALSE	/	TRUE	1780841622	__Host-next-auth.csrf-token	ab1c1bcecfe18f017ab6fa6e891376933672bf48541dc0df07fc1afb3764f95e%7C049e8c077e2a32a792380e19990e65f9fca1a7e6f3d587bfb6af7593b3af44d3
#HttpOnly_labs.google	FALSE	/	TRUE	1780841622	__Secure-next-auth.callback-url	https%3A%2F%2Flabs.google
#HttpOnly_labs.google	FALSE	/	TRUE	1783336423	__Secure-next-auth.session-token	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..F-Kqa3_4kwM04HoT.GZwvTvD0CBIQ6VBWjHZrZEJqVX2UiXIcPxScU5r5JYnYrKSrPqZCZ_dAf9PUi0lE06HeJk0CT1xcy-DcC3ZLJ0bALCTRKPMj7dvSLjJxcRpakyKzcishReb-PNjcpriRwp-SbLBc3K7MnCQFwpRctd9PZBIekykFRHKQ6VvtAtFPR0zOaHlMfTxY5i1p7PrREJRCUoZYBMYp3S8rQYR7t28HGSpCP0vKB1eK0KZs2jVmcjbEyDyEt5QE-bipz4GpW17Su6AJWiD19c6VycxIgyqAOzX4VgFj-WjVzbw1aXOJWSJBVscb9kd4bLpG_u7qtzmX6FvbrFxAHednD2koav0ExTgBFGvFhhd2Gm7At5iBqkR418tu20fFf0ygjMOAtb4v3eFKbTwmAuN9fRyooqWK92F6vdJCH0-CNK10hbSRAv2GBRxVIj3IPsWDLq5Cn5KLkMliZmQYFzSxyAg5fjlUGvwymIN91GZkMglDUUhwo9m86TpS7IpM7Yh83HftZz6S61SvfBDPbqgr17S_ol76lSWkkgmPC0AucV_B8h1wzIG_QyYgRXHEj3s38E6H6OzPDn1ox4iXBEGy0oQTD2tVAmSlq6sJDiHXALpBjrld0rbhiwhzzQ0b3UFSY1EvKJrKeDxGBigxiMsRafCLTs3fn3vYNuZqq-RkXBK5ZXOKjEhS1_ECnxu2K6LYWTdyNtHhyVFu_fztHb9xkYdkZ641upiqk4IP8aanBSbns4gLKN7rQuZ2xhXAj2HvHF-wuVpaArI_5e9PiV8vF7RGypmwKyhTUaL9qOkDU_tis4q6QPF87N91XVty3H0dgKkx2ZSB0cIZO5V87rO11Ryr0jUcZhgSnlvEvWHdCKV9RnN-TwMGoAO8UfQqScQcndVx9aMjPbCQ_kRFgiySxKhn7Nb9efmcQEAWTI5U_VEYsf-TC5QTwMFNO_Assz49WiqxVHivPi7pFdA4lniwGSC62nKiDg.uoGzQqgHamfcRNuFvyMJWA
#HttpOnly_labs.google	FALSE	/	TRUE	1780841622	__Secure-next-auth.state	eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..dx-92KVfzNTZa7-y.WwmP98NR4kx4SroqoWqRAwtuNQ6iYQg4Q4ZwnuMysTF8IJ3PEuEolsjR79kXA0l6B20x3kVErvIYRA5mRt837yroiK0SkEVnPojuxzqDwyfIgHKTYxspIqyTSx50SCYe2KIypvtds2oeyrPyKFZldyNSA4l5LlkZ39tN7jm21VgzUdQTLFE.e3qYEOu1zpH2k0_HxrOWQA
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
        "licenses":        LICENSES,
        "cookies_netscape": COOKIES_NETSCAPE,
    })

@app.route('/', methods=['GET'])
def index():
    return 'SD Flow Server is running.', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
