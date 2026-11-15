import {
  getAnnualSalesReport,
  getMonthlySalesReport,
} from "../services/api.js";
import { formatCurrency } from "../services/format.js";

const monthFormatter = new Intl.DateTimeFormat("es-AR", {
  month: "long",
  timeZone: "UTC",
});

const monthNames = Array.from({ length: 12 }, (_, index) =>
  monthFormatter.format(new Date(Date.UTC(2026, index, 1))),
);

export function createFinancialReports({ container, onError }) {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  container.innerHTML = `
    <div class="financial-report-layout">
      <section class="panel monthly-report-panel" aria-labelledby="monthly-report-title">
        <div class="panel-heading">
          <div>
            <p class="section-kicker">CONSULTA POR PERIODO</p>
            <h2 id="monthly-report-title">Reporte mensual</h2>
          </div>
          <span class="form-icon" aria-hidden="true">$</span>
        </div>
        <form class="report-filter-form" id="monthly-report-form">
          <label class="report-field">
            <span class="field-label">Año</span>
            <input
              class="text-input"
              name="anio"
              type="number"
              min="1"
              max="9998"
              value="${currentYear}"
              required
            />
          </label>
          <label class="report-field">
            <span class="field-label">Mes</span>
            <select class="text-input" name="mes" required>
              ${monthNames
                .map(
                  (name, index) =>
                    `<option value="${index + 1}" ${
                      index + 1 === currentMonth ? "selected" : ""
                    }>${name}</option>`,
                )
                .join("")}
            </select>
          </label>
          <button class="primary-button report-submit" type="submit">
            Consultar mes
          </button>
        </form>
        <div class="report-result" id="monthly-report-result" aria-live="polite"></div>
      </section>

      <section class="panel annual-report-panel" aria-labelledby="annual-report-title">
        <div class="panel-heading">
          <div>
            <p class="section-kicker">EVOLUCIÓN ANUAL</p>
            <h2 id="annual-report-title">Reporte anual</h2>
          </div>
        </div>
        <form class="report-filter-form annual-filter-form" id="annual-report-form">
          <label class="report-field">
            <span class="field-label">Año</span>
            <input
              class="text-input"
              name="anio"
              type="number"
              min="1"
              max="9998"
              value="${currentYear}"
              required
            />
          </label>
          <button class="primary-button report-submit" type="submit">
            Consultar año
          </button>
        </form>
        <div class="report-result" id="annual-report-result" aria-live="polite"></div>
      </section>
    </div>
  `;

  const monthlyForm = container.querySelector("#monthly-report-form");
  const annualForm = container.querySelector("#annual-report-form");
  const monthlyResult = container.querySelector("#monthly-report-result");
  const annualResult = container.querySelector("#annual-report-result");
  const monthlySubmit = monthlyForm.querySelector('button[type="submit"]');
  const annualSubmit = annualForm.querySelector('button[type="submit"]');
  let monthlyLoading = false;
  let annualLoading = false;

  function renderMonthlyReport(report) {
    monthlyResult.replaceChildren();
    const summary = document.createElement("div");
    summary.className = "report-summary-card";
    const period = document.createElement("p");
    period.className = "report-period";
    period.textContent = `${monthNames[report.mes - 1]} ${report.anio}`;
    const label = document.createElement("span");
    label.textContent = "Recaudación total";
    const total = document.createElement("strong");
    total.textContent = formatCurrency(report.total);
    const count = document.createElement("p");
    count.textContent = `${report.cantidad_ventas} ${
      report.cantidad_ventas === 1 ? "venta registrada" : "ventas registradas"
    }`;
    summary.append(period, label, total, count);
    monthlyResult.append(summary);
  }

  function decimalToCents(value) {
    const [units, fraction = ""] = String(value).split(".");
    return Number(units) * 100 + Number(fraction.padEnd(2, "0").slice(0, 2));
  }

  function renderAnnualReport(report) {
    annualResult.replaceChildren();
    const totalCents = report.meses.reduce(
      (sum, month) => sum + decimalToCents(month.total),
      0,
    );
    const salesCount = report.meses.reduce(
      (sum, month) => sum + month.cantidad_ventas,
      0,
    );

    const summary = document.createElement("div");
    summary.className = "report-summary-card report-summary-annual";
    const period = document.createElement("p");
    period.className = "report-period";
    period.textContent = `Año ${report.anio}`;
    const label = document.createElement("span");
    label.textContent = "Recaudación total";
    const total = document.createElement("strong");
    total.textContent = formatCurrency(totalCents / 100);
    const count = document.createElement("p");
    count.textContent = `${salesCount} ${
      salesCount === 1 ? "venta registrada" : "ventas registradas"
    }`;
    summary.append(period, label, total, count);
    annualResult.append(summary);

    const maxTotal = Math.max(
      ...report.meses.map((month) => decimalToCents(month.total)),
    );
    const chart = document.createElement("div");
    chart.className = "annual-report-chart";
    chart.setAttribute("aria-label", `Recaudación por mes en ${report.anio}`);

    for (const month of report.meses) {
      const row = document.createElement("div");
      row.className = "annual-report-month";
      const name = document.createElement("span");
      name.className = "annual-report-month-name";
      name.textContent = monthNames[month.mes - 1];

      const track = document.createElement("div");
      track.className = "annual-report-bar-track";
      const bar = document.createElement("span");
      bar.className = "annual-report-bar";
      const amountCents = decimalToCents(month.total);
      bar.style.width = maxTotal > 0 ? `${(amountCents / maxTotal) * 100}%` : "0%";
      track.append(bar);

      const value = document.createElement("strong");
      value.className = "annual-report-value";
      value.textContent = formatCurrency(month.total);
      row.append(name, track, value);
      chart.append(row);
    }

    annualResult.append(chart);
  }

  async function submitMonthlyReport(year, month) {
    if (monthlyLoading) return;
    monthlyLoading = true;
    monthlySubmit.disabled = true;
    monthlySubmit.textContent = "Consultando…";
    monthlyResult.textContent = "Cargando reporte mensual…";
    try {
      renderMonthlyReport(await getMonthlySalesReport(year, month));
    } catch (error) {
      monthlyResult.textContent = error.message;
      onError(error);
    } finally {
      monthlyLoading = false;
      monthlySubmit.disabled = false;
      monthlySubmit.textContent = "Consultar mes";
    }
  }

  async function submitAnnualReport(year) {
    if (annualLoading) return;
    annualLoading = true;
    annualSubmit.disabled = true;
    annualSubmit.textContent = "Consultando…";
    annualResult.textContent = "Cargando reporte anual…";
    try {
      renderAnnualReport(await getAnnualSalesReport(year));
    } catch (error) {
      annualResult.textContent = error.message;
      onError(error);
    } finally {
      annualLoading = false;
      annualSubmit.disabled = false;
      annualSubmit.textContent = "Consultar año";
    }
  }

  monthlyForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!monthlyForm.reportValidity() || monthlySubmit.disabled) return;
    const data = new FormData(monthlyForm);
    void submitMonthlyReport(Number(data.get("anio")), Number(data.get("mes")));
  });

  annualForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!annualForm.reportValidity() || annualSubmit.disabled) return;
    const data = new FormData(annualForm);
    void submitAnnualReport(Number(data.get("anio")));
  });

  return {
    load() {
      const monthlyData = new FormData(monthlyForm);
      const annualData = new FormData(annualForm);
      void submitMonthlyReport(
        Number(monthlyData.get("anio")),
        Number(monthlyData.get("mes")),
      );
      void submitAnnualReport(Number(annualData.get("anio")));
    },
  };
}
