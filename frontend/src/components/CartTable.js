import { formatCurrency } from "../services/format.js";

export function createCartTable({
  container,
  onQuantityChange,
  onRemove,
  onCheckout,
}) {
  container.innerHTML = `
    <div class="cart-header">
      <div>
        <p class="section-kicker">RESUMEN</p>
        <h2>Carrito</h2>
      </div>
      <span class="cart-count" id="cart-count">0 artículos</span>
    </div>
    <div class="cart-table-wrap">
      <table class="cart-table">
        <thead>
          <tr>
            <th scope="col">Producto</th>
            <th scope="col">Precio</th>
            <th scope="col">Cant.</th>
            <th scope="col" class="align-right">Subtotal</th>
            <th scope="col"><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody id="cart-items"></tbody>
      </table>
      <div class="cart-empty" id="cart-empty">
        <span class="cart-empty-icon" aria-hidden="true">＋</span>
        <strong>Empezá una venta</strong>
        <span>Los productos que agregues aparecerán acá.</span>
      </div>
    </div>
    <div class="cart-footer">
      <div class="cart-total-row">
        <span>Total a cobrar</span>
        <strong id="cart-total">$ 0,00</strong>
      </div>
      <button class="checkout-button" id="checkout-button" type="button" disabled>
        <span>Finalizar venta</span>
        <span class="checkout-arrow" aria-hidden="true">→</span>
      </button>
      <p class="secure-note"><span aria-hidden="true">●</span> El stock se actualiza al confirmar el cobro</p>
    </div>
  `;

  const body = container.querySelector("#cart-items");
  const empty = container.querySelector("#cart-empty");
  const total = container.querySelector("#cart-total");
  const count = container.querySelector("#cart-count");
  const checkout = container.querySelector("#checkout-button");
  let items = [];
  let busy = false;

  function render() {
    body.replaceChildren();
    const hasItems = items.length > 0;
    empty.hidden = hasItems;
    container.querySelector(".cart-table").hidden = !hasItems;
    count.textContent = `${items.reduce((sum, item) => sum + item.quantity, 0)} ${
      items.reduce((sum, item) => sum + item.quantity, 0) === 1
        ? "artículo"
        : "artículos"
    }`;

    let totalCents = 0;
    for (const { product, quantity } of items) {
      const unitCents = Math.round(Number(product.precio) * 100);
      const subtotalCents = unitCents * quantity;
      totalCents += subtotalCents;
      const row = document.createElement("tr");

      const nameCell = document.createElement("td");
      nameCell.className = "cart-product-name";
      nameCell.textContent = product.nombre;
      const priceCell = document.createElement("td");
      priceCell.textContent = formatCurrency(product.precio);
      const quantityCell = document.createElement("td");
      const quantityInput = document.createElement("input");
      quantityInput.className = "quantity-input";
      quantityInput.type = "number";
      quantityInput.min = "1";
      quantityInput.max = String(product.stock_actual);
      quantityInput.step = "1";
      quantityInput.value = String(quantity);
      const quantityIsInvalid =
        product.stock_actual < 1 || quantity > product.stock_actual;
      quantityInput.classList.toggle("is-invalid", quantityIsInvalid);
      quantityInput.setAttribute("aria-invalid", String(quantityIsInvalid));
      quantityInput.title = quantityIsInvalid
        ? `Stock disponible: ${product.stock_actual}.`
        : "";
      quantityInput.setAttribute(
        "aria-label",
        `Cantidad de ${product.nombre}. Máximo ${product.stock_actual}`,
      );
      quantityInput.addEventListener("input", () => {
        const value = Number(quantityInput.value);
        const valid =
          Number.isInteger(value) &&
          value >= 1 &&
          value <= product.stock_actual;
        quantityInput.classList.toggle("is-invalid", !valid);
        quantityInput.setAttribute("aria-invalid", String(!valid));
        quantityInput.title = valid
          ? ""
          : `Ingresá una cantidad entre 1 y ${product.stock_actual}.`;
      });
      quantityInput.addEventListener("change", () => {
        const value = Number(quantityInput.value);
        if (
          !Number.isInteger(value) ||
          value < 1 ||
          value > product.stock_actual
        ) {
          quantityInput.value = String(quantity);
          quantityInput.classList.remove("is-invalid");
          quantityInput.setAttribute("aria-invalid", "false");
          return;
        }
        onQuantityChange(product.id, value);
      });
      quantityCell.append(quantityInput);

      const subtotalCell = document.createElement("td");
      subtotalCell.className = "align-right subtotal-cell";
      subtotalCell.textContent = formatCurrency(subtotalCents / 100);
      const actionCell = document.createElement("td");
      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "remove-item-button";
      removeButton.textContent = "×";
      removeButton.setAttribute("aria-label", `Quitar ${product.nombre}`);
      removeButton.addEventListener("click", () => onRemove(product.id));
      actionCell.append(removeButton);

      row.append(nameCell, priceCell, quantityCell, subtotalCell, actionCell);
      body.append(row);
    }

    total.textContent = formatCurrency(totalCents / 100);
    const hasInsufficientStock = items.some(
      ({ product, quantity }) => product.stock_actual < quantity,
    );
    checkout.disabled = !hasItems || busy || hasInsufficientStock;
    checkout.querySelector("span:first-child").textContent = busy
      ? "Procesando venta…"
      : "Finalizar venta";
  }

  checkout.addEventListener("click", onCheckout);

  return {
    setItems(nextItems) {
      items = nextItems;
      render();
    },
    setBusy(nextBusy) {
      busy = nextBusy;
      render();
    },
  };
}
