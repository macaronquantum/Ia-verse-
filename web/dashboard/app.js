let state = null;
let agentsData = [];
let selectedAgentId = null;
let map = null;
let agentMarkers = [];
let pollTimer = null;
let walletsData = [];
let transactionsData = [];
let currentView = 'map';
let simRunning = false;

function switchView(name) {
  currentView = name;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  document.querySelector(`[data-view="${name}"]`).classList.add('active');
  if (name === 'map' && !map) initMap();
  if (name === 'map' && map) map.invalidateSize();
  if (name === 'agents') fetchAgents();
  if (name === 'economy') fetchEconomy();
  if (name === 'wallets') fetchWallets();
  if (name === 'transactions') fetchTransactions();
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

const TX_COLORS = {
  deposit: '#2563eb', withdraw: '#ea580c', loan_issued: '#7c3aed',
  loan_repaid: '#16a34a', acquire_energy: '#0891b2', energy_burn: '#dc2626',
  revenue: '#16a34a', labor_income: '#64748b', dividend: '#ca8a04',
  company_create: '#6366f1', investment: '#2563eb', liquidity_injection: '#7c3aed',
  interest_rate_change: '#dc2626', web_search: '#0ea5e9',
  sub_agent_create: '#8b5cf6', sub_agent_revenue: '#a855f7',
  bank_lending: '#2563eb', interest_revenue: '#059669',
  web_action: '#06b6d4'
};

function initMap() {
  map = L.map('map-container', {
    center: [20, 0], zoom: 2.5, minZoom: 2, maxZoom: 8,
    zoomControl: false, attributionControl: false, worldCopyJump: true,
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
    if (currentView === 'map') updateMapAgents(data.agents || []);
    updateFeed();
  } catch (e) { console.warn('state fetch failed', e); }
}

function updateStatus(d) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  const tick = document.getElementById('tick-label');
  const toggleBtn = document.getElementById('btn-toggle');
  const toggleIcon = document.getElementById('toggle-icon');
  const toggleLabel = document.getElementById('toggle-label');

  if (!d.active) {
    dot.className = 'status-dot offline';
    label.textContent = 'No world';
    tick.textContent = 'Tick 0';
    simRunning = false;
  } else if (d.running) {
    dot.className = 'status-dot running';
    label.textContent = 'Running';
    tick.textContent = 'Tick ' + d.tick;
    simRunning = true;
  } else {
    dot.className = 'status-dot online';
    label.textContent = 'Paused';
    tick.textContent = 'Tick ' + d.tick;
    simRunning = false;
  }

  if (simRunning) {
    toggleBtn.classList.add('stop');
    toggleBtn.classList.remove('run');
    toggleIcon.className = 'toggle-icon stop-icon';
    toggleLabel.textContent = 'Stop';
  } else {
    toggleBtn.classList.remove('stop');
    toggleBtn.classList.add('run');
    toggleIcon.className = 'toggle-icon play-icon';
    toggleLabel.textContent = 'Run';
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
    if (selectedAgentId) {
      const exists = agentsData.find(a => a.id === selectedAgentId);
      if (exists) selectAgent(selectedAgentId);
    }
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

let agentProfileCache = null;

async function selectAgent(id) {
  selectedAgentId = id;
  document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.agent-item').forEach(el => {
    if (el.getAttribute('onclick')?.includes(id)) el.classList.add('active');
  });
  const panel = document.getElementById('agent-profile');
  panel.classList.add('fade-out');
  try {
    const a = await api(`/api/agents/${id}`);
    agentProfileCache = a;
    setTimeout(() => {
      renderAgentProfile(a, 'overview');
      panel.classList.remove('fade-out');
      panel.classList.add('fade-in');
      setTimeout(() => panel.classList.remove('fade-in'), 300);
    }, 150);
  } catch (e) { console.warn('profile load failed', e); }
}

function switchProfileTab(tab) {
  if (!agentProfileCache) return;
  document.querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.profile-tab[data-tab="${tab}"]`)?.classList.add('active');
  renderProfileContent(agentProfileCache, tab);
}

function renderAgentProfile(a, tab = 'overview') {
  const el = document.getElementById('agent-profile');
  const color = TYPE_COLORS[a.type] || '#64748b';
  const statusBadge = a.alive === false ? '<span class="dead-badge">INACTIVE</span>' : '';

  el.innerHTML = `
    <div class="profile-header" style="border-left:4px solid ${color}">
      <h2>${esc(a.name)} ${statusBadge}</h2>
      <div class="profile-type">${a.type.replace('_', ' ')} · ${a.country} · ${a.currency || 'USC'}</div>
    </div>
    <div class="profile-tabs">
      <button class="profile-tab ${tab === 'overview' ? 'active' : ''}" data-tab="overview" onclick="switchProfileTab('overview')">Overview</button>
      <button class="profile-tab ${tab === 'transactions' ? 'active' : ''}" data-tab="transactions" onclick="switchProfileTab('transactions')">Transactions</button>
      <button class="profile-tab ${tab === 'loans' ? 'active' : ''}" data-tab="loans" onclick="switchProfileTab('loans')">Loans</button>
      <button class="profile-tab ${tab === 'actions' ? 'active' : ''}" data-tab="actions" onclick="switchProfileTab('actions')">Actions</button>
      <button class="profile-tab ${tab === 'research' ? 'active' : ''}" data-tab="research" onclick="switchProfileTab('research')">Web Research</button>
      <button class="profile-tab ${tab === 'web_actions' ? 'active' : ''}" data-tab="web_actions" onclick="switchProfileTab('web_actions')">Web Actions</button>
      <button class="profile-tab ${tab === 'sub_agents' ? 'active' : ''}" data-tab="sub_agents" onclick="switchProfileTab('sub_agents')">Sub-Agents</button>
      <button class="profile-tab ${tab === 'wallet' ? 'active' : ''}" data-tab="wallet" onclick="switchProfileTab('wallet')">Solana Wallet</button>
    </div>
    <div id="profile-content" class="profile-content"></div>
  `;
  renderProfileContent(a, tab);
}

function renderProfileContent(a, tab) {
  const el = document.getElementById('profile-content');
  if (!el) return;
  const color = TYPE_COLORS[a.type] || '#64748b';

  if (tab === 'overview') {
    const wh = a.wealth_history || [];
    const maxW = Math.max(1, ...wh);
    const bars = wh.slice(-40).map(w => `<div class="wealth-bar" style="height:${Math.max(2, (w / maxW) * 100)}%;background:${color};"></div>`).join('');
    el.innerHTML = `
      <div class="profile-grid">
        <div class="profile-stat"><span class="profile-label">Wallet</span><span class="profile-value">${a.wallet.toFixed(2)} ${a.currency || 'USC'}</span></div>
        <div class="profile-stat"><span class="profile-label">EnergyCore</span><span class="profile-value">${(a.core_energy || 0).toFixed(2)}</span></div>
        <div class="profile-stat"><span class="profile-label">Total Value</span><span class="profile-value">${fmt(a.total_value || 0)}</span></div>
        <div class="profile-stat"><span class="profile-label">Bank Balance</span><span class="profile-value">${(a.bank_balance || 0).toFixed(2)}</span></div>
        <div class="profile-stat"><span class="profile-label">Influence</span><span class="profile-value">${a.influence}</span></div>
        <div class="profile-stat"><span class="profile-label">Risk</span><span class="profile-value">${a.risk}%</span></div>
        <div class="profile-stat"><span class="profile-label">Ideology</span><span class="profile-value">${a.ideology || '-'}</span></div>
        <div class="profile-stat"><span class="profile-label">Personality</span><span class="profile-value">${a.personality}</span></div>
      </div>
      ${a.company ? `<div class="profile-company">
        <h4>Company: ${esc(a.company.name)}</h4>
        <span>Cash: ${a.company.cash.toFixed(2)} · Productivity: ${a.company.productivity.toFixed(2)}</span>
      </div>` : ''}
      <div class="wealth-chart-container">
        <h4>Wealth History</h4>
        <div class="wealth-chart">${bars || '<div class="empty-state-sm">No history yet</div>'}</div>
      </div>
    `;
  } else if (tab === 'transactions') {
    const txs = a.transactions || [];
    if (!txs.length) {
      el.innerHTML = '<div class="empty-state">No transactions yet</div>';
      return;
    }
    el.innerHTML = `<div class="tx-list-profile">${txs.map(tx => renderTxCard(tx, true)).join('')}</div>`;
  } else if (tab === 'loans') {
    const loans = a.loans || [];
    if (!loans.length) {
      el.innerHTML = '<div class="empty-state">No active loans</div>';
      return;
    }
    el.innerHTML = `<div class="loans-list">${loans.map(l => `
      <div class="loan-card">
        <div class="loan-header">
          <span class="loan-id">Loan ${l.id.substring(0, 8)}...</span>
          <span class="loan-status ${l.remaining <= 0 ? 'paid' : 'active'}">${l.remaining <= 0 ? 'Paid' : 'Active'}</span>
        </div>
        <div class="loan-details">
          <div class="loan-detail"><span class="loan-label">Principal</span><span class="loan-val">${l.principal.toFixed(2)}</span></div>
          <div class="loan-detail"><span class="loan-label">Interest Rate</span><span class="loan-val">${(l.interest_rate * 100).toFixed(1)}%</span></div>
          <div class="loan-detail"><span class="loan-label">Remaining</span><span class="loan-val ${l.remaining > l.principal ? 'red' : ''}">${l.remaining.toFixed(2)}</span></div>
          <div class="loan-detail"><span class="loan-label">Accrued Interest</span><span class="loan-val">${Math.max(0, l.remaining - l.principal).toFixed(2)}</span></div>
        </div>
      </div>
    `).join('')}</div>`;
  } else if (tab === 'actions') {
    const logs = (a.decision_log || []).slice(-50);
    if (!logs.length) {
      el.innerHTML = '<div class="empty-state">No decisions yet</div>';
      return;
    }
    el.innerHTML = `<div class="actions-list">${logs.map(l => {
      const match = l.match(/\[tick (\d+)\] (\w+): (.+)/);
      if (match) {
        const [, tick, action, reason] = match;
        const actionColor = TX_COLORS[action] || '#64748b';
        return `<div class="action-item">
          <div class="action-meta"><span class="action-tick">Tick ${tick}</span><span class="action-type" style="color:${actionColor}">${action}</span></div>
          <div class="action-reason">${esc(reason)}</div>
        </div>`;
      }
      return `<div class="action-item"><div class="action-reason">${esc(l)}</div></div>`;
    }).reverse().join('')}</div>`;
  } else if (tab === 'research') {
    const searches = a.web_searches || [];
    if (!searches.length) {
      el.innerHTML = '<div class="empty-state">No web research yet. Agent will search the web when it needs real-world data to make decisions.</div>';
      return;
    }
    el.innerHTML = `<div class="research-list">${searches.map(s => `
      <div class="research-card">
        <div class="research-header">
          <span class="research-query">${esc(s.query)}</span>
          <span class="action-tick">Tick ${s.tick}</span>
        </div>
        <div class="research-results">
          ${(s.results || []).map(r => `
            <div class="research-result">
              <div class="research-title">${esc(r.title || 'Untitled')}</div>
              <div class="research-body">${esc((r.body || '').substring(0, 200))}</div>
              ${r.url ? `<a class="research-url" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.url.substring(0, 60))}...</a>` : ''}
            </div>
          `).join('')}
        </div>
        <div class="research-meta">${s.result_count} result${s.result_count !== 1 ? 's' : ''} found</div>
      </div>
    `).reverse().join('')}</div>`;
  } else if (tab === 'web_actions') {
    const actions = a.web_actions || [];
    if (!actions.length) {
      el.innerHTML = '<div class="empty-state">No web actions yet. Agent will perform autonomous web actions when needed.</div>';
      return;
    }
    el.innerHTML = `<div class="research-list">${actions.map(wa => `
      <div class="research-card" style="border-left:3px solid #06b6d4">
        <div class="research-header">
          <span class="research-query" style="color:#06b6d4">${esc(wa.action_type)}</span>
          <span class="action-tick">Tick ${wa.tick}</span>
        </div>
        <div class="wa-url">${esc(wa.url || 'N/A')}</div>
        <div class="wa-status"><span class="wa-status-badge ${wa.status === 'success' ? 'success' : 'fail'}">${wa.status}</span></div>
        ${wa.data ? `<div class="wa-data">${esc(JSON.stringify(wa.data).substring(0, 300))}</div>` : ''}
      </div>
    `).reverse().join('')}</div>`;
  } else if (tab === 'sub_agents') {
    const subs = a.sub_agents || [];
    if (!subs.length) {
      el.innerHTML = '<div class="empty-state">No sub-agents. This agent can create sub-agents specialized in tasks like market research, trading, or strategy analysis.</div>';
      return;
    }
    el.innerHTML = `<div class="sub-agents-list">${subs.map(s => {
      const specColor = {market_research:'#0ea5e9',code_generation:'#8b5cf6',social_media:'#ec4899',strategy_analysis:'#f59e0b',trading:'#16a34a',data_collection:'#06b6d4',content_creation:'#a855f7',risk_assessment:'#dc2626'}[s.specialty] || '#64748b';
      return `<div class="sub-agent-card">
        <div class="sub-agent-header">
          <span class="sub-agent-name">${esc(s.name)}</span>
          <span class="sub-agent-status ${s.active ? 'active' : 'inactive'}">${s.active ? 'Active' : 'Inactive'}</span>
        </div>
        <div class="sub-agent-specialty" style="color:${specColor}">${s.specialty.replace(/_/g, ' ')}</div>
        <div class="sub-agent-stats">
          <div class="sub-agent-stat"><span class="sub-agent-label">Revenue</span><span class="sub-agent-val">${s.revenue_generated.toFixed(2)}</span></div>
          <div class="sub-agent-stat"><span class="sub-agent-label">Tasks</span><span class="sub-agent-val">${s.tasks_completed}</span></div>
          <div class="sub-agent-stat"><span class="sub-agent-label">Your Ownership</span><span class="sub-agent-val">${s.ownership_pct.toFixed(1)}%</span></div>
          <div class="sub-agent-stat"><span class="sub-agent-label">Shareholders</span><span class="sub-agent-val">${s.shareholders}</span></div>
        </div>
      </div>`;
    }).join('')}</div>`;
  } else if (tab === 'wallet') {
    const sw = a.solana_wallet;
    if (!sw) {
      el.innerHTML = '<div class="empty-state">No Solana wallet assigned yet.</div>';
      return;
    }
    el.innerHTML = `
      <div class="solana-wallet-card">
        <div class="sw-header">Solana Wallet</div>
        <div class="sw-row"><span class="sw-label">Network</span><span class="sw-val">${esc(sw.network || 'solana')}</span></div>
        <div class="sw-row"><span class="sw-label">Public Key</span><code class="sw-key">${esc(sw.public_key)}</code></div>
        <div class="sw-row">
          <span class="sw-label">Private Key</span>
          <span class="sw-pk-wrap">
            <button class="reveal-btn" onclick="this.nextElementSibling.style.display='inline';this.style.display='none'">Reveal</button>
            <code class="sw-key pk-hidden" style="display:none">${esc(sw.private_key)}</code>
          </span>
        </div>
      </div>`;
  }
}

function renderTxCard(tx, compact = false) {
  const color = TX_COLORS[tx.type] || '#64748b';
  const typeLabel = tx.type.replace(/_/g, ' ');
  const details = tx.details || {};
  let detailsHtml = '';

  if (tx.type === 'loan_issued') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Principal</span><span>${details.principal?.toFixed(2) || tx.amount}</span></div>
      <div class="tx-detail-row"><span>Interest Rate</span><span>${((details.interest_rate || 0) * 100).toFixed(1)}%</span></div>
      <div class="tx-detail-row"><span>Remaining</span><span>${details.remaining?.toFixed(2) || '-'}</span></div>
    `;
  } else if (tx.type === 'loan_repaid') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Before</span><span>${details.remaining_before?.toFixed(2) || '-'}</span></div>
      <div class="tx-detail-row"><span>After</span><span>${details.remaining_after?.toFixed(2) || '-'}</span></div>
      <div class="tx-detail-row"><span>Fully Repaid</span><span>${details.fully_repaid ? 'Yes' : 'No'}</span></div>
    `;
  } else if (tx.type === 'acquire_energy') {
    detailsHtml = `
      <div class="tx-detail-row"><span>EC Units</span><span>${tx.amount.toFixed(2)}</span></div>
      <div class="tx-detail-row"><span>Cost</span><span>${details.cost_currency?.toFixed(2) || '-'} ${details.currency || ''}</span></div>
      <div class="tx-detail-row"><span>Price/Unit</span><span>${details.price_per_unit || '-'}</span></div>
    `;
  } else if (tx.type === 'dividend') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Revenue</span><span>${details.revenue?.toFixed(2) || '-'}</span></div>
      <div class="tx-detail-row"><span>Energy Cost</span><span>${details.energy_cost?.toFixed(2) || '-'} EC</span></div>
      <div class="tx-detail-row"><span>Productivity</span><span>${details.productivity?.toFixed(2) || '-'}</span></div>
    `;
  } else if (tx.type === 'revenue') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Total Revenue</span><span>${details.total_revenue?.toFixed(2) || '-'}</span></div>
      <div class="tx-detail-row"><span>Agent Share</span><span>${((details.agent_share || 0) * 100).toFixed(0)}%</span></div>
      <div class="tx-detail-row"><span>Company</span><span>${details.company || '-'}</span></div>
    `;
  } else if (tx.type === 'interest_rate_change') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Old Rate</span><span>${((details.old_rate || 0) * 100).toFixed(1)}%</span></div>
      <div class="tx-detail-row"><span>New Rate</span><span>${((details.new_rate || 0) * 100).toFixed(1)}%</span></div>
    `;
  } else if (tx.type === 'web_search') {
    const topResults = details.top_results || [];
    detailsHtml = `
      <div class="tx-detail-row"><span>Search Query</span><span>${esc(details.query || '')}</span></div>
      <div class="tx-detail-row"><span>Results Found</span><span>${details.result_count || 0}</span></div>
      ${topResults.map(r => `<div class="tx-detail-row"><span>Found</span><span><a href="${esc(r.url || '')}" target="_blank" rel="noopener">${esc((r.title || '').substring(0, 50))}</a></span></div>`).join('')}
      ${details.reasoning ? `<div class="tx-detail-row"><span>Reason</span><span>${esc(details.reasoning)}</span></div>` : ''}
    `;
  } else if (tx.type === 'sub_agent_create') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Sub-Agent</span><span>${esc(details.sub_agent_name || '')}</span></div>
      <div class="tx-detail-row"><span>Specialty</span><span>${esc(details.specialty || '')}</span></div>
      ${details.reasoning ? `<div class="tx-detail-row"><span>Reason</span><span>${esc(details.reasoning)}</span></div>` : ''}
    `;
  } else if (tx.type === 'sub_agent_revenue') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Sub-Agent</span><span>${esc(details.sub_agent_name || '')}</span></div>
      <div class="tx-detail-row"><span>Specialty</span><span>${esc(details.specialty || '')}</span></div>
      <div class="tx-detail-row"><span>Revenue</span><span>${(details.revenue || tx.amount).toFixed(2)}</span></div>
    `;
  } else if (tx.type === 'bank_lending') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Borrower</span><span>${esc(details.borrower || '')}</span></div>
      <div class="tx-detail-row"><span>Credit Score</span><span>${(details.credit_score || 0).toFixed(0)}</span></div>
      <div class="tx-detail-row"><span>Interest Rate</span><span>${((details.interest_rate || 0) * 100).toFixed(1)}%</span></div>
    `;
  } else if (tx.type === 'interest_revenue') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Source</span><span>${esc(details.source || 'loan interest')}</span></div>
      <div class="tx-detail-row"><span>Revenue</span><span>${(details.revenue || tx.amount).toFixed(2)}</span></div>
    `;
  } else if (tx.type === 'web_action') {
    detailsHtml = `
      <div class="tx-detail-row"><span>Action Type</span><span>${esc(details.action_type || '')}</span></div>
      <div class="tx-detail-row"><span>URL</span><span>${esc((details.url || '').substring(0, 50))}</span></div>
      <div class="tx-detail-row"><span>Status</span><span>${esc(details.status || '')}</span></div>
    `;
  }

  const hasDetails = detailsHtml.length > 0;
  const expandClass = hasDetails ? 'expandable' : '';

  return `<div class="tx-card ${expandClass} ${compact ? 'compact' : ''}" onclick="${hasDetails ? 'this.classList.toggle(\"expanded\")' : ''}">
    <div class="tx-card-header">
      <span class="tx-badge" style="background:${color}20;color:${color}">${typeLabel}</span>
      <span class="tx-tick">Tick ${tx.tick}</span>
    </div>
    <div class="tx-card-body">
      <div class="tx-agents">
        <span class="tx-from">${esc(tx.from_name)}</span>
        <span class="tx-arrow">&rarr;</span>
        <span class="tx-to">${esc(tx.to_name)}</span>
      </div>
      <span class="tx-amount">${tx.amount.toFixed(2)} ${tx.currency}</span>
    </div>
    ${hasDetails ? `<div class="tx-expand-content">${detailsHtml}</div>` : ''}
  </div>`;
}

