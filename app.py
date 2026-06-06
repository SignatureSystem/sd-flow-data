from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# YOUR DATA
# ─────────────────────────────────────────────────────────────────────────────

LICENSES = {
    "SD-ULTRA-TEST-0001": {"expires": "2027-12-31", "plan": "ultra"},
}

COOKIES_NETSCAPE = """[
    {
        "domain": "labs.google",
        "expirationDate": 1783295421,
        "hostOnly": true,
        "httpOnly": false,
        "name": "EMAIL",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "%22rafixspark%40gmail.com%22"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1815264108.273548,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GA1.1.35101338.1780703426"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1815264109.45904,
        "hostOnly": false,
        "httpOnly": false,
        "name": "_ga_X2GNH8R5NS",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "GS2.1.s1780703426$o1$g1$t1780704109$j53$l0$h1117841660"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1780801312,
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Host-next-auth.csrf-token",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "aa6e511cba57faf001ee2ff2ed431acb742d34f7cfe1a896f67d1bc8102260ff%7C72143fc15bbe298f51ed759063cfb09884c4c8f389e075bc91f9b276aad7bbb5"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1780795850,
        "hostOnly": false,
        "httpOnly": true,
        "name": "__Secure-next-auth.callback-url",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "https%3A%2F%2Flabs.google%2Ffx%2Ftools%2Fflow"
    },
    {
        "domain": ".labs.google",
        "expirationDate": 1783290659,
        "hostOnly": false,
        "httpOnly": true,
        "name": "__Secure-next-auth.session-token",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..aKA_Hq_fxesNNe11.L99QZrBGZo4CQi7uK4Lsp1MY64cm2irVrqkKEygrd-MtLH9rqcL0sgw4yCVheJyFhw5dp6jzzvW4DE-NcMZ4D40BmSc_CJfkIxuhlvbsoyXMPsiP_owxRLM5xCqmNkSmaC_WifgiJkXfdLVwHRDAMlU0VrCLJjle7baSt8phHSQ7WNKSmHAgqassfq7roFQIRNpBuh3GiT06qAzX49F29kaByGGRY-9oMv3iJIY0tMP_d4e5Luzo0eI_TTGuf6EKkZgdIvMvICMOxAkFVN6jsx3_fAWsD_CVWsMOGYPCxI836y1CkiMz6JtfhsW6OOQgvHFAm_VIZTJttIjp6Z1pI5oQZWJb8zrmXw-rvBr0U-Flq_2wpQZwrD8oob79efohZh4ieM9V_7lg64jYkZ5_DZmsdb3PBYVEWXihp9yNRmxFk050TfDV3hqRolKgIDj1OEmoFGk8HBwG5ehoAIYf7Uai2c7-yPz5Y79-FPYjv6-PYYXMvW5BNvlSksI8QMeMe7L9bQzV2gxdNo7Om1a8BqRxIDnXxXtQlszRotEejxj6aPNeGgnY54ITPoMsUNMEIVtv2lVcGy0d6rVN21gYxTw8BcNpSBMFkA4mz5KjZJH8sKI0gZtcxDHIB-0222t2MsVIiaQVzmVGHeP4nbEae-oHuR_JKKADL7pyet4r1JgZ-9uWG-Spi3jcS5Ovao2HlLlcJsknj9JPAi1yXDIsqPxu2ja05aY4YUgs-ISYABTqUeqfhUBFtq_SnwJY-NG59HDoPSSZ6VU5973Rhjyi4Dq0b1OCpsEjGNQa1v2kzeLhOL61hRNMinICA3mmdqeCO278d9o4B18gDd2_QeXy-PT2oPITPnwFlsfhXjzLeUom4EeyCg_qPh2m27X2suHmzVg31-YMCIgfBEZpok6nF8LwhDldL4skpxqruw7gAhY3Dm6A99XX-KtdVDMijU8AT2bPjMOjsfKYRGow6v8JRX4V5tWn_w.9bPRcDwI-HN1rm2900jxAQ"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1780801312,
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Secure-next-auth.callback-url",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "https%3A%2F%2Flabs.google%2Ffx%2Ftools%2Fflow"
    },
    {
        "domain": "labs.google",
        "expirationDate": 1780801312,
        "hostOnly": true,
        "httpOnly": true,
        "name": "__Secure-next-auth.session-token",
        "path": "/",
        "sameSite": "lax",
        "secure": true,
        "session": false,
        "storeId": null,
        "value": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..iHn8BCJnkUc7LcOn.dl609EgJgzyfylFhmDmpsv8BK8kN3S_d0REPUMglX5nb9N6g_3UoQoxmFCcoPINXNYjLWD73kN465UV2eZutl0XhV1jQlrGFr2RAKAVo7Orlpc7-MMdOAO_DvNYU-TxO-PZI4Km0VboItOl_dmdm5hrkXMA8d6mDtFGjk1p4H5nbXkoD0KYHvYYL-abQXuJRJfP4rQ72hmQ2_LP6g7Yw-NnW4hr3tftceYJ7mfNFviS01IuRHXCaSArwTavBfdy-eJS_Y5DI4yy7EjH83VMyH2N4iVS98Z0EANOjsFhh7SI8Y31Q5FGW5FkPnNkitH7RyJcB2oTOdJbjXCY-AsyWQjehHTuJhPDk8pKTCQfPpEeVMJ-tKUjI5jkMtYPF5JPLel1Nb9LTOVWV_YeQZjyZzxDZ83TegUWn0FQefjJsid7yIyFSSt2Nwc4OCOttRqm8GOlJEymNcSI2bGPUZFuhDxFDvOcsn5gM9VlWxCrNJWV5hrMgcMpaA4G-9jGm7O0wwZcmmI5V4mxVEP_9AR9RgUSp1Nt4ZfrHgJhnicPpZQF1iV9ech0obJEORTXoY9ayGs9FmY7FK9a6apof55S8Ic0oCMHAlassq6lF4lyeHE8hwmix7fagq8N7_rHzkA5jSkhmDoSd0ygxZOLHzOpkebGgsYkAlzvCbHLluYoSgHwXnJG0iwCZsVZga0KAOTRG6cvxaDHjoYs5gwtnoe-SAAg8N7v8Ab_t6mZe01EMj8L--jjO8cc-b70w5hUvnZgBP5Pk7Az1ol4iUzQHIvBRfJ8-vVLd418tq2QsDTcbnoo28f1Da6JOhrDurO5fJAIioMM9lYf8OAvOu7fW5qP8EBNlAfPljVdd2NPRcV0zLpfGH339Td8PXxyqtuUlMIJj5lw2IA0xASskuoDs9YQLaXKFoFYluTSFAme9llRadg_US6IFC1sCBzGgdYaeS9iYdvdUzK8jkFvZ7X0g_Bo1YclLK2y7UmCf0g.R16XB_JaI7ouOR1eeQoHMQ"
    }
]
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
