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

  map.on('click', () => {
    document.getElementById('agent-popup').classList.add('hidden');
  });
}

function updateMapAgents(agents) {
  agentMarkers.forEach(m => map.removeLayer(m));
  agentMarkers = [];
  if (!agents || !agents.length) return;

  agents.forEach(a => {
    if (!a.lat && !a.lng) return;
    const color = TYPE_COLORS[a.type] || '#64748b';
    const energy = a.core_energy || 0;
    const r = Math.max(6, Math.min(20, Math.sqrt((a.wallet + energy * 10) / 10)));
    const opacity = a.alive === false ? 0.3 : 0.85;
    const icon = L.divIcon({
      className: 'agent-marker',
      html: `<div style="width:${r*2}px;height:${r*2}px;border-radius:50%;background:${color};opacity:${opacity};border:2px solid rgba(255,255,255,0.8);box-shadow:0 1px 4px rgba(0,0,0,0.2);"></div>`,
      iconSize: [r*2, r*2], iconAnchor: [r, r],
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
  const statusBadge = a.alive === false ? '<span class="dead-badge">INACTIVE</span>' : '';
  const aiEvents = (state?.ai_events || []).filter(e => e.includes(a.name)).slice(-3);
  const actionsHtml = aiEvents.length ? `
    <div class="popup-actions">
      <div class="popup-actions-title">Recent Actions</div>
      ${aiEvents.map(e => `<div class="popup-action-item">${esc(e)}</div>`).join('')}
    </div>` : '';
  popup.innerHTML = `
    <button class="popup-close" onclick="document.getElementById('agent-popup').classList.add('hidden')">&times;</button>
    <div class="popup-name">${esc(a.name)} ${statusBadge}</div>
    <div class="popup-type" style="color:${typeColor}">${a.type.replace('_', ' ')}</div>
    <div class="popup-row"><span class="popup-label">Currency</span><span class="popup-val">${a.wallet?.toFixed(1)} ${a.currency || 'USC'}</span></div>
    <div class="popup-row"><span class="popup-label">EnergyCore</span><span class="popup-val">${(a.core_energy || 0).toFixed(2)}</span></div>
    <div class="popup-row"><span class="popup-label">Total Value</span><span class="popup-val">${fmt(a.total_value || 0)}</span></div>
    <div class="popup-row"><span class="popup-label">Country</span><span class="popup-val">${a.country}</span></div>
    <div class="popup-row"><span class="popup-label">Ideology</span><span class="popup-val">${a.ideology || '-'}</span></div>
    <div class="popup-row"><span class="popup-label">Personality</span><span class="popup-val">${a.personality}</span></div>
    <div class="popup-row"><span class="popup-label">Influence</span><span class="popup-val">${a.influence}</span></div>
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
  const agents = d.agents || [];
  const alive = agents.filter(a => a.alive !== false).length;
  document.getElementById('s-agents').textContent = alive;
  document.getElementById('s-companies').textContent = d.companies ? d.companies.length : 0;
  const totalEnergy = agents.reduce((s, a) => s + (a.core_energy || 0), 0);
  document.getElementById('s-energy').textContent = fmt(totalEnergy);
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

  if (sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === 'wallet') list.sort((a, b) => b.wallet - a.wallet);
  else if (sort === 'core_energy') list.sort((a, b) => (b.core_energy || 0) - (a.core_energy || 0));
  else if (sort === 'total_value') list.sort((a, b) => (b.total_value || 0) - (a.total_value || 0));
  else list.sort((a, b) => b.influence - a.influence);

  renderAgentList(list);
}

function renderAgentList(list) {
  const el = document.getElementById('agents-list');
  if (!list.length) {
    el.innerHTML = '<div class="empty-state">No agents found</div>';
    return;
  }
  el.innerHTML = list.map(a => {
    const color = TYPE_COLORS[a.type] || '#64748b';
    const active = a.id === selectedAgentId ? 'active' : '';
    const status = a.alive === false ? ' (dead)' : '';
    return `<div class="agent-item ${active}" onclick="selectAgent('${a.id}')" style="border-left:3px solid ${color}">
      <div class="agent-item-name">${esc(a.name)}${status}</div>
      <div class="agent-item-meta">${a.type.replace('_', ' ')} · ${a.country}</div>
      <div class="agent-item-stats">${a.wallet.toFixed(0)} ${a.currency || 'USC'} · EC: ${(a.core_energy || 0).toFixed(1)}</div>
    </div>`;
  }).join('');
}

async function selectAgent(id) {
  selectedAgentId = id;
  document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('active'));
  const items = document.querySelectorAll('.agent-item');
  items.forEach(el => { if (el.getAttribute('onclick')?.includes(id)) el.classList.add('active'); });

  try {
    const a = await api(`/api/agents/${id}`);
    renderAgentProfile(a);
  } catch (e) { console.warn('profile load failed', e); }
}

function renderAgentProfile(a) {
  const el = document.getElementById('agent-profile');
  const color = TYPE_COLORS[a.type] || '#64748b';
  const wh = a.wealth_history || [];
  const maxW = Math.max(1, ...wh);
  const bars = wh.slice(-30).map(w => `<div class="wealth-bar" style="height:${Math.max(2, (w / maxW) * 100)}%;background:${color};"></div>`).join('');
  const logs = (a.decision_log || []).slice(-10).map(l => `<div class="log-item">${esc(l)}</div>`).join('');
  const statusBadge = a.alive === false ? '<span class="dead-badge">INACTIVE</span>' : '';

  el.innerHTML = `
    <div class="profile-header" style="border-left:4px solid ${color}">
      <h2>${esc(a.name)} ${statusBadge}</h2>
      <div class="profile-type">${a.type.replace('_', ' ')} · ${a.country}</div>
    </div>
    <div class="profile-grid">
      <div class="profile-stat"><span class="profile-label">Currency Balance</span><span class="profile-value">${a.wallet.toFixed(2)} ${a.currency || 'USC'}</span></div>
      <div class="profile-stat"><span class="profile-label">EnergyCore</span><span class="profile-value">${(a.core_energy || 0).toFixed(2)}</span></div>
      <div class="profile-stat"><span class="profile-label">Total Value</span><span class="profile-value">${fmt(a.total_value || 0)}</span></div>
      <div class="profile-stat"><span class="profile-label">Influence</span><span class="profile-value">${a.influence}</span></div>
      <div class="profile-stat"><span class="profile-label">Risk</span><span class="profile-value">${a.risk}%</span></div>
      <div class="profile-stat"><span class="profile-label">Bank Balance</span><span class="profile-value">${(a.bank_balance || 0).toFixed(2)}</span></div>
      <div class="profile-stat"><span class="profile-label">Ideology</span><span class="profile-value">${a.ideology || '-'}</span></div>
      <div class="profile-stat"><span class="profile-label">Personality</span><span class="profile-value">${a.personality}</span></div>
    </div>
    ${a.company ? `<div class="profile-company">
      <h4>Company: ${esc(a.company.name)}</h4>
      <span>Cash: ${a.company.cash.toFixed(2)} · Productivity: ${a.company.productivity.toFixed(2)}</span>
    </div>` : ''}
    <div class="wealth-chart-container">
      <h4>Wealth History</h4>
      <div class="wealth-chart">${bars}</div>
    </div>
    <div class="decision-log-container">
      <h4>Recent Decisions</h4>
      <div class="decision-log">${logs || '<div class="empty-state">No decisions yet</div>'}</div>
    </div>
  `;
}

async function fetchEconomy() {
  try {
    const data = await api('/api/economy');
    if (!data.active) return;
    document.getElementById('e-money').textContent = fmt(data.total_money_supply);
    document.getElementById('e-energy').textContent = fmt(data.total_energy || 0);
    document.getElementById('e-burned').textContent = fmt(data.total_energy_burned || 0);
    document.getElementById('e-agents').textContent = data.alive_agents || data.agent_count;
    document.getElementById('e-companies').textContent = data.company_count;
    document.getElementById('e-gini').textContent = data.gini_index.toFixed(3);
    document.getElementById('gini-fill').style.width = (data.gini_index * 100) + '%';
    document.getElementById('e-dead').textContent = data.dead_agents || 0;
    document.getElementById('e-reserve').textContent = fmt(data.bank_reserve);

    const energyEl = document.getElementById('energy-stats');
    energyEl.innerHTML = `
      <div class="energy-row"><span class="energy-label">EnergyCore Price</span><span class="energy-val">${data.energy_price || 10} per unit</span></div>
      <div class="energy-row"><span class="energy-label">Total Energy in System</span><span class="energy-val">${fmt(data.total_energy || 0)}</span></div>
      <div class="energy-row"><span class="energy-label">Total Energy Burned</span><span class="energy-val">${fmt(data.total_energy_burned || 0)}</span></div>
      <div class="energy-row"><span class="energy-label">Bank Interest Rate</span><span class="energy-val">${((data.interest_rate || 0.02) * 100).toFixed(1)}%</span></div>
      <div class="energy-row"><span class="energy-label">Active Loans</span><span class="energy-val">${data.total_loans || 0}</span></div>
    `;

    const currEl = document.getElementById('currencies-grid');
    const currencies = data.currencies || {};
    currEl.innerHTML = Object.entries(currencies).map(([code, name]) =>
      `<div class="price-item"><span class="price-name">${code}</span><span class="price-val">${name}</span></div>`
    ).join('');

    const lb = document.getElementById('leaderboard');
    const top = data.top_agents || [];
    lb.innerHTML = top.map((a, i) => {
      const color = TYPE_COLORS[a.type] || '#64748b';
      const rank = i < 3 ? ['g', 's', 'b'][i] : '';
      return `<div class="lb-row">
        <span class="lb-rank ${rank}">${i + 1}</span>
        <span class="lb-dot" style="background:${color}"></span>
        <span class="lb-name">${esc(a.name)}</span>
        <span class="lb-val">${fmt(a.total_value || a.wallet)} · EC: ${(a.core_energy || 0).toFixed(1)}</span>
      </div>`;
    }).join('');
  } catch (e) { console.warn('economy fetch failed', e); }
}

async function createWorld() {
  await api('/api/simulation/control', { action: 'create_world' });
  fetchState();
}
async function startSim() {
  await api('/api/simulation/control', { action: 'start' });
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

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(fetchState, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  fetchState();
  startPolling();
});
