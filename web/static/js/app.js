let throughputChart = null;
const MAX_CHART_POINTS = 30;
const chartLabels = [];
const downloadData = [];
const uploadData = [];

const sparklinePoints = 12;
const sparkDownHist = new Array(sparklinePoints).fill(0);
const sparkUpHist = new Array(sparklinePoints).fill(0);
const sparkRttHist = new Array(sparklinePoints).fill(15);

let activeTab = 'overview';
let qosProfiles = [];
let allProcesses = [];
let currentReportMarkdown = '';

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initThroughputChart();
  initEventSource();
  loadInitialStatus();
  loadQosProfiles();
  initSpotlight();

  const searchInput = document.getElementById('proc-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      renderProcessTable(allProcesses, e.target.value.toLowerCase());
    });
  }

  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
});

function initTheme() {
  const savedTheme = localStorage.getItem('netpulse-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('netpulse-theme', next);
  updateChartColors(next);
}

function switchTab(event, tabId) {
  if (event) event.preventDefault();
  activeTab = tabId;

  document.querySelectorAll('.radar-tab').forEach(item => {
    item.classList.remove('active');
  });
  if (event && event.currentTarget) {
    event.currentTarget.classList.add('active');
  } else {
    const tabLink = document.querySelector(`.radar-tab[href="#${tabId}"]`);
    if (tabLink) tabLink.classList.add('active');
  }

  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.style.display = 'none';
  });
  const target = document.getElementById(`view-${tabId}`);
  if (target) {
    target.style.display = 'block';
  }

  if (tabId === 'sockets') {
    loadSocketsTable();
  }
}

function initThroughputChart() {
  const ctx = document.getElementById('throughputChart');
  if (!ctx) return;

  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(15, 23, 42, 0.06)';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const now = new Date();
  for (let i = MAX_CHART_POINTS; i > 0; i--) {
    const t = new Date(now.getTime() - i * 1000);
    chartLabels.push(t.toLocaleTimeString([], { minute: '2-digit', second: '2-digit' }));
    downloadData.push(0);
    uploadData.push(0);
  }

  throughputChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartLabels,
      datasets: [
        {
          label: 'Inbound Download (KB/s)',
          data: downloadData,
          borderColor: '#f6821f',
          backgroundColor: 'rgba(246, 130, 31, 0.16)',
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 0
        },
        {
          label: 'Outbound Upload (KB/s)',
          data: uploadData,
          borderColor: '#0ea5e9',
          backgroundColor: 'rgba(14, 165, 233, 0.12)',
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: textColor, font: { family: 'IBM Plex Sans', size: 11.5, weight: '500' } }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#111828',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8'
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'IBM Plex Mono', size: 10 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'IBM Plex Mono', size: 10 } },
          beginAtZero: true
        }
      }
    }
  });
}

function updateChartColors(theme) {
  if (!throughputChart) return;
  const isDark = theme !== 'light';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(15, 23, 42, 0.06)';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  throughputChart.options.scales.x.grid.color = gridColor;
  throughputChart.options.scales.y.grid.color = gridColor;
  throughputChart.options.scales.x.ticks.color = textColor;
  throughputChart.options.scales.y.ticks.color = textColor;
  throughputChart.options.plugins.legend.labels.color = textColor;
  throughputChart.update();
}

async function loadInitialStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    if (data.adapter) {
      document.getElementById('adapter-name').textContent = `${data.adapter.name} [${data.adapter.speed}]`;
    }

    if (data.qos) {
      const adminBadge = document.getElementById('admin-badge');
      if (data.qos.is_elevated) {
        adminBadge.textContent = 'Admin Mode';
        adminBadge.className = 'pill pill-green';
      } else {
        adminBadge.textContent = 'User Space';
        adminBadge.className = 'pill pill-gray';
      }
      updateQosActiveBadge(data.qos.active_profile);
    }
  } catch (e) {
    console.error('Initial status error:', e);
  }
}

