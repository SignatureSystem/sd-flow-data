// ==UserScript==
// @name         SD Flow Access
// @namespace    https://signaturedigital.asia
// @version      1.0.0
// @description  Signature Digital — Google Flow session injector
// @author       Signature Digital
// @match        https://labs.google/*
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      raw.githubusercontent.com
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ── CONFIG ────────────────────────────────────────────────────────────────
  // Replace with your own GitHub raw URL after you create the repo/gist
  const DATA_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/flow-data.json';
  // ─────────────────────────────────────────────────────────────────────────

  const PANEL_ID    = '__sd_panel__';
  const KEY_STORE   = 'sd_key';
  const EXP_STORE   = 'sd_exp';
  const PLAN_STORE  = 'sd_plan';

  // ── Helpers ───────────────────────────────────────────────────────────────

  function today() { return new Date().toISOString().slice(0, 10); }

  function isExpired(dateStr) {
    if (!dateStr) return true;
    return dateStr < today();
  }

  function fetchData() {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method:  'GET',
        url:     DATA_URL + '?t=' + Date.now(),
        headers: { 'Cache-Control': 'no-cache' },
        onload:  r => {
          try { resolve(JSON.parse(r.responseText)); }
          catch (e) { reject(new Error('Bad JSON from server')); }
        },
        onerror: () => reject(new Error('Network error — check your connection')),
        ontimeout: () => reject(new Error('Request timed out')),
        timeout: 10000,
      });
    });
  }

  // ── Cookie injection ──────────────────────────────────────────────────────

  function nukeExistingCookies() {
    // Expire every readable cookie on this domain
    const pairs = document.cookie.split(';');
    const domains = [
      'labs.google', '.labs.google',
      '.google.com', 'google.com',
      '.google', 'google',
    ];
    const paths = ['/', '/fx', '/fx/tools', '/fx/tools/flow', '/fx/api'];

    for (const pair of pairs) {
      const name = pair.split('=')[0].trim();
      if (!name) continue;
      for (const d of domains) {
        for (const p of paths) {
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; domain=${d}; path=${p}`;
        }
      }
    }
  }

  async function injectCookies(cookieList) {
    nukeExistingCookies();
    await new Promise(r => setTimeout(r, 150)); // let deletions settle

    const exp = new Date(Date.now() + 24 * 3600 * 1000).toUTCString();
    let count = 0;

    for (const ck of cookieList) {
      try {
        const parts = [
          `${ck.name}=${ck.value}`,
          `path=${ck.path || '/'}`,
          `expires=${exp}`,
        ];
        if (ck.domain)   parts.push(`domain=${ck.domain}`);
        if (ck.secure)   parts.push('secure');
        if (ck.sameSite) parts.push(`samesite=${ck.sameSite}`);
        document.cookie = parts.join('; ');
        count++;
      } catch (e) {
        console.warn('[SD] Could not set cookie:', ck.name);
      }
    }
    return count;
  }

  // ── Styles ────────────────────────────────────────────────────────────────

  GM_addStyle(`
    #${PANEL_ID} {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 2147483647;
      width: 280px;
      background: #111827;
      border: 1px solid #374151;
      border-radius: 14px;
      padding: 16px 18px 14px;
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
      font-size: 13px;
      color: #d1d5db;
      box-shadow: 0 20px 60px rgba(0,0,0,0.7);
      user-select: none;
    }
    #${PANEL_ID}.hidden { display: none; }
    #${PANEL_ID} .sd-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 13px;
    }
    #${PANEL_ID} .sd-title {
      font-size: 13px;
      font-weight: 700;
      color: #fff;
      letter-spacing: 0.3px;
    }
    #${PANEL_ID} .sd-badge {
      font-size: 10px;
      background: #1d4ed8;
      color: #93c5fd;
      padding: 2px 7px;
      border-radius: 20px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    #${PANEL_ID} .sd-badge.connected { background: #14532d; color: #86efac; }
    #${PANEL_ID} .sd-input {
      width: 100%;
      box-sizing: border-box;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 8px;
      padding: 9px 11px;
      color: #f9fafb;
      font-size: 13px;
      font-family: 'Courier New', monospace;
      letter-spacing: 1.5px;
      outline: none;
      margin-bottom: 9px;
    }
    #${PANEL_ID} .sd-input:focus { border-color: #6366f1; }
    #${PANEL_ID} .sd-input::placeholder {
      color: #4b5563;
      font-family: -apple-system, sans-serif;
      letter-spacing: 0;
    }
    #${PANEL_ID} .sd-btn {
      width: 100%;
      padding: 9px;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.15s, transform 0.1s;
    }
    #${PANEL_ID} .sd-btn:active { transform: scale(0.98); }
    #${PANEL_ID} .sd-btn:hover  { opacity: 0.88; }
    #${PANEL_ID} .sd-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    #${PANEL_ID} .sd-btn-connect    { background: #6366f1; color: #fff; margin-bottom: 7px; }
    #${PANEL_ID} .sd-btn-reinject   { background: #1d4ed8; color: #fff; margin-bottom: 7px; }
    #${PANEL_ID} .sd-btn-disconnect { background: #1f2937; color: #9ca3af; font-size: 12px; padding: 7px; }
    #${PANEL_ID} .sd-msg {
      font-size: 12px;
      border-radius: 7px;
      padding: 7px 10px;
      margin-bottom: 9px;
      text-align: center;
      display: none;
    }
    #${PANEL_ID} .sd-msg.ok      { background: #052e16; color: #4ade80; border: 1px solid #166534; display: block; }
    #${PANEL_ID} .sd-msg.err     { background: #1c0a09; color: #f87171; border: 1px solid #7f1d1d; display: block; }
    #${PANEL_ID} .sd-msg.loading { background: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; display: block; }
    #${PANEL_ID} .sd-footer {
      font-size: 10px;
      color: #4b5563;
      text-align: center;
      margin-top: 8px;
    }
    #${PANEL_ID} .sd-plan-info {
      font-size: 11px;
      color: #6b7280;
      text-align: center;
      margin-bottom: 8px;
    }
    #${PANEL_ID} .sd-plan-info strong { color: #9ca3af; }
    /* Minimised pill */
    #__sd_pill__ {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 2147483647;
      background: #111827;
      border: 1px solid #374151;
      border-radius: 20px;
      padding: 7px 14px;
      font-family: -apple-system, sans-serif;
      font-size: 12px;
      font-weight: 600;
      color: #9ca3af;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,0,0,0.5);
      transition: all 0.15s;
      display: none;
    }
    #__sd_pill__:hover { color: #fff; border-color: #6366f1; }
    #__sd_pill__.visible { display: block; }
  `);

  // ── Panel builder ─────────────────────────────────────────────────────────

  function buildPanel() {
    const key  = GM_getValue(KEY_STORE, '');
    const exp  = GM_getValue(EXP_STORE, '');
    const plan = GM_getValue(PLAN_STORE, '');
    const live = key && !isExpired(exp);

    const panel = document.createElement('div');
    panel.id = PANEL_ID;

    if (live) {
      panel.innerHTML = `
        <div class="sd-header">
          <span class="sd-title">⚡ SD Flow Access</span>
          <span class="sd-badge connected">Active</span>
        </div>
        <div class="sd-plan-info">Plan: <strong>${plan || 'standard'}</strong> · Expires <strong>${exp}</strong></div>
        <div class="sd-msg" id="sd-msg"></div>
        <button class="sd-btn sd-btn-reinject" id="sd-reinject">↻ Re-inject Cookies</button>
        <button class="sd-btn sd-btn-disconnect" id="sd-disconnect">Disconnect</button>
        <div class="sd-footer">Signature Digital · signaturedigital.asia</div>
      `;
    } else {
      panel.innerHTML = `
        <div class="sd-header">
          <span class="sd-title">⚡ SD Flow Access</span>
          <span class="sd-badge">Locked</span>
        </div>
        <input class="sd-input" id="sd-key" type="text" placeholder="Enter your license key" autocomplete="off" spellcheck="false" />
        <div class="sd-msg" id="sd-msg"></div>
        <button class="sd-btn sd-btn-connect" id="sd-connect">Connect</button>
        <div class="sd-footer">Signature Digital · signaturedigital.asia</div>
      `;
    }

    document.body.appendChild(panel);

    // Minimise pill
    let pill = document.getElementById('__sd_pill__');
    if (!pill) {
      pill = document.createElement('div');
      pill.id = '__sd_pill__';
      pill.textContent = '⚡ SD';
      document.body.appendChild(pill);
      pill.addEventListener('click', () => {
        panel.classList.remove('hidden');
        pill.classList.remove('visible');
      });
    }

    // Header double-click to minimise
    panel.querySelector('.sd-header').addEventListener('dblclick', () => {
      panel.classList.add('hidden');
      pill.classList.add('visible');
    });

    // Wire up buttons
    const msg = panel.querySelector('#sd-msg');

    function setMsg(text, type) {
      msg.textContent = text;
      msg.className   = `sd-msg ${type}`;
    }

    if (live) {
      panel.querySelector('#sd-reinject').addEventListener('click', async () => {
        const btn = panel.querySelector('#sd-reinject');
        btn.disabled = true;
        setMsg('Fetching latest cookies…', 'loading');
        try {
          const data   = await fetchData();
          const lic    = data.licenses && data.licenses[key];
          if (!lic || isExpired(lic.expires)) {
            setMsg('License expired. Please reconnect.', 'err');
            GM_deleteValue(KEY_STORE);
            GM_deleteValue(EXP_STORE);
            GM_deleteValue(PLAN_STORE);
            setTimeout(() => { panel.remove(); buildPanel(); }, 1800);
            return;
          }
          // Update expiry in case you extended it
          GM_setValue(EXP_STORE, lic.expires);
          GM_setValue(PLAN_STORE, lic.plan || 'standard');

          const count = await injectCookies(data.cookies || []);
          setMsg(`✓ ${count} cookies injected — reloading…`, 'ok');
          setTimeout(() => location.reload(), 1000);
        } catch (e) {
          setMsg(e.message, 'err');
          btn.disabled = false;
        }
      });

      panel.querySelector('#sd-disconnect').addEventListener('click', () => {
        GM_deleteValue(KEY_STORE);
        GM_deleteValue(EXP_STORE);
        GM_deleteValue(PLAN_STORE);
        panel.remove();
        buildPanel();
      });

    } else {
      const keyInput  = panel.querySelector('#sd-key');
      const connectBtn = panel.querySelector('#sd-connect');

      async function doConnect() {
        const k = keyInput.value.trim().toUpperCase();
        if (!k) { setMsg('Enter your license key first.', 'err'); return; }

        connectBtn.disabled = true;
        setMsg('Verifying license…', 'loading');

        let data;
        try {
          data = await fetchData();
        } catch (e) {
          setMsg(e.message, 'err');
          connectBtn.disabled = false;
          return;
        }

        const lic = data.licenses && data.licenses[k];
        if (!lic) {
          setMsg('Invalid license key.', 'err');
          connectBtn.disabled = false;
          return;
        }
        if (isExpired(lic.expires)) {
          setMsg(`License expired on ${lic.expires}.`, 'err');
          connectBtn.disabled = false;
          return;
        }

        setMsg('Injecting session cookies…', 'loading');
        const count = await injectCookies(data.cookies || []);

        GM_setValue(KEY_STORE,  k);
        GM_setValue(EXP_STORE,  lic.expires);
        GM_setValue(PLAN_STORE, lic.plan || 'standard');

        setMsg(`✓ Connected! ${count} cookies set — reloading…`, 'ok');
        setTimeout(() => { panel.remove(); buildPanel(); location.reload(); }, 1200);
      }

      connectBtn.addEventListener('click', doConnect);
      keyInput.addEventListener('keydown', e => { if (e.key === 'Enter') doConnect(); });
    }

    return panel;
  }

  // ── Auto re-inject on page load ───────────────────────────────────────────

  async function autoInject() {
    const key = GM_getValue(KEY_STORE, '');
    const exp = GM_getValue(EXP_STORE, '');
    if (!key || isExpired(exp)) return;

    try {
      const data = await fetchData();
      const lic  = data.licenses && data.licenses[key];
      if (!lic || isExpired(lic.expires)) {
        GM_deleteValue(KEY_STORE);
        GM_deleteValue(EXP_STORE);
        GM_deleteValue(PLAN_STORE);
        return;
      }
      GM_setValue(EXP_STORE,  lic.expires);
      GM_setValue(PLAN_STORE, lic.plan || 'standard');
      await injectCookies(data.cookies || []);
    } catch (e) {
      // Silent fail — user can manually re-inject from panel
    }
  }

  // ── Boot ──────────────────────────────────────────────────────────────────

  function boot() {
    if (document.getElementById(PANEL_ID)) return;
    if (location.pathname.startsWith('/fx/api/auth/signout')) return;

    buildPanel();
    autoInject(); // silent background re-inject every page load
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

})();
