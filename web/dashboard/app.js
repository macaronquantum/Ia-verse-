let state = null;
let agentsData = [];
let selectedAgentId = null;
let globeScene, globeCamera, globeRenderer, globeGlobe, agentMeshes = [], raycaster, mouse;
let globeInitialized = false;
let pollInterval = null;

function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  document.querySelector(`[data-view="${name}"]`).classList.add('active');
  if (name === 'globe' && !globeInitialized) initGlobe();
  if (name === 'economy') fetchEconomy();
  if (name === 'agents') fetchAgents();
}

async function apiPost(url, data) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  return res.json();
}

async function fetchState() {
  try {
    const res = await fetch('/api/simulation/state');
    const data = await res.json();
    state = data;
    updateStatus(data);
    updateMiniStats(data);
    updateFeed(data);
    if (globeInitialized) updateGlobeAgents(data);
  } catch (e) {
    console.warn('fetch state failed', e);
  }
}

function updateStatus(data) {
  const dot = document.getElementById('status-indicator');
  const text = document.getElementById('status-text');
  const tick = document.getElementById('tick-display');
  if (!data.active) {
    dot.className = 'status-dot offline';
    text.textContent = 'No World';
    tick.textContent = 'Tick 0';
  } else if (data.running) {
    dot.className = 'status-dot running';
    text.textContent = 'Running';
    tick.textContent = 'Tick ' + data.tick;
  } else {
    dot.className = 'status-dot online';
    text.textContent = 'Paused';
    tick.textContent = 'Tick ' + data.tick;
  }
}

function updateMiniStats(data) {
  if (!data.active) return;
  document.getElementById('stat-agents').textContent = data.agents ? data.agents.length : 0;
  document.getElementById('stat-companies').textContent = data.companies ? data.companies.length : 0;
  document.getElementById('stat-money').textContent = '$' + formatNum(sumWallets(data));
  document.getElementById('stat-tick').textContent = data.tick;
}

function sumWallets(data) {
  if (!data.agents) return 0;
  return data.agents.reduce((s, a) => s + a.wallet, 0);
}

function formatNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return Math.round(n).toLocaleString();
}

