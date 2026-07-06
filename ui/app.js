let currentSide = 'BUY';

function $(id) { return document.getElementById(id); }

// ── Toast ──
let toastTimer;
function toast(msg, type) {
  const el = $('toast');
  el.textContent = msg;
  el.className = 'toast ' + type + ' show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 4000);
}

// ── API ──
async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw await r.text();
  return r.json();
}

async function apiPost(url, body) {
  return api(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ── Formatters ──
function timeStr(ts) { return new Date(ts).toLocaleString(); }

function fmt(n) {
  if (n === undefined || n === null) return '\u2014';
  return Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pnlCell(v) {
  if (v === undefined || v === null || v === 0) return '<td class="green">\u2014</td>';
  return '<td class="' + (v >= 0 ? 'green' : 'red') + '">' + (v >= 0 ? '+' : '') + fmt(v) + '</td>';
}

// ── Trade Form ──
function initTradeForm() {
  // Side buttons
  $('t-side-group').querySelectorAll('button').forEach(function (b) {
    b.addEventListener('click', function () {
      $('t-side-group').querySelectorAll('button').forEach(function (x) { x.className = ''; });
      b.className = 'active ' + (b.dataset.side === 'BUY' ? 'buy' : 'sell');
      currentSide = b.dataset.side;
      updateSubmitBtn();
    });
  });
  // Type change
  $('t-type').addEventListener('change', function () {
    var t = $('t-type').value;
    $('t-price-row').className = 'form-row' + (t === 'MARKET' ? ' field-hidden' : '');
    $('t-stop-row').className = 'form-row' + (t === 'STOP' ? '' : ' field-hidden');
  });
  $('t-submit').addEventListener('click', placeOrder);
}

function updateSubmitBtn() {
  var btn = $('t-submit');
  btn.textContent = 'Place ' + currentSide + ' Order';
  btn.className = 'submit ' + currentSide.toLowerCase();
}

async function placeOrder() {
  var btn = $('t-submit');
  var orig = btn.textContent;
  btn.textContent = 'Placing...';
  btn.disabled = true;
  try {
    var body = {
      symbol: $('t-symbol').value.toUpperCase(),
      side: currentSide,
      type: $('t-type').value,
      quantity: $('t-qty').value,
      price: $('t-price').value || null,
      stopPrice: $('t-stop').value || null,
    };
    var r = await apiPost('/api/place_order', body);
    toast(r.message || 'Order placed! ID: ' + r.orderId, 'success');
    loadAll();
    loadOpenOrders();
  } catch (e) {
    toast('Order failed: ' + e, 'error');
  } finally {
    btn.textContent = orig;
    btn.disabled = false;
  }
}

async function closePosition(symbol, side, size) {
  if (!confirm('Close ' + symbol + ' ' + side + ' ' + size + '?')) return;
  try {
    var oppSide = side === 'LONG' ? 'SELL' : 'BUY';
    var r = await apiPost('/api/place_order', { symbol: symbol, side: oppSide, type: 'MARKET', quantity: String(size) });
    toast('Position closed! ID: ' + r.orderId, 'success');
    loadAll();
    loadPositionTab();
  } catch (e) {
    toast('Close failed: ' + e, 'error');
  }
}

async function cancelOrder(symbol, orderId) {
  try {
    var r = await apiPost('/api/cancel_order', { symbol: symbol, orderId: orderId });
    toast('Cancelled order #' + orderId, 'success');
    loadOpenOrders();
  } catch (e) {
    toast('Cancel failed: ' + e, 'error');
  }
}

// ── Renderers ──
function renderQuickInfo(data) {
  var pos = data.positions || [];
  var sym = $('t-symbol').value.toUpperCase();
  var match = pos.find(function (p) { return p.symbol === sym; });
  if (match) {
    $('t-quick').innerHTML =
      '<table><tbody>' +
      '<tr><td>Position</td><td><span class="badge ' + (match.side === 'LONG' ? 'long' : 'short') + '">' + match.side + '</span> ' + match.size + '</td></tr>' +
      '<tr><td>Entry</td><td>$' + fmt(match.entryPrice) + '</td></tr>' +
      '<tr><td>Mark</td><td>$' + fmt(match.markPrice) + '</td></tr>' +
      '<tr><td>PnL</td><td class="' + (match.unrealizedPnl >= 0 ? 'green' : 'red') + '">' + (match.unrealizedPnl >= 0 ? '+' : '') + '$' + fmt(match.unrealizedPnl) + ' (' + (match.pnlPercent >= 0 ? '+' : '') + match.pnlPercent + '%)</td></tr>' +
      '<tr><td>Leverage</td><td>' + match.leverage + 'x</td></tr>' +
      '<tr><td>Liq.</td><td>$' + fmt(match.liquidationPrice) + '</td></tr>' +
      '</tbody></table>';
  } else {
    var bal = data.balances || [];
    var usdt = bal.find(function (b) { return b.asset === 'USDT'; });
    var btc = bal.find(function (b) { return b.asset === 'BTC'; });
    $('t-quick').innerHTML =
      '<table><tbody>' +
      (usdt ? '<tr><td>USDT Bal.</td><td>$' + fmt(usdt.available) + ' avail</td></tr>' : '') +
      (btc ? '<tr><td>BTC Bal.</td><td>' + btc.available + '</td></tr>' : '') +
      '<tr><td colspan="2" style="color:#8b949e">No open position in ' + sym + '</td></tr>' +
      '</tbody></table>';
  }
}

function renderOverview(data) {
  var html = '<div class="cards">';
  var acct = data.account;
  if (acct) {
    html += '<div class="card"><h3>Total Equity</h3><div class="val">$' + fmt(acct.totalEquity) + '</div><div class="sub">Wallet: $' + fmt(acct.totalWalletBalance) + ' | PnL: <span class="' + (acct.totalUnrealizedPnl >= 0 ? 'green' : 'red') + '">' + (acct.totalUnrealizedPnl >= 0 ? '+' : '') + '$' + fmt(acct.totalUnrealizedPnl) + '</span></div></div>';
  }
  var bal = data.balances || [];
  if (bal.length) {
    bal.forEach(function (a) {
      html += '<div class="card"><h3>' + a.asset + '</h3><div class="val">' + fmt(a.wallet) + '</div><div class="sub">Available: ' + fmt(a.available) + '</div></div>';
    });
  } else {
    html += '<div class="card">No non-zero balances</div>';
  }
  $('overview').innerHTML = html + '</div>';
}

function renderPositionsTab(data) {
  var p = data.positions || [];
  if (!p.length) { $('positions').innerHTML = '<div class="loading">No open positions</div>'; return; }
  var h = '<table><thead><tr><th>Symbol</th><th>Side</th><th>Size</th><th>Entry</th><th>Mark</th><th>PnL</th><th>PnL%</th><th>Lev.</th><th></th></tr></thead><tbody>';
  p.forEach(function (r) {
    var sc = r.side === 'LONG' ? 'long' : 'short';
    h += '<tr><td><b>' + r.symbol + '</b></td><td><span class="badge ' + sc + '">' + r.side + '</span></td><td>' + r.size + '</td>' +
      '<td>$' + fmt(r.entryPrice) + '</td><td>$' + fmt(r.markPrice) + '</td>' + pnlCell(r.unrealizedPnl) + pnlCell(r.pnlPercent) +
      '<td>' + r.leverage + 'x</td>' +
      '<td><button class="btn-sm red" onclick="closePosition(\'' + r.symbol + '\',\'' + r.side + '\',\'' + r.size + '\')">Close</button></td></tr>';
  });
  $('positions').innerHTML = h + '</tbody></table>';
}

function renderOpenOrders() {
  var o = $('openorders');
  o.innerHTML = '<div class="loading">Loading...</div>';
  api('/api/open_orders').then(function (d) {
    if (!d.orders || !d.orders.length) { o.innerHTML = '<div class="loading">No open orders</div>'; return; }
    var h = '<table><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Type</th><th>Price</th><th>Qty</th><th>Filled</th><th></th></tr></thead><tbody>';
    d.orders.forEach(function (r) {
      var sc = r.side === 'BUY' ? 'green' : 'red';
      h += '<tr><td>' + timeAgo(r.time) + '</td><td>' + r.symbol + '</td><td class="' + sc + '">' + r.side + '</td><td>' + r.type + '</td>' +
        '<td>$' + fmt(r.price) + '</td><td>' + r.origQty + '</td><td>' + r.executedQty + '</td>' +
        '<td><button class="btn-sm red" onclick="cancelOrder(\'' + r.symbol + '\',' + r.orderId + ')">Cancel</button></td></tr>';
    });
    o.innerHTML = h + '</tbody></table>';
  }).catch(function (e) { o.innerHTML = '<div class="loading">Error: ' + e + '</div>'; });
}

function renderOrdersTab(data) {
  var o = data.recentOrders || [];
  if (!o.length) { $('orders').innerHTML = '<div class="loading">No filled orders</div>'; return; }
  var h = '<table><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Type</th><th>Qty</th><th>Price</th><th>Volume</th></tr></thead><tbody>';
  o.forEach(function (r) {
    var sc = r.side === 'BUY' ? 'green' : 'red';
    h += '<tr><td>' + timeStr(r.time) + '</td><td>' + r.symbol + '</td><td class="' + sc + '">' + r.side + '</td><td>' + r.type + '</td>' +
      '<td>' + r.qty + '</td><td>$' + fmt(r.price) + '</td><td>$' + fmt(r.cumQuote) + '</td></tr>';
  });
  $('orders').innerHTML = h + '</tbody></table>';
}

function timeAgo(ts) {
  var s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  return Math.floor(s / 3600) + 'h ago';
}

function loadOverview(data) { renderOverview(data); }
function loadPositionTab() {
  api('/api/summary').then(function (d) { renderPositionsTab(d); });
}
function loadOrdersTab(data) { renderOrdersTab(data); }
function loadOpenOrders() { renderOpenOrders(); }
function loadQuickInfo(data) { renderQuickInfo(data); }

async function loadAll() {
  $('status').textContent = 'loading...';
  try {
    var data = await api('/api/summary');
    loadOverview(data);
    renderPositionsTab(data);
    renderOrdersTab(data);
    renderQuickInfo(data);
    $('status').textContent = 'Updated ' + new Date().toLocaleTimeString();
  } catch (e) {
    $('status').textContent = 'Error: ' + e;
    console.error(e);
  }
}

// ── Tab switching ──
document.querySelectorAll('.tabs button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.tabs button').forEach(function (b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
    btn.classList.add('active');
    $(btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'openorders') loadOpenOrders();
    if (btn.dataset.tab === 'positions') loadPositionTab();
  });
});

// ── Init ──
initTradeForm();
loadAll();
setInterval(loadAll, 15000);
