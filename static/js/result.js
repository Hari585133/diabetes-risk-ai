// result.js - probability gauge and comparison bar chart (Chart.js).
(function () {
  const data = JSON.parse(document.getElementById("result-data").textContent);
  const color = data.predicted_class === 1 ? "#dc2626" : "#16a34a";

  new Chart(document.getElementById("gaugeChart"), {
    type: "doughnut",
    data: {
      labels: ["Model score", "Remainder"],
      datasets: [{ data: [data.probability, 100 - data.probability],
                   backgroundColor: [color, "#e2e8f0"], borderWidth: 0 }],
    },
    options: {
      rotation: -90, circumference: 180, cutout: "72%", aspectRatio: 2,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    },
  });

  const compare = document.getElementById("compareChart");
  if (!compare) return;
  new Chart(compare, {
    data: {
      labels: data.labels,
      datasets: [
        { type: "bar", label: "Your value (% of training median)", data: data.percent,
          backgroundColor: "#0f766e", borderRadius: 6 },
        { type: "line", label: "Training median (100%)", data: data.labels.map(() => 100),
          borderColor: "#2563eb", borderDash: [6, 4], pointRadius: 0, borderWidth: 2 },
      ],
    },
    options: {
      indexAxis: "x", responsive: true, maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, title: { display: true, text: "% of median" } } },
      plugins: { legend: { position: "bottom" } },
    },
  });
})();
