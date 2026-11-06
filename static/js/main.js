// main.js - sidebar toggle and client-side form validation.
document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebarToggle");
  if (toggle) toggle.addEventListener("click", () => sidebar.classList.toggle("open"));

  // Assessment form validation
  const form = document.getElementById("assessForm");
  if (!form) return;

  form.querySelectorAll("input[type=number]").forEach((input) => {
    input.addEventListener("input", () => validateField(input));
  });

  form.addEventListener("submit", (event) => {
    let valid = true;
    form.querySelectorAll("input[type=number]").forEach((input) => {
      if (!validateField(input)) valid = false;
    });
    if (!valid) {
      event.preventDefault();
      const firstInvalid = form.querySelector(".is-invalid");
      if (firstInvalid) firstInvalid.focus();
    }
  });

  document.getElementById("resetBtn").addEventListener("click", () => {
    form.querySelectorAll(".is-invalid, .is-valid").forEach((el) => el.classList.remove("is-invalid", "is-valid"));
  });

  // Checks one field and writes a clear message into its feedback box.
  function validateField(input) {
    const feedback = input.parentElement.querySelector(".invalid-feedback");
    const label = input.dataset.label;
    const min = Number(input.min), max = Number(input.max);
    const raw = input.value.trim();
    let message = "";

    if (raw === "") message = `${label} is required.`;
    else if (Number.isNaN(Number(raw))) message = `${label} must be a number.`;
    else if (input.step === "1" && !Number.isInteger(Number(raw))) message = `${label} must be a whole number.`;
    else if (Number(raw) < min || Number(raw) > max) message = `${label} must be between ${min} and ${max} ${input.dataset.unit}.`;

    input.classList.toggle("is-invalid", message !== "");
    input.classList.toggle("is-valid", message === "");
    if (feedback && message) feedback.textContent = message;
    return message === "";
  }
});
