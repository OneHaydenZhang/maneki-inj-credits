/* INJ credit economy — front-end (extracted from Maneki Inj).
 * Preset top-up packs → Keplr/Leap/OKX signDirect → MsgSend to treasury → backend
 * reads the on-chain transfer (indexer) and credits the sender. No balance polling.
 *
 * Auth here is a demo X-Login-Address header; in the full app it's a wallet
 * signature session. Set window.LOGIN_ADDRESS to your wallet (0x…) first.
 */
const LOGIN = () => (window.LOGIN_ADDRESS || '').toLowerCase();
const fmtPts = (n) => (n == null || isNaN(n) ? '—' : Number(n).toLocaleString(undefined, { maximumFractionDigits: (Number(n) % 1 === 0 ? 0 : 2) }));

async function api(path, { method = 'GET', body } = {}) {
  const r = await fetch(path, {
    method,
    headers: { 'content-type': 'application/json', 'X-Login-Address': LOGIN() },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || data.detail || ('HTTP ' + r.status));
  return data;
}

let POINTS = null;

async function refreshPoints() {
  if (!LOGIN()) return;
  try { POINTS = await api('/api/points'); renderPointsPanel(); }
  catch (e) { console.warn(e); }
}

function $(s) { return document.querySelector(s); }

function renderPointsPanel() {
  if (!POINTS || !$('#ptsBalance')) return;
  const cfg = POINTS.config || {};
  $('#ptsBalance').textContent = fmtPts(POINTS.balance);
  $('#ptsRate').textContent = fmtPts(cfg.rate_inj || 100);
  $('#ptsNet').textContent = cfg.network || 'mainnet';
  $('#ptsPerTick').textContent = fmtPts(cfg.per_tick || 1);
  const configured = !!cfg.treasury;
  if ($('#ptsOff')) $('#ptsOff').style.display = configured ? 'none' : '';
  const box = $('#ptsPresets');
  if (box) {
    const presets = cfg.presets || [1, 5, 10, 100, 200, 1000];
    box.innerHTML = presets.map((c) =>
      `<button class="preset" data-c="${c}" ${configured ? '' : 'disabled'}>+${fmtPts(c)} credits<small> · ${fmtPts(c / (cfg.rate_inj || 100))} INJ</small></button>`).join('');
    box.querySelectorAll('.preset').forEach((b) => (b.onclick = () => depositCredits(Number(b.dataset.c))));
  }
  const lb = $('#ptsLedger');
  if (lb) lb.innerHTML = (POINTS.history || []).slice(0, 12).map((h) => {
    const d = Number(h.points), sign = d >= 0 ? '+' : '';
    return `<tr><td>${new Date(h.ts * 1000).toLocaleString()}</td><td>${h.kind}${h.note ? ' · ' + h.note : ''}</td><td style="text-align:right;color:${d >= 0 ? '#14d6ba' : '#ff6472'}">${sign}${fmtPts(d)}</td></tr>`;
  }).join('') || '<tr><td colspan="3">—</td></tr>';
}

/* Keplr / Leap / OKX all inject the same Keplr-style API. */
function injCosmosWallet() {
  if (window.keplr) return { name: 'Keplr', w: window.keplr };
  if (window.leap) return { name: 'Leap', w: window.leap };
  if (window.okxwallet && window.okxwallet.keplr) return { name: 'OKX', w: window.okxwallet.keplr };
  if (window.owallet) return { name: 'OWallet', w: window.owallet };
  return null;
}
const b64ToBytes = (b64) => { const s = atob(b64), a = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return a; };
const bytesToB64 = (bytes) => { const a = new Uint8Array(bytes); let s = ''; for (let i = 0; i < a.length; i++) s += String.fromCharCode(a[i]); return btoa(s); };

/* One-click top-up: build MsgSend → wallet signDirect → backend broadcast + credit. */
async function depositCredits(credits) {
  const m = $('#ptsMsg'), cfg = (POINTS && POINTS.config) || {};
  if (!cfg.treasury) { if (m) m.textContent = 'top-up not configured'; return; }
  const cw = injCosmosWallet();
  if (!cw) { if (m) m.textContent = 'No Keplr/Leap/OKX wallet detected'; return; }
  const chainId = (cfg.network === 'testnet') ? 'injective-888' : 'injective-1';
  try {
    if (m) m.textContent = 'connecting wallet…';
    await cw.w.enable(chainId);
    const key = await cw.w.getKey(chainId);
    const pubkey = bytesToB64(key.pubKey);
    const b = await api('/api/points/deposit/build', { method: 'POST', body: { credits, pubkey, sender_inj: key.bech32Address } });
    const Long = (await import('https://esm.sh/long@5')).default;
    if (m) m.textContent = 'confirm the transfer in your wallet…';
    const signed = await cw.w.signDirect(chainId, key.bech32Address, {
      bodyBytes: b64ToBytes(b.bodyBytes), authInfoBytes: b64ToBytes(b.authInfoBytes),
      chainId: b.chainId, accountNumber: Long.fromString(String(b.accountNumber)),
    });
    if (m) m.textContent = 'broadcasting & crediting…';
    const r = await api('/api/points/deposit/submit', { method: 'POST', body: {
      bodyBytes: bytesToB64(signed.signed.bodyBytes), authInfoBytes: bytesToB64(signed.signed.authInfoBytes),
      signature: signed.signature.signature,
    } });
    POINTS.balance = r.balance; POINTS.history = r.history; renderPointsPanel();
    if (m) m.textContent = '✓ balance ' + fmtPts(r.balance);
  } catch (e) { if (m) m.textContent = 'failed: ' + (e.message || e); }
}

async function scanDeposits() {
  const m = $('#ptsMsg');
  if (m) m.textContent = 'scanning…';
  try {
    const r = await api('/api/points/scan', { method: 'POST' });
    POINTS.balance = r.balance; POINTS.history = r.history; renderPointsPanel();
    if (m) m.textContent = '✓ balance ' + fmtPts(r.balance);
  } catch (e) { if (m) m.textContent = 'failed: ' + (e.message || e); }
}

window.addEventListener('DOMContentLoaded', () => {
  if ($('#btnScan')) $('#btnScan').onclick = scanDeposits;
  refreshPoints();
});