function updateFeed(data) {
  const el = document.getElementById('feed-items');
  if (!data.ai_events || data.ai_events.length === 0) return;
  const last10 = data.ai_events.slice(-10).reverse();
  el.innerHTML = last10.map(e => {
    let cls = 'feed-item';
    if (e.includes('[AI]')) cls += ' ai';
    if (e.toLowerCase().includes('buy') || e.toLowerCase().includes('sell')) cls += ' trade';
    if (e.toLowerCase().includes('bankrupt') || e.toLowerCase().includes('fail')) cls += ' crisis';
    return `<div class="${cls}">${escHtml(e)}</div>`;
  }).join('');
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function initGlobe() {
  const container = document.getElementById('globe-container');
  const w = container.clientWidth;
  const h = container.clientHeight;

  globeScene = new THREE.Scene();
  globeCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  globeCamera.position.z = 3.5;

  globeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  globeRenderer.setSize(w, h);
  globeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  globeRenderer.setClearColor(0x060612, 1);
  container.appendChild(globeRenderer.domElement);

  const ambLight = new THREE.AmbientLight(0x334466, 0.6);
  globeScene.add(ambLight);
  const dirLight = new THREE.DirectionalLight(0x4fc3f7, 0.8);
  dirLight.position.set(5, 3, 5);
  globeScene.add(dirLight);

  const globeGeo = new THREE.SphereGeometry(1, 64, 64);
  const globeMat = new THREE.MeshPhongMaterial({
    color: 0x0a1628,
    emissive: 0x0a0a2e,
    specular: 0x4fc3f7,
    shininess: 15,
    transparent: true,
    opacity: 0.92,
    wireframe: false,
  });
  globeGlobe = new THREE.Mesh(globeGeo, globeMat);
  globeScene.add(globeGlobe);

  const wireGeo = new THREE.SphereGeometry(1.005, 36, 36);
  const wireMat = new THREE.MeshBasicMaterial({ color: 0x4fc3f7, wireframe: true, transparent: true, opacity: 0.06 });
  const wireframe = new THREE.Mesh(wireGeo, wireMat);
  globeScene.add(wireframe);

  const atmosGeo = new THREE.SphereGeometry(1.08, 64, 64);
  const atmosMat = new THREE.MeshBasicMaterial({ color: 0x4fc3f7, transparent: true, opacity: 0.04, side: THREE.BackSide });
  globeScene.add(new THREE.Mesh(atmosGeo, atmosMat));

  addStars();

  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  let isDragging = false, prevX = 0, prevY = 0, rotVelX = 0, rotVelY = 0;
  const canvas = globeRenderer.domElement;

  canvas.addEventListener('mousedown', e => { isDragging = true; prevX = e.clientX; prevY = e.clientY; rotVelX = 0; rotVelY = 0; });
  canvas.addEventListener('mousemove', e => {
    if (isDragging) {
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      globeGlobe.rotation.y += dx * 0.005;
      globeGlobe.rotation.x += dy * 0.005;
      rotVelX = dy * 0.005;
      rotVelY = dx * 0.005;
      prevX = e.clientX;
      prevY = e.clientY;
    }
    mouse.x = (e.offsetX / canvas.clientWidth) * 2 - 1;
    mouse.y = -(e.offsetY / canvas.clientHeight) * 2 + 1;
    checkHover(e);
  });
  canvas.addEventListener('mouseup', () => { isDragging = false; });
  canvas.addEventListener('wheel', e => {
    globeCamera.position.z = Math.max(2, Math.min(8, globeCamera.position.z + e.deltaY * 0.003));
  });

  function animate() {
    requestAnimationFrame(animate);
    if (!isDragging) {
      globeGlobe.rotation.y += 0.001;
      rotVelX *= 0.95;
      rotVelY *= 0.95;
      globeGlobe.rotation.y += rotVelY;
      globeGlobe.rotation.x += rotVelX;
    }
    agentMeshes.forEach(m => {
      if (m.userData.pulse) {
        m.scale.setScalar(m.userData.baseScale * (1 + 0.08 * Math.sin(Date.now() * 0.003 + m.userData.phase)));
      }
    });
    globeRenderer.render(globeScene, globeCamera);
  }
  animate();

  window.addEventListener('resize', () => {
    const w2 = container.clientWidth;
    const h2 = container.clientHeight;
    globeCamera.aspect = w2 / h2;
    globeCamera.updateProjectionMatrix();
    globeRenderer.setSize(w2, h2);
  });

  globeInitialized = true;
}

function addStars() {
  const starsGeo = new THREE.BufferGeometry();
  const positions = new Float32Array(3000);
  for (let i = 0; i < 3000; i++) {
    positions[i] = (Math.random() - 0.5) * 20;
  }
  starsGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const starsMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.015, transparent: true, opacity: 0.6 });
  globeScene.add(new THREE.Points(starsGeo, starsMat));
}

function latLngToVec3(lat, lng, r) {
  const phi = (90 - lat) * Math.PI / 180;
  const theta = (lng + 180) * Math.PI / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );
}

const TYPE_COLORS = {
  central_bank: 0x5c6bc0, bank: 0x1e88e5, company: 0x43a047, state: 0xe53935,
  judge: 0x8e24aa, energy_provider: 0xf9a825, trader: 0x00897b, citizen: 0x546e7a
};

let glowMeshes = [];

