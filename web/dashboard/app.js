let state = null;
let agentsData = [];
let selectedAgentId = null;
let map = null;
let agentMarkers = [];
let pollTimer = null;

function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  document.querySelector(`[data-view="${name}"]`).classList.add('active');
  if (name === 'map' && !map) initMap();
  if (name === 'map' && map) map.invalidateSize();
  if (name === 'agents') fetchAgents();
  if (name === 'economy') fetchEconomy();
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function fmt(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return Math.round(n).toLocaleString();
}

async function api(url, data) {
  const opts = data ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) } : {};
  const res = await fetch(url, opts);
  return res.json();
}

const TYPE_COLORS = {
  central_bank: '#6366f1', bank: '#2563eb', company: '#16a34a', state: '#dc2626',
  judge: '#7c3aed', energy_provider: '#ea580c', trader: '#0891b2', citizen: '#64748b'
};

function initMap() {
  map = L.map('map-container', {
    center: [20, 0], zoom: 2.5, minZoom: 2, maxZoom: 8,
    zoomControl: false, attributionControl: false,
    worldCopyJump: true,
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd', maxZoom: 19,
  }).addTo(map);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd', maxZoom: 19, pane: 'overlayPane',
  }).addTo(map);

  L.control.zoom({ position: 'topright' }).addTo(map);
}

function updateMapAgents(agents) {
  if (!map) return;
  agentMarkers.forEach(m => map.removeLayer(m));
  agentMarkers = [];

  agents.forEach(a => {
    const color = TYPE_COLORS[a.type] || '#64748b';
    const size = Math.max(6, Math.min(20, Math.sqrt(a.wallet / 10)));

    const icon = L.divIcon({
      className: 'agent-marker',
      html: `<div style="
        width:${size}px; height:${size}px; border-radius:50%;
        background:${color}; opacity:0.75;
        box-shadow: 0 0 ${size/2}px ${color}40;
        border: 1.5px solid white;
      "></div>`,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
    });

    const marker = L.marker([a.lat, a.lng], { icon }).addTo(map);
    marker.on('click', () => showAgentPopup(a, marker));
    agentMarkers.push(marker);
  });
}

function showAgentPopup(a, marker) {
  const popup = document.getElementById('agent-popup');
  popup.className = 'agent-popup';
  const typeColor = TYPE_COLORS[a.type] || '#64748b';
  const inv = a.inventory || {};
  const invRows = Object.entries(inv).filter(([,v]) => v > 0).map(([k,v]) =>
    `<div class="popup-row"><span class="popup-label">${k}</span><span class="popup-val">${v}</span></div>`
  ).join('');
  const aiEvents = (state?.ai_events || []).filter(e => e.includes(a.name)).slice(-3);
  const actionsHtml = aiEvents.length ? `
    <div class="popup-actions">
      <div class="popup-actions-title">Recent Actions</div>
      ${aiEvents.map(e => `<div class="popup-action-item">${esc(e)}</div>`).join('')}
    </div>` : '';
  popup.innerHTML = `
    <button class="popup-close" onclick="document.getElementById('agent-popup').classList.add('hidden')">&times;</button>
    <div class="popup-name">${esc(a.name)}</div>
    <div class="popup-type" style="color:${typeColor}">${a.type.replace('_', ' ')}</div>
    <div class="popup-row"><span class="popup-label">Wallet</span><span class="popup-val">$${fmt(a.wallet)}</span></div>
    <div class="popup-row"><span class="popup-label">Total Assets</span><span class="popup-val">$${fmt(a.total_assets)}</span></div>
    <div class="popup-row"><span class="popup-label">Country</span><span class="popup-val">${a.country}</span></div>
    <div class="popup-row"><span class="popup-label">Influence</span><span class="popup-val">${a.influence}</span></div>
    <div class="popup-row"><span class="popup-label">Personality</span><span class="popup-val">${a.personality}</span></div>
    ${invRows}
    ${actionsHtml}
  `;
  const pt = map.latLngToContainerPoint([a.lat, a.lng]);
  popup.style.left = Math.min(pt.x + 12, window.innerWidth - 360) + 'px';
  popup.style.top = Math.min(pt.y - 20, window.innerHeight - 300) + 'px';
}

async function fetchState() {
  try {
    const data = await api('/api/simulation/state');
    state = data;
    updateStatus(data);
    updateMiniStats(data);
    updateMapAgents(data.agents || []);
    updateFeed();
  } catch (e) { console.warn('state fetch failed', e); }
}