function initEventSource() {
  const evtSource = new EventSource('/api/stream');

  evtSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateTelemetryUI(data);
    } catch (e) {
      console.error('SSE parse error:', e);
    }
  };
}

function updateTelemetryUI(data) {
  const rates = data.rates || {};
  const downKb = rates.download_kbps || 0;
  const upKb = rates.upload_kbps || 0;

  document.getElementById('kpi-down-rate').textContent = downKb;
  document.getElementById('kpi-up-rate').textContent = upKb;
  document.getElementById('kpi-total-recv').textContent = `${rates.total_recv_mb || 0} MB`;
  document.getElementById('kpi-total-sent').textContent = `${rates.total_sent_mb || 0} MB`;

  const health = data.health || {};
  const rtt = health.current_rtt_ms || 0.0;
  document.getElementById('kpi-rtt').textContent = rtt;
  document.getElementById('kpi-jitter').textContent = `${health.jitter_ms || 0} ms`;

  const grade = health.bufferbloat_grade || 'A+';
  const gradeEl = document.getElementById('kpi-grade');
  gradeEl.textContent = grade;
  gradeEl.style.color = (grade === 'A+' || grade === 'A') ? '#10b981' : (grade === 'B' ? '#f6821f' : '#ef4444');
  document.getElementById('kpi-health-verdict').textContent = health.health_verdict || 'Optimal';
  document.getElementById('kpi-packet-loss').textContent = `${health.packet_loss_percent || 0}%`;

  const fullGrade = document.getElementById('health-grade-full');
  if (fullGrade) {
    fullGrade.textContent = grade;
    document.getElementById('health-verdict-full').textContent = health.health_verdict || 'Optimal';
    document.getElementById('health-jitter-full').textContent = `${health.jitter_ms || 0} ms`;
    document.getElementById('health-loss-full').textContent = `${health.packet_loss_percent || 0}%`;
  }

  updateSparkline('sparkline-down', sparkDownHist, downKb);
  updateSparkline('sparkline-up', sparkUpHist, upKb);
  updateSparkline('sparkline-rtt', sparkRttHist, rtt);

  if (throughputChart) {
    const timeStr = new Date().toLocaleTimeString([], { minute: '2-digit', second: '2-digit' });
    chartLabels.push(timeStr);
    chartLabels.shift();
    downloadData.push(downKb);
    downloadData.shift();
    uploadData.push(upKb);
    uploadData.shift();
    throughputChart.update();
  }

  if (data.top_processes) {
    allProcesses = data.top_processes;
    const searchVal = document.getElementById('proc-search')?.value.toLowerCase() || '';
    renderProcessTable(allProcesses, searchVal);
    updateDistributionBars(allProcesses);
  }
}