function updateGlobeAgents(data) {
  if (!data.active || !data.agents) return;

  agentMeshes.forEach(m => globeGlobe.remove(m));
  glowMeshes.forEach(m => globeGlobe.remove(m));
  agentMeshes = [];
  glowMeshes = [];

  data.agents.forEach(agent => {
    const pos = latLngToVec3(agent.lat, agent.lng, 1.02);
    const size = Math.max(0.02, Math.min(0.06, agent.wallet / 500));
    const color = TYPE_COLORS[agent.type] || 0x546e7a;

    let geo;
    if (agent.type === 'bank' || agent.type === 'central_bank') {
      geo = new THREE.BoxGeometry(size, size, size);
    } else if (agent.type === 'judge') {
      geo = new THREE.OctahedronGeometry(size * 0.7);
    } else {
      geo = new THREE.SphereGeometry(size * 0.7, 12, 12);
    }

    const mat = new THREE.MeshPhongMaterial({
      color: color, emissive: color, emissiveIntensity: 0.5,
      transparent: true, opacity: 0.9,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    mesh.lookAt(0, 0, 0);
    mesh.userData = { agent, pulse: true, baseScale: 1, phase: Math.random() * Math.PI * 2 };
    globeGlobe.add(mesh);
    agentMeshes.push(mesh);

    const glowGeo = new THREE.SphereGeometry(size * 1.5, 8, 8);
    const glowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.12 });
    const glow = new THREE.Mesh(glowGeo, glowMat);
    glow.position.copy(pos);
    globeGlobe.add(glow);
    glowMeshes.push(glow);
  });
}

function checkHover(event) {
  if (!globeInitialized || !agentMeshes.length) return;
  raycaster.setFromCamera(mouse, globeCamera);
  const intersects = raycaster.intersectObjects(agentMeshes);
  const tooltip = document.getElementById('agent-tooltip');
  if (intersects.length > 0) {
    const agent = intersects[0].object.userData.agent;
    tooltip.className = 'tooltip';
    tooltip.innerHTML = `
      <div class="tooltip-name">${escHtml(agent.name)}</div>
      <div class="tooltip-type">${agent.type}</div>
      <div class="tooltip-stat"><span>Wallet</span><span>$${agent.wallet.toFixed(0)}</span></div>
      <div class="tooltip-stat"><span>Country</span><span>${agent.country}</span></div>
      <div class="tooltip-stat"><span>Influence</span><span>${agent.influence}</span></div>
      <div class="tooltip-stat"><span>Personality</span><span>${agent.personality}</span></div>
    `;
    tooltip.style.left = event.clientX + 16 + 'px';
    tooltip.style.top = event.clientY - 20 + 'px';
  } else {
    tooltip.className = 'tooltip hidden';
  }
}

async function fetchAgents() {
  try {
    const res = await fetch('/api/agents');
    const data = await res.json();
    agentsData = data.agents || [];
    renderAgentList(agentsData);
  } catch (e) {
    console.warn('fetch agents failed', e);
  }
}

function filterAgents() {
  const search = document.getElementById('agent-search').value.toLowerCase();
  const typeFilter = document.getElementById('agent-type-filter').value;
  const sort = document.getElementById('agent-sort').value;

  let filtered = agentsData.filter(a => {
    if (search && !a.name.toLowerCase().includes(search)) return false;
    if (typeFilter !== 'all' && a.type !== typeFilter) return false;
    return true;
  });

  filtered.sort((a, b) => {
    if (sort === 'wallet') return b.wallet - a.wallet;
    if (sort === 'influence') return b.influence - a.influence;
    if (sort === 'risk') return b.risk - a.risk;
    if (sort === 'name') return a.name.localeCompare(b.name);
    return 0;
  });

  renderAgentList(filtered);
}

function renderAgentList(agents) {
  const el = document.getElementById('agents-list');
  if (!agents.length) {
    el.innerHTML = '<div class="empty-state"><span class="empty-state-icon">&#128100;</span><p>No agents found</p></div>';
    return;
  }
  el.innerHTML = agents.map(a => `
    <div class="agent-card ${selectedAgentId === a.id ? 'selected' : ''}" onclick="selectAgent('${a.id}')">
      <div class="agent-avatar avatar-${a.type}">${a.name.charAt(0)}</div>
      <div class="agent-info">
        <div class="agent-name">${escHtml(a.name)}</div>
        <div class="agent-meta">${a.type} &middot; ${a.country}</div>
      </div>
      <div class="agent-wallet">$${formatNum(a.wallet)}</div>
    </div>
  `).join('');
}