function updateStatus(d) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  const tick = document.getElementById('tick-label');
  const start = document.getElementById('btn-start');
  const pause = document.getElementById('btn-pause');

  if (!d.active) {
    dot.className = 'status-dot offline';
    label.textContent = 'No world';
    tick.textContent = 'Tick 0';
    start.classList.remove('active');
    pause.classList.remove('active');
  } else if (d.running) {
    dot.className = 'status-dot running';
    label.textContent = 'Running';
    tick.textContent = 'Tick ' + d.tick;
    start.classList.add('active');
    pause.classList.remove('active');
  } else {
    dot.className = 'status-dot online';
    label.textContent = 'Paused';
    tick.textContent = 'Tick ' + d.tick;
    start.classList.remove('active');
    pause.classList.remove('active');
  }
}

function updateMiniStats(d) {
  if (!d.active) return;
  document.getElementById('s-agents').textContent = d.agents ? d.agents.length : 0;
  document.getElementById('s-companies').textContent = d.companies ? d.companies.length : 0;
  const total = (d.agents || []).reduce((s, a) => s + a.wallet, 0);
  document.getElementById('s-money').textContent = '$' + fmt(total);
}

let lastFeedFetch = 0;
async function updateFeed() {
  const now = Date.now();
  if (now - lastFeedFetch < 8000) return;
  lastFeedFetch = now;
  try {
    const data = await api('/api/events/feed');
    const el = document.getElementById('feed-items');
    const items = (data.headlines || []).slice(0, 10);
    if (!items.length) return;
    el.innerHTML = items.map(e => `<div class="feed-item">${esc(e)}</div>`).join('');
  } catch (e) {}
}

async function fetchAgents() {
  try {
    const data = await api('/api/agents');
    agentsData = data.agents || [];
    document.getElementById('agent-count-badge').textContent = agentsData.length;
    renderAgentList(agentsData);
  } catch (e) { console.warn('agents fetch failed', e); }
}

function filterAgents() {
  const q = document.getElementById('agent-search').value.toLowerCase();
  const type = document.getElementById('agent-type-filter').value;
  const sort = document.getElementById('agent-sort').value;

  let list = agentsData.filter(a => {
    if (q && !a.name.toLowerCase().includes(q)) return false;
    if (type !== 'all' && a.type !== type) return false;
    return true;
  });

  list.sort((a, b) => {
    if (sort === 'wallet') return b.wallet - a.wallet;
    if (sort === 'influence') return b.influence - a.influence;
    return a.name.localeCompare(b.name);
  });

  renderAgentList(list);
}

function renderAgentList(list) {
  const el = document.getElementById('agents-list');
  if (!list.length) {
    el.innerHTML = '<div class="empty-state">No agents found</div>';
    return;
  }
  el.innerHTML = list.map(a => `
    <div class="agent-row ${selectedAgentId === a.id ? 'selected' : ''}" onclick="selectAgent('${a.id}')">
      <div class="agent-dot dot-${a.type}"></div>
      <div class="agent-row-info">
        <div class="agent-row-name">${esc(a.name)}</div>
        <div class="agent-row-meta">${a.type.replace('_',' ')} &middot; ${a.country}</div>
      </div>
      <div class="agent-row-wallet">$${fmt(a.wallet)}</div>
    </div>
  `).join('');
}

async function selectAgent(id) {
  selectedAgentId = id;
  document.querySelectorAll('.agent-row').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(`.agent-row[onclick*="${id}"]`);
  if (row) row.classList.add('selected');
  try {
    const a = await api('/api/agents/' + id);
    renderProfile(a);
  } catch (e) { console.warn('profile fetch failed', e); }
}