async function fetchWallets() {
  try {
    const data = await api('/api/wallets');
    walletsData = data.wallets || [];
    renderWallets(walletsData);
  } catch (e) { console.warn('wallets fetch failed', e); }
}

function filterWallets() {
  const q = document.getElementById('wallet-search').value.toLowerCase();
  const type = document.getElementById('wallet-type-filter').value;
  let list = walletsData.filter(w => {
    if (q && !w.name.toLowerCase().includes(q)) return false;
    if (type !== 'all' && w.type !== type) return false;
    return true;
  });
  renderWallets(list);
}

function renderWallets(list) {
  const tbody = document.getElementById('wallets-tbody');
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No wallets found</td></tr>';
    return;
  }
  tbody.innerHTML = list.map(w => {
    const color = TYPE_COLORS[w.type] || '#64748b';
    const statusClass = w.alive === false ? 'dead-row' : '';
    const pubKey = w.solana_public_key || w.public_address || '';
    const privKey = w.solana_private_key || w.private_key || '';
    const network = w.network || 'solana';
    return `<tr class="${statusClass}">
      <td><div class="wallet-agent"><span class="wallet-dot" style="background:${color}"></span>${esc(w.name)}</div></td>
      <td><span class="type-badge" style="background:${color}15;color:${color}">${w.type.replace('_', ' ')}</span></td>
      <td>${w.currency}</td>
      <td class="num">${w.wallet_balance.toFixed(2)}</td>
      <td class="num">${w.bank_balance.toFixed(2)}</td>
      <td class="num">${w.core_energy.toFixed(2)}</td>
      <td><code class="addr" title="${esc(pubKey)}">${pubKey.substring(0, 8)}...${pubKey.slice(-6)}</code><span class="network-tag">${network}</span></td>
      <td><button class="reveal-btn" onclick="revealKey(this, '${esc(privKey)}')">Reveal</button></td>
    </tr>`;
  }).join('');
}