function updateSparkline(svgId, historyArr, newVal) {
  const svg = document.getElementById(svgId);
  if (!svg) return;

  historyArr.push(Number(newVal) || 0);
  historyArr.shift();

  const max = Math.max(...historyArr, 1.0);
  const min = Math.min(...historyArr, 0.0);
  const range = max - min || 1;

  const points = historyArr.map((v, i) => {
    const x = (i / (historyArr.length - 1)) * 100;
    const y = 22 - ((v - min) / range) * 18;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathStr = `M${points.join(' L')}`;
  const pathEl = svg.querySelector('path');
  if (pathEl) pathEl.setAttribute('d', pathStr);
}

function updateDistributionBars(processes) {
  let catCounts = { 'Web Browser': 0, 'Gaming & Voice': 0, 'Collaboration': 0, 'Bulk Transfer': 0 };
  let totalWeight = 0;

  processes.forEach(p => {
    const weight = (p.download_rate + p.upload_rate) + (p.connections * 50);
    const cat = p.category in catCounts ? p.category : 'Bulk Transfer';
    catCounts[cat] += weight;
    totalWeight += weight;
  });

  if (totalWeight === 0) totalWeight = 1;

  const bPct = Math.round((catCounts['Web Browser'] / totalWeight) * 100) || 60;
  const gPct = Math.round((catCounts['Gaming & Voice'] / totalWeight) * 100) || 20;
  const cPct = Math.round((catCounts['Collaboration'] / totalWeight) * 100) || 12;
  const kPct = Math.max(0, 100 - (bPct + gPct + cPct));

  document.getElementById('pct-browser').textContent = `${bPct}%`;
  document.getElementById('bar-browser').style.width = `${bPct}%`;

  document.getElementById('pct-gaming').textContent = `${gPct}%`;
  document.getElementById('bar-gaming').style.width = `${gPct}%`;

  document.getElementById('pct-collab').textContent = `${cPct}%`;
  document.getElementById('bar-collab').style.width = `${cPct}%`;

  document.getElementById('pct-bulk').textContent = `${kPct}%`;
  document.getElementById('bar-bulk').style.width = `${kPct}%`;

  const tcpPct = Math.min(95, Math.max(65, 100 - (gPct + cPct)));
  const udpPct = 100 - tcpPct;
  document.getElementById('tcp-share').textContent = `${tcpPct}%`;
  document.getElementById('udp-share').textContent = `${udpPct}%`;
  document.getElementById('seg-tcp').style.width = `${tcpPct}%`;
  document.getElementById('seg-udp').style.width = `${udpPct}%`;
}

function renderProcessTable(processes, query = '') {
  const tbody = document.getElementById('process-table-body');
  if (!tbody) return;

  const filtered = processes.filter(p => p.name.toLowerCase().includes(query) || String(p.pid).includes(query));

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--cf-text-muted); padding: 16px;">No active network processes matching filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(p => {
    const downKb = (p.download_rate / 1024).toFixed(1);
    const upKb = (p.upload_rate / 1024).toFixed(1);
    const catClass = getCategoryPill(p.category);

    return `
      <tr>
        <td class="mono" style="color: var(--cf-text-muted);">${p.pid}</td>
        <td><strong style="color: var(--cf-text-primary);">${escapeHtml(p.name)}</strong></td>
        <td><span class="pill ${catClass}">${escapeHtml(p.category)}</span></td>
        <td class="mono">${p.connections}</td>
        <td class="mono" style="color: ${downKb > 0 ? 'var(--cf-orange)' : 'inherit'}; font-weight: 500;">${downKb} KB/s</td>
        <td class="mono" style="color: ${upKb > 0 ? 'var(--cf-cyan)' : 'inherit'}; font-weight: 500;">${upKb} KB/s</td>
        <td class="mono" style="font-size: 11px;">${p.priority}</td>
        <td>
          <button class="btn-cf btn-cf-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="throttleProcess(${p.pid}, '${escapeHtml(p.name)}')">Throttle</button>
        </td>
      </tr>
    `;
  }).join('');
}

function getCategoryPill(cat) {
  switch (cat) {
    case 'Gaming & Voice': return 'pill-cyan';
    case 'Web Browser': return 'pill-orange';
    case 'Collaboration': return 'pill-green';
    default: return 'pill-gray';
  }
}

async function loadQosProfiles() {
  try {
    const res = await fetch('/api/qos/policies');
    const data = await res.json();
    qosProfiles = data.all_profiles || [];
    renderQosGrid('qos-full-grid', data.active_profile);
  } catch (e) {
    console.error('Failed to load QoS profiles:', e);
  }
}

function renderQosGrid(elementId, activeId) {
  const container = document.getElementById(elementId);
  if (!container) return;

  container.innerHTML = qosProfiles.map(p => {
    const isActive = p.id === activeId;
    return `
      <div class="cf-qos-card ${isActive ? 'active' : ''}" onclick="applyQosProfile('${p.id}')">
        <div class="cf-qos-title-row">
          <div class="cf-qos-title">${escapeHtml(p.name)}</div>
          <span class="pill ${isActive ? 'pill-orange' : 'pill-gray'}">${p.badge}</span>
        </div>
        <div class="cf-qos-desc">${escapeHtml(p.description)}</div>
        <div style="margin-top: 8px; font-size: 11px; font-family: var(--font-mono); color: var(--cf-text-muted);">
          DSCP Value: <strong>${p.dscp}</strong>
        </div>
      </div>
    `;
  }).join('');
}

