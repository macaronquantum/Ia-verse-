let currentWorldId = null;
let autoInterval = null;
let previousPrices = {};

const API = '';

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function fmt(n) {
  if (n === undefined || n === null) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 10000) return (n / 1000).toFixed(1) + 'K';
  return n.toLocaleString('en-US', { maximumFractionDigits: 1 });
}

async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

async function createWorld() {
  const name = document.getElementById('world-name').value.trim();
  if (!name) return;
  try {
    const data = await api('POST', '/worlds', { name });
    currentWorldId = data.id;
    document.getElementById('agent-controls').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'block';
    updateDashboard(data);
  } catch (e) {
    console.error(e);
  }
}

async function createAgent() {
  if (!currentWorldId) return;
  const name = document.getElementById('agent-name').value.trim();
  if (!name) {
    const names = ['Atlas', 'Nova', 'Cipher', 'Echo', 'Vega', 'Orion', 'Luna', 'Nexus', 'Pulse', 'Flux'];
    document.getElementById('agent-name').value = names[Math.floor(Math.random() * names.length)] + '-' + Math.floor(Math.random() * 999);
    return createAgent();
  }
  try {
    const data = await api('POST', `/worlds/${currentWorldId}/agents`, { name });
    document.getElementById('agent-name').value = '';
    updateDashboard(data);
  } catch (e) {
    console.error(e);
  }
}

async function runTick() {
  if (!currentWorldId) return;
  const steps = parseInt(document.getElementById('tick-steps').value) || 1;
  try {
    const data = await api('POST', `/worlds/${currentWorldId}/tick`, { steps });
    updateDashboard(data);
  } catch (e) {
    console.error(e);
  }
}

function toggleAutoTick() {
  const btn = document.getElementById('auto-btn');
  if (autoInterval) {
    clearInterval(autoInterval);
    autoInterval = null;
    btn.classList.remove('active');
    btn.textContent = 'Auto';
  } else {
    btn.classList.add('active');
    btn.textContent = 'Stop';
    autoInterval = setInterval(() => runTick(), 1500);
  }
}

function updateDashboard(data) {
  const res = data.global_resources || {};
  const cap = 15000;

  updateResource('energy', res.energy, cap);
  updateResource('food', res.food, cap);
  updateResource('metal', res.metal, cap);
  updateResource('knowledge', res.knowledge, cap);

  updatePrices(data.market_prices || {});
  updateBank(data.bank || {});
  updateAgents(data.agents || []);
  updateCompanies(data.companies || []);
  updateLog(data.event_log || []);

  document.getElementById('tick-badge').textContent = `Tick ${data.tick_count || 0}`;
}

function updateResource(name, value, cap) {
  const v = value || 0;
  document.getElementById(`res-${name}`).textContent = fmt(v);
  const pct = Math.min(100, (v / cap) * 100);
  document.getElementById(`bar-${name}`).style.width = pct + '%';
}

function updatePrices(prices) {
  const grid = document.getElementById('price-grid');
  const resources = [
    { key: 'energy', label: 'Energy', color: 'var(--energy-color)' },
    { key: 'food', label: 'Food', color: 'var(--food-color)' },
    { key: 'metal', label: 'Metal', color: 'var(--metal-color)' },
    { key: 'knowledge', label: 'Knowledge', color: 'var(--knowledge-color)' },
  ];

  grid.innerHTML = resources.map(r => {
    const val = prices[r.key] || 0;
    const prev = previousPrices[r.key] || val;
    const change = val - prev;
    const pct = prev > 0 ? ((change / prev) * 100).toFixed(1) : '0.0';
    const dir = change > 0.01 ? 'up' : change < -0.01 ? 'down' : 'neutral';
    const arrow = dir === 'up' ? '+' : dir === 'down' ? '' : '';

    return `<div class="price-card">
      <span class="price-name">${r.label}</span>
      <span class="price-value" style="color:${r.color}">${val.toFixed(2)}</span>
      <span class="price-change ${dir}">${arrow}${pct}%</span>
    </div>`;
  }).join('');

  previousPrices = { ...prices };
}

function updateBank(bank) {
  document.getElementById('bank-reserve').textContent = fmt(bank.reserve || 0);
  const loans = bank.loans || [];
  document.getElementById('bank-loans').textContent = loans.length;
  const totalDebt = loans.reduce((sum, l) => sum + (l.remaining || 0), 0);
  document.getElementById('bank-debt').textContent = fmt(totalDebt);
}

function updateAgents(agents) {
  document.getElementById('agent-count').textContent = agents.length;
  const grid = document.getElementById('agent-grid');

  if (agents.length === 0) {
    grid.innerHTML = `<div class="empty-state">
      <div class="empty-state-icon">&#9775;</div>
      <span>No agents yet</span>
      <span style="font-size:0.7rem">Add an agent to begin</span>
    </div>`;
    return;
  }

  grid.innerHTML = agents.map(a => {
    const initials = esc(a.name.substring(0, 2).toUpperCase());
    const name = esc(a.name);
    const hasCompany = a.company_id ? 'Owner' : 'Free';
    return `<div class="entity-card">
      <div class="entity-header">
        <div class="entity-avatar agent-avatar">${initials}</div>
        <span class="entity-name">${name}</span>
      </div>
      <div class="entity-stats">
        <div class="entity-stat">
          <span class="entity-stat-label">Wallet</span>
          <span class="entity-stat-value">${fmt(a.wallet)}</span>
        </div>
        <div class="entity-stat">
          <span class="entity-stat-label">Status</span>
          <span class="entity-stat-value">${hasCompany}</span>
        </div>
      </div>
    </div>`;
  }).join('');
}

function updateCompanies(companies) {
  document.getElementById('company-count').textContent = companies.length;
  const grid = document.getElementById('company-grid');

  if (companies.length === 0) {
    grid.innerHTML = `<div class="empty-state">
      <div class="empty-state-icon">&#9881;</div>
      <span>No companies yet</span>
      <span style="font-size:0.7rem">Agents create companies automatically</span>
    </div>`;
    return;
  }

  grid.innerHTML = companies.map(c => {
    const initials = esc(c.name.substring(0, 2).toUpperCase());
    const name = esc(c.name);
    return `<div class="entity-card">
      <div class="entity-header">
        <div class="entity-avatar company-avatar">${initials}</div>
        <span class="entity-name">${name}</span>
      </div>
      <div class="entity-stats">
        <div class="entity-stat">
          <span class="entity-stat-label">Cash</span>
          <span class="entity-stat-value">${fmt(c.cash)}</span>
        </div>
        <div class="entity-stat">
          <span class="entity-stat-label">Productivity</span>
          <span class="entity-stat-value">${c.productivity.toFixed(2)}</span>
        </div>
      </div>
    </div>`;
  }).join('');
}

function updateLog(log) {
  const container = document.getElementById('event-log');
  const entries = log.slice(-60).reverse();

  container.innerHTML = entries.map(entry => {
    let cls = '';
    if (entry.includes('Crisis') || entry.includes('crisis')) cls = 'crisis';
    else if (entry.includes('company') || entry.includes('Company') || entry.includes('produced') || entry.includes('sold')) cls = 'company';
    else if (entry.includes('Agent') || entry.includes('cognition')) cls = 'agent';
    else if (entry.includes('loan') || entry.includes('deposited') || entry.includes('withdrew') || entry.includes('borrowed')) cls = 'bank';
    return `<div class="log-entry ${cls}">${esc(entry)}</div>`;
  }).join('');
}
