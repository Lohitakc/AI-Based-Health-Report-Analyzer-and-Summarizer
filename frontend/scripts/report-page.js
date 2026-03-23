const emptyState = document.getElementById("emptyState");
const reportContent = document.getElementById("reportContent");

const resultRows = document.getElementById("resultRows");
const statsGrid = document.getElementById("statsGrid");
const patientView = document.getElementById("patientView");
const doctorView = document.getElementById("doctorView");
const disclaimerText = document.getElementById("disclaimerText");
const downloadPdfButton = document.getElementById("downloadPdfButton");
const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
const tabPanes = Array.from(document.querySelectorAll(".tab-pane"));

const storedResult =
  sessionStorage.getItem("analysis_result") || localStorage.getItem("analysis_result");
const storedName =
  sessionStorage.getItem("analysis_file_name") ||
  localStorage.getItem("analysis_file_name") ||
  "Pathology_Report";
let latestResult = null;

const EXPLANATION_MAP = {
  Hemoglobin: "Can affect oxygen delivery and may relate to anemia when low.",
  RBC: "Reflects red blood cells that carry oxygen through the body.",
  WBC: "Can change during infection or immune response.",
  Platelets: "Platelets help blood clot and prevent bleeding.",
  MCV: "Shows average red blood cell size.",
  MCH: "Shows average hemoglobin amount in red blood cells.",
  Neutrophils: "Often rises with bacterial infection patterns.",
  Lymphocytes: "Often changes with viral or immune response patterns.",
  "Fasting Glucose": "Indicates blood sugar control after fasting.",
  "Postprandial Glucose": "Shows blood sugar trend after meals.",
  "Random Glucose": "Quick indicator of blood glucose status.",
  Creatinine: "Strong marker of kidney filtration performance.",
  "Urea / BUN": "May rise with dehydration or kidney stress.",
  Cholesterol: "Higher levels increase long-term heart risk.",
  LDL: "Higher LDL can increase plaque buildup risk.",
  HDL: "Lower HDL reduces cardiovascular protection.",
  Triglycerides: "Higher triglycerides can increase metabolic risk.",
  TSH: "Key regulator used for thyroid assessment.",
  T3: "Thyroid hormone linked to metabolism and energy balance.",
  T4: "Thyroid hormone used with TSH for thyroid status.",
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeStatusClass(status) {
  if (!status) return "";
  return `status-${status.toLowerCase()}`;
}

function statusPill(status) {
  return `<span class="status-pill ${normalizeStatusClass(status)}">${escapeHtml(status)}</span>`;
}

function activateTab(tabId) {
  tabButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.tabTarget === tabId);
  });
  tabPanes.forEach((pane) => {
    pane.classList.toggle("active", pane.id === tabId);
  });
}

tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tabTarget));
});

function showEmptyState() {
  emptyState.classList.remove("hidden");
  reportContent.classList.add("hidden");
  downloadPdfButton.disabled = true;
}

function showReport() {
  emptyState.classList.add("hidden");
  reportContent.classList.remove("hidden");
  downloadPdfButton.disabled = false;
}

function renderStats(table) {
  const total = table.length;
  const normal = table.filter((row) => row.status === "NORMAL").length;
  const abnormal = table.filter((row) => row.status !== "NORMAL").length;
  const critical = table.filter((row) => row.status === "CRITICAL").length;

  const stats = [
    { label: "Parameters", value: total, className: "" },
    { label: "Normal", value: normal, className: "normal-value" },
    { label: "Abnormal", value: abnormal, className: "abnormal-value" },
    { label: "Critical", value: critical, className: "critical-value" },
  ];

  statsGrid.innerHTML = stats
    .map(
      (item) => `
      <article class="stat-card">
        <div class="stat-label">${escapeHtml(item.label)}</div>
        <div class="stat-value ${item.className}">${escapeHtml(item.value)}</div>
      </article>
    `
    )
    .join("");
}

function renderAnalysisTable(table) {
  resultRows.innerHTML = "";
  table.forEach((row) => {
    const tr = document.createElement("tr");
    const valueLabel = row.unit ? `${row.value} ${row.unit}` : `${row.value}`;
    tr.innerHTML = `
      <td class="parameter-cell">${escapeHtml(row.parameter)}</td>
      <td class="value-main">${escapeHtml(valueLabel)}</td>
      <td>${escapeHtml(row.range)}</td>
      <td>${statusPill(row.status)}</td>
      <td>${escapeHtml(row.range_source || "Unknown source")}</td>
    `;
    resultRows.appendChild(tr);
  });
}

function getActionItems(text) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line);

  const numbered = lines
    .filter((line) => /^\d+\.\s+/.test(line))
    .map((line) => line.replace(/^\d+\.\s+/, ""));

  if (numbered.length > 0) return numbered;

  return [
    "Keep hydration, balanced meals, and regular sleep.",
    "Reduce sugar-rich and ultra-processed food intake where relevant.",
    "Avoid smoking and alcohol excess.",
    "Repeat tests or seek review if symptoms persist.",
  ];
}

function getClinicalNotes(text) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => line.slice(2));

  if (lines.length > 0) return lines;

  return [
    "Prioritize follow-up for CRITICAL values, then HIGH/LOW values.",
    "Integrate with symptoms, medications, and prior baseline reports.",
  ];
}