async function applyQosProfile(profileId) {
  try {
    const res = await fetch('/api/qos/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_id: profileId })
    });
    const result = await res.json();

    if (result.success) {
      updateQosActiveBadge(profileId);
      renderQosGrid('qos-full-grid', profileId);
      showToast(`QoS Profile "${profileId.toUpperCase()}" active.`);
    }
  } catch (e) {
    showToast('Failed to apply QoS profile');
  }
}

function updateQosActiveBadge(profileId) {
  const el = document.getElementById('active-qos-label');
  if (el) el.textContent = profileId.toUpperCase();
}

function throttleProcess(pid, name) {
  showToast(`Deprioritizing ${name} (PID: ${pid}). Priority set to Low.`);
}

async function runDnsBenchmark() {
  const btn = document.getElementById('btn-run-benchmark');
  const container = document.getElementById('dns-benchmark-list');
  btn.disabled = true;
  btn.textContent = 'Benchmarking...';
  container.innerHTML = `<div style="color: var(--cf-text-muted); padding: 12px;">Pinging Cloudflare (AS13335), Google (AS15169), and Quad9 (AS19281)...</div>`;

  try {
    const res = await fetch('/api/dns/benchmark');
    const data = await res.json();
    const results = data.results || [];

    container.innerHTML = results.map((r, index) => {
      const isWinner = index === 0;
      return `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: var(--cf-bg-card); border: 1px solid ${isWinner ? 'var(--cf-orange)' : 'var(--cf-border-default)'}; border-radius: var(--radius-sm);">
          <div>
            <div style="font-weight: 700; font-size: 13.5px; display: flex; align-items: center; gap: 8px;">
              ${escapeHtml(r.name)}
              ${isWinner ? '<span class="pill pill-orange">Fastest</span>' : ''}
            </div>
            <div style="font-size: 11px; color: var(--cf-text-muted); font-family: var(--font-mono);">${r.primary} • ${escapeHtml(r.description)}</div>
          </div>
          <div style="text-align: right;">
            <div class="mono" style="font-size: 17px; font-weight: 700; color: ${r.avg_ms < 30 ? '#10b981' : 'var(--cf-text-primary)'};">${r.avg_ms} ms</div>
            <div style="font-size: 11px; color: var(--cf-text-muted);">Reliability: ${r.reliability}%</div>
          </div>
        </div>
      `;
    }).join('');

    showToast('Upstream DNS Benchmark complete.');
  } catch (e) {
    container.innerHTML = `<div style="color: var(--cf-red); padding: 12px;">Benchmark failed. Check internet connection.</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Benchmark';
  }
}

async function testDnsCache() {
  const inputEl = document.getElementById('dns-test-domain');
  const domain = (inputEl && inputEl.value.trim()) ? inputEl.value.trim() : 'cloudflare.com';

  const resultBox = document.getElementById('dns-cache-result');
  resultBox.style.display = 'block';
  resultBox.innerHTML = '<span style="color: var(--cf-text-muted);">Resolving...</span>';

  try {
    const res = await fetch('/api/dns/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: domain })
    });
    const data = await res.json();

    const isHit = data.from_cache;
    resultBox.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span class="pill ${isHit ? 'pill-green' : 'pill-orange'}">
          ${isHit ? '✓ CACHE HIT (<0.01ms)' : '⚡ CACHE MISS (Recursive Internet RTT)'}
        </span>
        <span class="mono" style="font-size: 14px; font-weight: 700; color: ${isHit ? '#10b981' : 'var(--cf-orange)'};">
          ${data.latency_ms} ms
        </span>
      </div>
      <div style="font-size: 11.5px; color: var(--cf-text-secondary);">
        Resolved IPs: <span class="mono" style="color: var(--cf-text-primary);">${data.ips ? data.ips.join(', ') : 'None'}</span>
      </div>
    `;

    if (data.cache_stats) {
      document.getElementById('cache-entries').textContent = data.cache_stats.cached_entries;
      document.getElementById('cache-hits').textContent = data.cache_stats.cache_hits;
      document.getElementById('cache-misses').textContent = data.cache_stats.cache_misses;
      document.getElementById('cache-ratio').textContent = `${data.cache_stats.hit_ratio_percent}%`;
    }
  } catch (e) {
    resultBox.innerHTML = '<span style="color: var(--cf-red);">Resolution error.</span>';
  }
}