function renderProfile(a) {
  const el = document.getElementById('agent-profile');
  const color = TYPE_COLORS[a.type] || '#64748b';
  const maxW = a.wealth_history?.length ? Math.max(...a.wealth_history, 1) : 1;
  const bars = (a.wealth_history || []).slice(-50).map(w =>
    `<div class="w-bar" style="height:${Math.max(2, (w / maxW) * 100)}%"></div>`
  ).join('');

  const inv = Object.entries(a.inventory || {}).map(([k, v]) =>
    `<div class="inv-item"><span class="inv-key">${k}</span><span class="inv-val">${v}</span></div>`
  ).join('');

  const logs = (a.decision_log || []).slice(-12).reverse().map(d =>
    `<div class="log-item">${esc(d)}</div>`
  ).join('');

  el.innerHTML = `
    <div class="profile-header">
      <div class="profile-dot" style="background:${color}"></div>
      <div>
        <div class="profile-name">${esc(a.name)}</div>
        <div class="profile-type" style="color:${color}">${a.type.replace('_',' ')}</div>
        <div class="profile-country">${a.country}</div>
      </div>
    </div>
    <div class="profile-metrics">
      <div class="p-metric"><span class="stat-l">Wallet</span><span class="stat-n">$${a.wallet.toFixed(2)}</span></div>
      <div class="p-metric"><span class="stat-l">Total Assets</span><span class="stat-n">$${a.total_assets.toFixed(2)}</span></div>
      <div class="p-metric"><span class="stat-l">Influence</span><span class="stat-n">${a.influence}</span></div>
      <div class="p-metric"><span class="stat-l">Risk</span><span class="stat-n">${a.risk}</span></div>
      <div class="p-metric"><span class="stat-l">Personality</span><span class="stat-n" style="font-size:0.82rem">${a.personality}</span></div>
      <div class="p-metric"><span class="stat-l">Bank Balance</span><span class="stat-n">$${a.bank_balance}</span></div>
    </div>
    ${a.company ? `<div class="section-title">Company</div><div class="inv-item"><span class="inv-key">${esc(a.company.name)}</span><span class="inv-val">$${a.company.cash.toFixed(2)}</span></div>` : ''}
    <div class="section-title">Wealth History</div>
    <div class="wealth-chart">${bars || '<span style="color:var(--text-muted);font-size:0.75rem">No history</span>'}</div>
    <div class="section-title">Inventory</div>
    <div class="inv-grid">${inv}</div>
    <div class="section-title">Decision Log</div>
    <div class="log-list">${logs || '<span style="color:var(--text-muted);font-size:0.75rem">No decisions yet</span>'}</div>
  `;
}

async function fetchEconomy() {
  try {
    const d = await api('/api/economy');
    if (!d.active) return;
    document.getElementById('e-money').textContent = '$' + fmt(d.total_money_supply);
    document.getElementById('e-agents').textContent = d.agent_count;
    document.getElementById('e-companies').textContent = d.company_count;
    document.getElementById('e-gini').textContent = d.gini_index.toFixed(3);
    document.getElementById('gini-fill').style.width = (d.gini_index * 100) + '%';
    document.getElementById('e-bankrupt').textContent = d.bankrupt_agents;
    document.getElementById('e-reserve').textContent = '$' + fmt(d.bank_reserve);

    const pg = document.getElementById('prices-grid');
    pg.innerHTML = Object.entries(d.market_prices || {}).map(([k, v]) =>
      `<div class="price-item"><div class="price-name">${k}</div><div class="price-val">$${v.toFixed(2)}</div></div>`
    ).join('');

    const lb = document.getElementById('leaderboard');
    lb.innerHTML = (d.top_agents || []).map((a, i) => {
      const rc = i === 0 ? 'g' : i === 1 ? 's' : i === 2 ? 'b' : '';
      return `<div class="lb-row"><span class="lb-rank ${rc}">${i+1}</span><span class="lb-name">${esc(a.name)}</span><span class="lb-type">${a.type.replace('_',' ')}</span><span class="lb-wallet">$${fmt(a.wallet)}</span></div>`;
    }).join('');

    const rb = document.getElementById('resources-bars');
    const maxR = Math.max(...Object.values(d.global_resources || {}), 1);
    rb.innerHTML = Object.entries(d.global_resources || {}).map(([k, v]) =>
      `<div class="res-row"><span class="res-label">${k}</span><div class="res-track"><div class="res-fill ${k}" style="width:${(v/maxR*100).toFixed(1)}%"></div></div><span class="res-val">${fmt(v)}</span></div>`
    ).join('');
  } catch (e) { console.warn('economy fetch failed', e); }
}

async function createWorld() {
  await api('/api/simulation/control', { action: 'create_world' });
  fetchState();
}

async function startSim() {
  await api('/api/simulation/control', { action: 'start', speed: 5 });
  fetchState();
}

async function pauseSim() {
  await api('/api/simulation/control', { action: 'pause' });
  fetchState();
}

async function stopSim() {
  await api('/api/simulation/control', { action: 'stop' });
  fetchState();
}

initMap();
fetchState();

pollTimer = setInterval(() => {
  fetchState();
  const active = document.querySelector('.view.active');
  if (active?.id === 'view-economy') fetchEconomy();
  if (active?.id === 'view-agents' && selectedAgentId) selectAgent(selectedAgentId);
}, 4000);
