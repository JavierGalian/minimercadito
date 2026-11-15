import { getSalesHistory } from "../services/api.js";
import { formatCurrency } from "../services/format.js";

const PAGE_SIZE = 20;

const dateTimeFormatter = new Intl.DateTimeFormat("es-AR", {
  dateStyle: "short",
  timeStyle: "medium",
});

export function createSalesHistory({ container, onError }) {
  container.innerHTML = `
    <section class="panel sales-history-panel" aria-labelledby="sales-history-title">
      <div class="panel-heading">
        <div>
          <p class="section-kicker">OPERACIONES REGISTRADAS</p>
          <h2 id="sales-history-title">Historial de ventas</h2>
        </div>
        <button class="secondary-button" id="sales-history-refresh" type="button">
          Actualizar
        </button>
      </div>
      <p class="history-feedback" id="sales-history-feedback" role="status" aria-live="polite">
        Cargando ventas…
      </p>
      <div class="sales-history-table-wrap" id="sales-history-table-wrap"></div>
      <div class="history-pagination" aria-label="Paginación del historial">
        <button class="secondary-button" id="sales-history-previous" type="button">
          Anterior
        </button>
        <span id="sales-history-page">Página 1</span>
        <button class="secondary-button" id="sales-history-next" type="button">
          Siguiente
        </button>
      </div>
    </section>
  `;

  const feedback = container.querySelector("#sales-history-feedback");
  const tableWrap = container.querySelector("#sales-history-table-wrap");
  const pageLabel = container.querySelector("#sales-history-page");
  const previousButton = container.querySelector("#sales-history-previous");
  const nextButton = container.querySelector("#sales-history-next");
  const refreshButton = container.querySelector("#sales-history-refresh");
  let sales = [];
  let offset = 0;
  let hasMore = false;
  let isLoading = false;

  function renderSales() {
    tableWrap.replaceChildren();
    if (sales.length === 0) {
      const empty = document.createElement("p");
      empty.className = "inventory-empty";
      empty.textContent = "No hay ventas registradas en esta página.";
      tableWrap.append(empty);
      return;
    }

    const table = document.createElement("table");
    table.className = "sales-history-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th scope="col">Fecha y hora</th>
          <th scope="col">Cajero</th>
          <th scope="col">Productos</th>
          <th scope="col">Total</th>
        </tr>
      </thead>
    `;
    const body = document.createElement("tbody");

    for (const sale of sales) {
      const row = document.createElement("tr");
      const dateCell = document.createElement("td");
      const saleDate = new Date(sale.fecha);
      dateCell.textContent = Number.isNaN(saleDate.getTime())
        ? sale.fecha
        : dateTimeFormatter.format(saleDate);

      const cashierCell = document.createElement("td");
      cashierCell.textContent = sale.cajero || "No registrado";

      const detailsCell = document.createElement("td");
      const detailsList = document.createElement("ul");
      detailsList.className = "sales-line-items";
      for (const detail of sale.detalles) {
        const detailRow = document.createElement("li");
        const description = document.createElement("span");
        description.textContent =
          `${detail.cantidad} × ${detail.nombre_producto}`;
        const subtotal = document.createElement("strong");
        subtotal.textContent = formatCurrency(detail.subtotal);
        detailRow.append(description, subtotal);
        detailsList.append(detailRow);
      }
      detailsCell.append(detailsList);

      const totalCell = document.createElement("td");
      totalCell.className = "sales-history-total";
      totalCell.textContent = formatCurrency(sale.total);

      row.append(dateCell, cashierCell, detailsCell, totalCell);
      body.append(row);
    }

    table.append(body);
    tableWrap.append(table);
  }

  function updateControls() {
    pageLabel.textContent = `Página ${Math.floor(offset / PAGE_SIZE) + 1}`;
    previousButton.disabled = isLoading || offset === 0;
    nextButton.disabled = isLoading || !hasMore;
    refreshButton.disabled = isLoading;
    feedback.textContent = isLoading ? "Cargando ventas…" : "";
    feedback.hidden = !isLoading;
  }

  async function load(nextOffset = offset) {
    if (isLoading) return;
    isLoading = true;
    updateControls();
    try {
      const result = await getSalesHistory(PAGE_SIZE + 1, nextOffset);
      offset = nextOffset;
      hasMore = result.length > PAGE_SIZE;
      sales = result.slice(0, PAGE_SIZE);
      renderSales();
      if (sales.length === 0) {
        feedback.textContent = "No hay ventas registradas.";
        feedback.hidden = false;
      }
    } catch (error) {
      onError(error);
      feedback.textContent = error.message;
      feedback.hidden = false;
    } finally {
      isLoading = false;
      updateControls();
    }
  }

  previousButton.addEventListener("click", () => {
    void load(Math.max(0, offset - PAGE_SIZE));
  });
  nextButton.addEventListener("click", () => {
    if (hasMore) void load(offset + PAGE_SIZE);
  });
  refreshButton.addEventListener("click", () => {
    void load(offset);
  });

  return { load: () => load(0) };
}