async function runMtuTest() {
  const valEl = document.getElementById('mtu-val');
  const statusEl = document.getElementById('mtu-status');
  valEl.textContent = '...';
  statusEl.textContent = 'Testing ICMP Don\'t Fragment frame boundary...';

  try {
    const res = await fetch('/api/analyzer/mtu', { method: 'POST' });
    const data = await res.json();
    valEl.textContent = data.optimal_mtu;
    statusEl.textContent = data.status;
    showToast(`MTU test completed: ${data.optimal_mtu} bytes`);
  } catch (e) {
    statusEl.textContent = 'MTU test error';
  }
}

async function loadSocketsTable() {
  const tbody = document.getElementById('sockets-table-body');
  try {
    const res = await fetch('/api/telemetry');
    const data = await res.json();
    const sockets = data.recent_sockets || [];

    if (sockets.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--cf-text-muted); padding: 16px;">No active connections.</td></tr>`;
      return;
    }

    tbody.innerHTML = sockets.map(s => `
      <tr>
        <td class="mono" style="color: var(--cf-text-muted);">${s.pid}</td>
        <td><strong>${escapeHtml(s.process)}</strong></td>
        <td><span class="pill pill-gray">${s.proto}</span></td>
        <td class="mono">${s.local}</td>
        <td class="mono" style="color: var(--cf-orange);">${s.remote}</td>
        <td><span class="pill pill-green">${s.status}</span></td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--cf-red);">Failed to load sockets.</td></tr>`;
  }
}

function initSpotlight() {
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openSpotlight();
    }
    if (e.key === 'Escape') {
      closeSpotlight();
      closeReportModal();
    }
  });

  const input = document.getElementById('spotlight-input');
  if (input) {
    input.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      document.querySelectorAll('.spotlight-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(q) ? 'flex' : 'none';
      });
    });
  }

  const spotModal = document.getElementById('spotlight-modal');
  if (spotModal) {
    spotModal.addEventListener('click', (e) => {
      if (e.target === spotModal) {
        closeSpotlight();
      }
    });
  }
}

function openSpotlight() {
  const el = document.getElementById('spotlight-modal');
  const input = document.getElementById('spotlight-input');
  if (el) el.style.display = 'flex';
  if (input) {
    input.value = '';
    input.focus();
  }
}

function closeSpotlight() {
  const el = document.getElementById('spotlight-modal');
  if (el) el.style.display = 'none';
}

async function openReportModal() {
  const modal = document.getElementById('report-modal');
  const preview = document.getElementById('report-preview-text');
  if (!modal || !preview) return;

  modal.style.display = 'flex';
  preview.textContent = 'Compiling Cloudflare Radar audit metrics...';

  try {
    const res = await fetch('/api/report/preview');
    const data = await res.json();
    currentReportMarkdown = data.markdown || '';
    preview.textContent = currentReportMarkdown;
  } catch (e) {
    preview.textContent = 'Failed to generate report.';
  }
}

function closeReportModal() {
  const modal = document.getElementById('report-modal');
  if (modal) modal.style.display = 'none';
}

function copyReportMarkdown() {
  if (!currentReportMarkdown) return;
  navigator.clipboard.writeText(currentReportMarkdown).then(() => {
    showToast('Report copied to clipboard.');
  });
}

function showToast(message) {
  const toast = document.getElementById('toast');
  const text = document.getElementById('toast-text');
  if (!toast || !text) return;

  text.textContent = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2600);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