function renderPatientView(data) {
  const table = data.table || [];
  const abnormalRows = table.filter((row) => row.status !== "NORMAL");
  const actions = getActionItems(data.patient_summary);
  const referenceSources = Array.from(
    new Set(
      table
        .map((row) => row.range_source)
        .filter((source) => source && source.toLowerCase() !== "report reference range")
    )
  );

  const findingsHTML =
    abnormalRows.length === 0
      ? `<article class="finding-card"><div class="finding-title">No abnormal values were detected in extracted parameters.</div></article>`
      : abnormalRows
          .map((row) => {
            const valueLabel = row.unit ? `${row.value} ${row.unit}` : `${row.value}`;
            const note =
              EXPLANATION_MAP[row.parameter] ||
              "This value should be interpreted in clinical context with your doctor.";
            return `
              <article class="finding-card">
                <div class="finding-line">
                  ${statusPill(row.status)}
                  <div class="finding-title">${escapeHtml(row.parameter)} - ${escapeHtml(valueLabel)}</div>
                </div>
                <div class="finding-note">${escapeHtml(note)}</div>
                <div class="finding-meta">Ref: ${escapeHtml(row.range)} · Source: ${escapeHtml(
              row.range_source || "Unknown source"
            )}</div>
              </article>
            `;
          })
          .join("");

  const actionsHTML = actions
    .map(
      (item, index) => `
      <div class="advice-item">
        <span class="advice-index">${index + 1}</span>
        <span>${escapeHtml(item)}</span>
      </div>
    `
    )
    .join("");

  const referencesHTML =
    referenceSources.length === 0
      ? `<span class="ref-chip">Report reference range</span>`
      : referenceSources.map((source) => `<span class="ref-chip">${escapeHtml(source)}</span>`).join("");

  patientView.innerHTML = `
    <div class="summary-alert">${escapeHtml(
      `${abnormalRows.length} parameter(s) are outside the reference range. Please review findings below and consult your physician.`
    )}</div>

    <h3 class="patient-heading">Key Findings</h3>
    ${findingsHTML}

    <h3 class="actions-heading">What You Can Do</h3>
    ${actionsHTML}

    <div class="ref-strip">
      Trusted References:
      ${referencesHTML}
    </div>
  `;
}

function renderDoctorView(data) {
  const table = data.table || [];
  const abnormalRows = table.filter((row) => row.status !== "NORMAL");
  const reportType = data.report_type || "Unknown";
  const clinicalNotes = getClinicalNotes(data.doctor_summary);

  const findingsHTML =
    abnormalRows.length === 0
      ? `<li><span>No major abnormal extracted parameters.</span></li>`
      : abnormalRows
          .map((row) => {
            const valueLabel = row.unit ? `${row.value} ${row.unit}` : `${row.value}`;
            return `
              <li>
                <span>
                  <strong>${escapeHtml(row.parameter)}</strong>
                  &nbsp; ${escapeHtml(valueLabel)} · Ref: ${escapeHtml(row.range)}
                </span>
                ${statusPill(row.status)}
              </li>
            `;
          })
          .join("");

  const notesHTML = clinicalNotes.map((note) => `<li>${escapeHtml(note)}</li>`).join("");

  doctorView.innerHTML = `
    <article class="doctor-block">
      <div class="doctor-label">Report Type</div>
      <div class="doctor-main">${escapeHtml(reportType)}</div>
    </article>

    <article class="doctor-block">
      <div class="doctor-label">Abnormal Findings</div>
      <ul class="doctor-list">${findingsHTML}</ul>
    </article>

    <article class="doctor-block">
      <div class="doctor-label">Clinical Notes</div>
      <ul class="doctor-note-list">${notesHTML}</ul>
    </article>
  `;
}

function renderDisclaimer(disclaimer) {
  disclaimerText.innerHTML = `<strong>Disclaimer:</strong> ${escapeHtml(disclaimer)}`;
}

function renderReport(data) {
  latestResult = data;
  const table = data.table || [];
  renderStats(table);
  renderAnalysisTable(table);
  renderPatientView(data);
  renderDoctorView(data);
  renderDisclaimer(data.disclaimer || "This is not a medical diagnosis. Consult a doctor.");
  activateTab("analysisTab");
  showReport();
}

async function downloadReportPDF() {
  if (!latestResult) return;

  downloadPdfButton.disabled = true;
  const originalLabel = downloadPdfButton.textContent;
  downloadPdfButton.textContent = "Preparing PDF...";

  try {
    const payload = {
      report_name: storedName,
      table: latestResult.table || [],
      patient_summary: latestResult.patient_summary || "",
      doctor_summary: latestResult.doctor_summary || "",
      disclaimer: latestResult.disclaimer || "",
    };

    const response = await fetch("/download-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || "PDF generation failed.");
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `${storedName || "Pathology_Report"}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    downloadPdfButton.disabled = false;
    downloadPdfButton.textContent = originalLabel;
  }
}

downloadPdfButton.addEventListener("click", downloadReportPDF);

if (!storedResult) {
  showEmptyState();
} else {
  try {
    renderReport(JSON.parse(storedResult));
  } catch {
    showEmptyState();
  }
}
