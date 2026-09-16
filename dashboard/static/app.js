let currentHorizon = 5;
let currentStrategy = "london_only";
let isLogScale = false;
let liveBalance = 1000.0;
let chartInstance = null;
let strategiesData = {};

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  await loadStatus();
  await loadStrategies();
  await updateProjections();
  setupEventListeners();
  // Refresc d'estat cada 15 segons
  setInterval(loadStatus, 15000);
}

function setupEventListeners() {
  const stratSelect = document.getElementById("strategySelect");
  stratSelect.addEventListener("change", (e) => {
    currentStrategy = e.target.value;
    updateStrategyCards();
    updateProjections();
  });

  const slider = document.getElementById("balanceSlider");
  slider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    document.getElementById("sliderValue").textContent = `$${val.toLocaleString()}`;
    loadWithdrawalAdvice(val);
  });
}

// 1. Carregar estat del compte Tradovate
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();

    liveBalance = data.cash_balance;

    // Actualitzar Pills
    const statusDot = document.getElementById("statusDot");
    const statusPing = document.getElementById("statusPing");
    const statusText = document.getElementById("statusText");
    const envBadge = document.getElementById("envBadge");

    envBadge.textContent = data.environment;
    if (data.environment === "LIVE") {
      envBadge.className = "text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 uppercase font-bold";
    }

    if (data.connected) {
      statusText.textContent = `TRADOVATE CONNECTAT (${data.account_spec})`;
      statusDot.className = "relative inline-flex rounded-full h-2 w-2 bg-emerald-500";
      statusPing.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75";
    } else {
      statusText.textContent = `SIMULACIÓ TRADOVATE (${data.account_spec})`;
      statusDot.className = "relative inline-flex rounded-full h-2 w-2 bg-amber-500";
      statusPing.className = "hidden";
    }

    document.getElementById("activeContract").textContent = data.active_contract;
    document.getElementById("cardBalance").textContent = `$${liveBalance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Posició recomanada segons saldo
    let contracts = 1;
    let nextMilestone = "$2,200";
    if (liveBalance >= 4800) {
      contracts = 4;
      nextMilestone = "$6,500";
    } else if (liveBalance >= 3500) {
      contracts = 3;
      nextMilestone = "$4,800";
    } else if (liveBalance >= 2200) {
      contracts = 2;
      nextMilestone = "$3,500";
    }

    document.getElementById("cardContracts").textContent = `${contracts} MNQ`;
    document.getElementById("cardNextMilestone").textContent = nextMilestone;

    // Actualitzar consell de retirada
    loadWithdrawalAdvice(liveBalance);

  } catch (err) {
    console.error("Error carregant estat:", err);
  }
}

// 2. Carregar metadades de les estratègies
async function loadStrategies() {
  try {
    const res = await fetch("/api/strategies");
    strategiesData = await res.json();
    updateStrategyCards();
  } catch (err) {
    console.error("Error carregant estratègies:", err);
  }
}

function updateStrategyCards() {
  const strat = strategiesData[currentStrategy];
  if (!strat) return;

  document.getElementById("cardWinRate").textContent = `${strat.win_rate}%`;
  document.getElementById("cardProfitFactor").textContent = `PF: ${strat.profit_factor}`;
  document.getElementById("cardMonthlyNet").textContent = `+$${strat.monthly_net_1mnq.toFixed(2)}/m`;
  document.getElementById("cardMaxDD").textContent = `-$${strat.max_dd_1mnq.toFixed(0)} (1 MNQ)`;
}

// 3. Canvi d'Horitzó
function setHorizon(years) {
  currentHorizon = years;
  
  // Actualitzar estils de botons
  [1, 5, 10].forEach(y => {
    const btn = document.getElementById(`btnH${y}`);
    if (y === years) {
      btn.className = "px-3 py-1.5 text-xs font-semibold rounded-md bg-emerald-500 text-slate-950 shadow transition font-bold";
    } else {
      btn.className = "px-3 py-1.5 text-xs font-semibold rounded-md text-slate-300 hover:text-white transition";
    }
  });

  const subtitle = document.getElementById("chartSubtitle");
  subtitle.textContent = `Evolució mes a mes de 1.000$ inicials fins a ${years} ${years === 1 ? 'any' : 'anys'}`;

  updateProjections();
}

// 4. Canvi d'Escala Lineal / Log
function toggleScale() {
  isLogScale = !isLogScale;
  const scaleText = document.getElementById("scaleText");
  scaleText.textContent = isLogScale ? "LOG" : "LIN";
  if (chartInstance) {
    chartInstance.options.scales.y.type = isLogScale ? "logarithmic" : "linear";
    chartInstance.update();
  }
}

// 5. Carregar i Renderitzar Gràfica
async function updateProjections() {
  try {
    const res = await fetch(`/api/projections?strategy=${currentStrategy}&horizon=${currentHorizon}&balance=${liveBalance}`);
    const data = await res.json();
    renderChart(data);
  } catch (err) {
    console.error("Error carregant projeccions:", err);
  }
}

function renderChart(data) {
  const ctx = document.getElementById("projectionChart").getContext("2d");
  const sc = data.scenarios;
  const labels = data.labels;

  // Dataset per al punt actual
  const actualPointData = new Array(labels.length).fill(null);
  actualPointData[0] = liveBalance;

  const datasets = [
    {
      label: sc.income.name,
      data: sc.income.balance,
      borderColor: sc.income.color,
      backgroundColor: "rgba(16, 185, 129, 0.05)",
      borderWidth: 2.5,
      tension: 0.25,
      fill: false,
      pointRadius: currentHorizon === 1 ? 4 : 0,
      pointHoverRadius: 6
    },
    {
      label: sc.compounded.name,
      data: sc.compounded.balance,
      borderColor: sc.compounded.color,
      backgroundColor: "transparent",
      borderWidth: 2,
      borderDash: [5, 4],
      tension: 0.25,
      fill: false,
      pointRadius: currentHorizon === 1 ? 4 : 0,
      pointHoverRadius: 6
    },
    {
      label: sc.realistic_decay.name,
      data: sc.realistic_decay.balance,
      borderColor: sc.realistic_decay.color,
      backgroundColor: "transparent",
      borderWidth: 1.8,
      tension: 0.25,
      fill: false,
      pointRadius: currentHorizon === 1 ? 3 : 0,
      pointHoverRadius: 5
    },
    {
      label: sc.conservative.name,
      data: sc.conservative.balance,
      borderColor: sc.conservative.color,
      backgroundColor: "transparent",
      borderWidth: 1.8,
      tension: 0.25,
      fill: false,
      pointRadius: currentHorizon === 1 ? 3 : 0,
      pointHoverRadius: 5
    },
    {
      label: "📍 Saldo Actual a Tradovate",
      data: actualPointData,
      borderColor: "#f43f5e",
      backgroundColor: "#f43f5e",
      pointBackgroundColor: "#f43f5e",
      pointBorderColor: "#fff",
      pointBorderWidth: 2,
      pointRadius: 7,
      pointHoverRadius: 9,
      showLine: false
    }
  ];

  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#94a3b8",
            font: { size: 11, weight: "600" },
            boxWidth: 12,
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: "rgba(14, 21, 38, 0.95)",
          borderColor: "#1e293b",
          borderWidth: 1,
          titleColor: "#fff",
          bodyColor: "#cbd5e1",
          padding: 12,
          callbacks: {
            label: function (context) {
              const val = context.raw;
              if (val === null || val === undefined) return null;
              return `${context.dataset.label}: $${val.toLocaleString('en-US', {maximumFractionDigits: 0})}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(30, 41, 59, 0.4)" },
          ticks: { color: "#64748b", font: { size: 10 } }
        },
        y: {
          type: isLogScale ? "logarithmic" : "linear",
          grid: { color: "rgba(30, 41, 59, 0.4)" },
          ticks: {
            color: "#64748b",
            font: { size: 10, family: "monospace" },
            callback: function (val) {
              if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
              if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
              return `$${val}`;
            }
          }
        }
      }
    }
  });
}

// 6. Carregar Consell de Retirada
async function loadWithdrawalAdvice(balance) {
  try {
    const res = await fetch(`/api/withdrawal-advice?balance=${balance}`);
    const data = await res.json();

    document.getElementById("adviseAmount").textContent = `$${data.recommended_monthly_withdrawal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("adviseMessage").innerHTML = data.message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    const badge = document.getElementById("badgePhase");
    badge.textContent = data.phase;

    // Canvi de color de badge
    if (data.phase_color === "amber") {
      badge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30";
    } else if (data.phase_color === "blue") {
      badge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30";
    } else if (data.phase_color === "emerald") {
      badge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    } else {
      badge.className = "text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/30";
    }

    // Matalàs
    document.getElementById("cardCushion").textContent = `${data.drawdown_cushion_multiples}x`;

  } catch (err) {
    console.error("Error consell retirada:", err);
  }
}
