const riskPoints = [
  {
    area: "Somerset Levels",
    lat: 51.06,
    lng: -2.78,
    severity: "red",
    risk: "Inland flooding from heavier winter rainfall"
  },
  {
    area: "East Anglia Coast",
    lat: 52.36,
    lng: 1.62,
    severity: "red",
    risk: "Coastal erosion and sea-level rise"
  },
  {
    area: "Greater London",
    lat: 51.507,
    lng: -0.127,
    severity: "amber",
    risk: "Urban heat stress during longer heatwaves"
  },
  {
    area: "Yorkshire Dales",
    lat: 54.26,
    lng: -2.12,
    severity: "amber",
    risk: "Increased flash flooding and landslip risk"
  },
  {
    area: "Scottish Highlands",
    lat: 57.12,
    lng: -4.71,
    severity: "green",
    risk: "Habitat shifts affecting biodiversity"
  },
  {
    area: "Cornwall",
    lat: 50.45,
    lng: -4.92,
    severity: "amber",
    risk: "Water scarcity pressure in dry summers"
  },
  {
    area: "Belfast Lough",
    lat: 54.67,
    lng: -5.84,
    severity: "green",
    risk: "Saltmarsh ecosystem pressure"
  },
  {
    area: "Cardiff / Severn Estuary",
    lat: 51.48,
    lng: -3.18,
    severity: "red",
    risk: "Tidal flood risk and storm surge exposure"
  }
];

const STORAGE_KEY = "uk-climate-risk-history";

const colourBySeverity = {
  red: "#c0392b",
  amber: "#f39c12",
  green: "#2e7d32"
};

const map = L.map("map").setView([54.2, -2.5], 5.6);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

const markerLayer = L.layerGroup().addTo(map);
const tableBody = document.getElementById("risk-table-body");
const chips = document.querySelectorAll(".chip");
const changeLog = document.getElementById("change-log");
const monitorStatus = document.getElementById("monitor-status");
const runCheckBtn = document.getElementById("run-check-btn");

const markerIcon = (severity) =>
  L.divIcon({
    className: "",
    html: `<div class="marker-dot" style="background:${colourBySeverity[severity]}"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8]
  });

const titleCase = (text) => text[0].toUpperCase() + text.slice(1);
const todayString = () => new Date().toISOString().slice(0, 10);

const loadHistory = () => {
  const fallback = { snapshots: [] };

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return fallback;
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.snapshots) ? parsed : fallback;
  } catch {
    return fallback;
  }
};

const saveHistory = (history) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
};

const byArea = (points) =>
  points.reduce((acc, point) => {
    acc[point.area] = point;
    return acc;
  }, {});

const compareSnapshots = (previous, current) => {
  if (!previous) {
    return ["Baseline created. Future daily checks will show differences."];
  }

  const previousByArea = byArea(previous.points);
  const currentByArea = byArea(current.points);
  const changes = [];

  current.points.forEach((point) => {
    const previousPoint = previousByArea[point.area];

    if (!previousPoint) {
      changes.push(`${point.area}: New tracked area (${titleCase(point.severity)}).`);
      return;
    }

    if (previousPoint.severity !== point.severity) {
      changes.push(
        `${point.area}: Severity changed ${titleCase(previousPoint.severity)} → ${titleCase(point.severity)}.`
      );
    }

    if (previousPoint.risk !== point.risk) {
      changes.push(`${point.area}: Risk updated to "${point.risk}".`);
    }
  });

  previous.points.forEach((point) => {
    if (!currentByArea[point.area]) {
      changes.push(`${point.area}: Removed from tracking.`);
    }
  });

  return changes.length ? changes : ["No changes compared with the previous daily snapshot."];
};

const renderChanges = (changes) => {
  changeLog.innerHTML = "";

  changes.forEach((change) => {
    const li = document.createElement("li");
    li.textContent = change;
    changeLog.appendChild(li);
  });
};

const runDailyCheck = () => {
  const history = loadHistory();
  const today = todayString();
  const lastSnapshot = history.snapshots.at(-1) || null;

  if (lastSnapshot && lastSnapshot.date === today) {
    monitorStatus.textContent = `Daily check already run for ${today}.`;
    renderChanges(lastSnapshot.changes || ["No changes recorded for today."]);
    return;
  }

  const currentSnapshot = {
    date: today,
    points: riskPoints,
    changes: compareSnapshots(lastSnapshot, { points: riskPoints })
  };

  history.snapshots.push(currentSnapshot);
  saveHistory(history);

  monitorStatus.textContent = `Daily check saved for ${today}.`;
  renderChanges(currentSnapshot.changes);
};

const drawLegend = () => {
  const legend = L.control({ position: "bottomright" });

  legend.onAdd = () => {
    const div = L.DomUtil.create("div", "legend");

    div.innerHTML = `
      <strong>Severity</strong>
      <div class="legend-item"><span class="swatch" style="background:${colourBySeverity.red}"></span>Red - High concern</div>
      <div class="legend-item"><span class="swatch" style="background:${colourBySeverity.amber}"></span>Amber - Moderate concern</div>
      <div class="legend-item"><span class="swatch" style="background:${colourBySeverity.green}"></span>Green - Lower concern</div>
    `;

    return div;
  };

  legend.addTo(map);
};

const render = (filter = "all") => {
  markerLayer.clearLayers();
  tableBody.innerHTML = "";

  const visible =
    filter === "all"
      ? riskPoints
      : riskPoints.filter((point) => point.severity === filter);

  visible.forEach((point) => {
    const marker = L.marker([point.lat, point.lng], {
      icon: markerIcon(point.severity)
    });

    marker.bindPopup(`
      <strong>${point.area}</strong><br />
      Severity: ${titleCase(point.severity)}<br />
      Risk: ${point.risk}
    `);

    markerLayer.addLayer(marker);

    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${point.area}</td>
      <td><span class="badge ${point.severity}">${point.severity}</span></td>
      <td>${point.risk}</td>
    `;

    tableBody.appendChild(row);
  });
};

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    render(chip.dataset.filter);
  });
});

runCheckBtn.addEventListener("click", runDailyCheck);

drawLegend();
render();
runDailyCheck();
