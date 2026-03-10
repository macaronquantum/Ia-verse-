async function load() {
  const res = await fetch('/monitoring/world');
  const data = await res.json();
  document.getElementById('metrics').textContent = JSON.stringify(data, null, 2);
}
load();