function revealKey(btn, key) {
  const td = btn.parentElement;
  if (btn.textContent === 'Reveal') {
    td.innerHTML = `<code class="pk-revealed">${key.substring(0, 12)}...${key.slice(-8)}</code>
      <button class="reveal-btn hide-btn" onclick="hideKey(this, '${key}')">Hide</button>`;
  }
}

function hideKey(btn, key) {
  const td = btn.parentElement;
  td.innerHTML = `<button class="reveal-btn" onclick="revealKey(this, '${key}')">Reveal</button>`;
}

async function fetchTransactions() {
  const txType = document.getElementById('tx-type-filter').value;
  const url = '/api/transactions' + (txType ? `?tx_type=${txType}` : '');
  try {
    const data = await api(url);
    transactionsData = data.transactions || [];
    document.getElementById('tx-count').textContent = `${data.total_count || transactionsData.length} transactions`;
    filterTransactionsLocal();
  } catch (e) { console.warn('transactions fetch failed', e); }
}

function filterTransactionsLocal() {
  const q = document.getElementById('tx-agent-search').value.toLowerCase();
  let list = transactionsData;
  if (q) {
    list = list.filter(tx =>
      tx.from_name.toLowerCase().includes(q) || tx.to_name.toLowerCase().includes(q)
    );
  }
  renderTransactions(list);
}

function renderTransactions(list) {
  const el = document.getElementById('tx-list');
  if (!list.length) {
    el.innerHTML = '<div class="empty-state">No transactions found</div>';
    return;
  }
  el.innerHTML = list.slice(0, 100).map(tx => renderTxCard(tx)).join('');
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

async function toggleSim() {
  if (simRunning) {
    await api('/api/simulation/control', { action: 'stop' });
  } else {
    await api('/api/simulation/control', { action: 'start' });
  }
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