async function selectAgent(id) {
  selectedAgentId = id;
  document.querySelectorAll('.agent-card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector(`.agent-card[onclick*="${id}"]`);
  if (card) card.classList.add('selected');

  try {
    const res = await fetch('/api/agents/' + id);
    const agent = await res.json();
    renderAgentProfile(agent);
  } catch (e) {
    console.warn('fetch agent profile failed', e);
  }
}

function renderAgentProfile(a) {
  const el = document.getElementById('agent-profile-content');
  const maxWealth = a.wealth_history.length ? Math.max(...a.wealth_history, 1) : 1;
  const bars = a.wealth_history.slice(-40).map(w =>
    `<div class="wealth-bar" style="height:${Math.max(2, (w / maxWealth) * 100)}%"></div>`
  ).join('');

  const inventory = Object.entries(a.inventory || {}).map(([k, v]) =>
    `<div class="inv-item"><span class="inv-label">${k}</span><span class="inv-value">${v}</span></div>`
  ).join('');

  const decisions = (a.decision_log || []).slice(-15).reverse().map(d =>
    `<div class="decision-entry">${escHtml(d)}</div>`
  ).join('');

  el.innerHTML = `
    <div class="profile-header">
      <div class="profile-avatar avatar-${a.type}">${a.name.charAt(0)}</div>
      <div>
        <div class="profile-name">${escHtml(a.name)}</div>
        <div class="profile-type">${a.type}</div>
        <div class="profile-country">${a.country}</div>
      </div>
    </div>
    <div class="profile-stats">
      <div class="profile-stat"><span class="stat-label">Wallet</span><span class="stat-value">$${a.wallet.toFixed(2)}</span></div>
      <div class="profile-stat"><span class="stat-label">Total Assets</span><span class="stat-value">$${a.total_assets.toFixed(2)}</span></div>
      <div class="profile-stat"><span class="stat-label">Influence</span><span class="stat-value">${a.influence}</span></div>
      <div class="profile-stat"><span class="stat-label">Risk</span><span class="stat-value">${a.risk}</span></div>
      <div class="profile-stat"><span class="stat-label">Personality</span><span class="stat-value" style="font-size:0.85rem">${a.personality}</span></div>
      <div class="profile-stat"><span class="stat-label">Bank Balance</span><span class="stat-value">$${a.bank_balance}</span></div>
    </div>
    ${a.company ? `<div class="profile-section"><h3>Company</h3><div class="inv-item"><span class="inv-label">${escHtml(a.company.name)}</span><span class="inv-value">$${a.company.cash.toFixed(2)}</span></div></div>` : ''}
    <div class="profile-section"><h3>Wealth History</h3><div class="wealth-chart">${bars || '<div class="empty-state"><p>No history yet</p></div>'}</div></div>
    <div class="profile-section"><h3>Inventory</h3><div class="inventory-grid">${inventory}</div></div>
    <div class="profile-section"><h3>Decision Log</h3><div class="decision-log">${decisions || '<div class="empty-state"><p>No decisions yet</p></div>'}</div></div>
  `;
}

async function fetchEconomy() {
  try {
    const res = await fetch('/api/economy');
    const data = await res.json();
    if (!data.active) return;
    renderEconomy(data);
  } catch (e) {
    console.warn('fetch economy failed', e);
  }
}

function renderEconomy(data) {
  document.getElementById('eco-money').textContent = '$' + formatNum(data.total_money_supply);
  document.getElementById('eco-energy').textContent = formatNum(data.total_energy);
  document.getElementById('eco-gini').textContent = data.gini_index.toFixed(3);
  document.getElementById('gini-bar').style.width = (data.gini_index * 100) + '%';
  document.getElementById('eco-agents').textContent = data.agent_count;
  document.getElementById('eco-companies').textContent = data.company_count;
  document.getElementById('eco-bankrupt').textContent = data.bankrupt_agents;
  document.getElementById('eco-reserve').textContent = '$' + formatNum(data.bank_reserve);
  document.getElementById('eco-loans').textContent = data.total_loans;

  const pricesEl = document.getElementById('prices-grid');
  const prices = data.market_prices || {};
  pricesEl.innerHTML = Object.entries(prices).map(([k, v]) =>
    `<div class="price-card"><span class="price-name">${k}</span><span class="price-value price-${k}">$${v.toFixed(2)}</span></div>`
  ).join('');

  const lbEl = document.getElementById('leaderboard');
  const top = data.top_agents || [];
  lbEl.innerHTML = top.map((a, i) => {
    let rankCls = 'lb-rank';
    if (i === 0) rankCls += ' gold';
    else if (i === 1) rankCls += ' silver';
    else if (i === 2) rankCls += ' bronze';
    return `<div class="lb-row">
      <span class="${rankCls}">${i + 1}</span>
      <span class="lb-name">${escHtml(a.name)}</span>
      <span class="lb-type">${a.type}</span>
      <span class="lb-wallet">$${formatNum(a.wallet)}</span>
    </div>`;
  }).join('');

  const resEl = document.getElementById('resources-bars');
  const resources = data.global_resources || {};
  const maxRes = Math.max(...Object.values(resources), 1);
  resEl.innerHTML = Object.entries(resources).map(([k, v]) =>
    `<div class="resource-bar-row">
      <span class="resource-bar-label">${k}</span>
      <div class="resource-bar-track"><div class="resource-bar-fill ${k}" style="width:${(v / maxRes * 100).toFixed(1)}%"></div></div>
      <span class="resource-bar-val">${formatNum(v)}</span>
    </div>`
  ).join('');
}

async function createWorld() {
  const count = parseInt(document.getElementById('agent-count-slider').value);
  const data = await apiPost('/api/simulation/control', { action: 'create_world', agent_count: count });
  addLogEntry('World created with ' + count + ' agents');
  fetchState();
}

async function startSim() {
  const speed = parseInt(document.getElementById('speed-slider').value);
  await apiPost('/api/simulation/control', { action: 'start', speed: speed });
  addLogEntry('Simulation started (speed: ' + speed + 's/tick)');
}

async function pauseSim() {
  await apiPost('/api/simulation/control', { action: 'pause' });
  addLogEntry('Simulation paused');
}

async function manualTick() {
  const data = await apiPost('/api/simulation/control', { action: 'tick' });
  addLogEntry('Manual tick executed (tick ' + (data.tick || '?') + ')');
  fetchState();
}

async function setSpeed(val) {
  await apiPost('/api/simulation/control', { action: 'speed', speed: parseInt(val) });
}

async function spawnAgent() {
  const name = document.getElementById('new-agent-name').value.trim();
  if (!name) return;
  await apiPost('/api/simulation/control', { action: 'spawn_agent', agent_name: name });
  document.getElementById('new-agent-name').value = '';
  addLogEntry('Spawned agent: ' + name);
  fetchState();
}

function addLogEntry(text) {
  const el = document.getElementById('event-log');
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  if (text.includes('[AI]')) entry.className += ' ai';
  if (text.toLowerCase().includes('buy') || text.toLowerCase().includes('sell')) entry.className += ' trade';
  if (text.toLowerCase().includes('loan') || text.toLowerCase().includes('bank')) entry.className += ' bank';
  entry.textContent = text;
  el.appendChild(entry);
  el.scrollTop = el.scrollHeight;
}

function updateEventLog(data) {
  if (!data.events) return;
  const el = document.getElementById('event-log');
  el.innerHTML = '';
  data.events.slice(-40).forEach(e => addLogEntry(e));
}

fetchState();
initGlobe();

pollInterval = setInterval(() => {
  fetchState();
  const activeView = document.querySelector('.view.active');
  if (activeView && activeView.id === 'view-economy') fetchEconomy();
  if (activeView && activeView.id === 'view-agents' && selectedAgentId) selectAgent(selectedAgentId);
  if (activeView && activeView.id === 'view-controls' && state) updateEventLog(state);
}, 4000);
