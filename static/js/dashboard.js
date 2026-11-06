// dashboard.js - loads statistics from /api/dashboard-data and draws the charts.
(async function () {
  let data;
  try {
    const response = await fetch("/api/dashboard-data");
    if (!response.ok) throw new Error("Request failed");
    data = await response.json();
  } catch (error) {
    document.getElementById("emptyState").classList.remove("d-none");
    document.getElementById("emptyState").textContent = "Could not load dashboard data.";
    return;
  }
  if (data.total === 0) return;               // the template already shows the empty state

  document.getElementById("statTotal").textContent = data.total;
  document.getElementById("statClass1").textContent = `${data.class1} (${Math.round(data.class1 / data.total * 100)}%)`;
  document.getElementById("statAvg").textContent = data.average_probability + "%";
  document.getElementById("statLatest").textContent = data.latest;

  const C0 = "#16a34a", C1 = "#dc2626";
  const stacked = (id, block) => new Chart(document.getElementById(id), {
    type: "bar",
    data: { labels: block.labels, datasets: [
      { label: "Class 0", data: block.class0, backgroundColor: C0, borderRadius: 4 },
      { label: "Class 1", data: block.class1, backgroundColor: C1, borderRadius: 4 } ] },
    options: { responsive: true, maintainAspectRatio: false,
      scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
      plugins: { legend: { position: "bottom" } } },
  });

  new Chart(document.getElementById("classChart"), {
    type: "doughnut",
    data: { labels: ["Class 0", "Class 1"], datasets: [{ data: [data.class0, data.class1], backgroundColor: [C0, C1] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });
  new Chart(document.getElementById("bandChart"), {
    type: "bar",
    data: { labels: ["Low", "Moderate", "High"],
      datasets: [{ label: "Predictions", data: [data.bands.Low, data.bands.Moderate, data.bands.High],
        backgroundColor: ["#16a34a", "#d97706", "#dc2626"], borderRadius: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
  stacked("ageChart", data.age);
  stacked("glucoseChart", data.glucose);
  stacked("bmiChart", data.bmi);

  const fmt = (v) => (v === null ? "n/a" : v);
  document.getElementById("glucoseAvg").textContent =
    `Average glucose - Class 0: ${fmt(data.average_glucose.class0)} | Class 1: ${fmt(data.average_glucose.class1)}`;
  document.getElementById("bmiAvg").textContent =
    `Average BMI - Class 0: ${fmt(data.average_bmi.class0)} | Class 1: ${fmt(data.average_bmi.class1)}`;
})();
