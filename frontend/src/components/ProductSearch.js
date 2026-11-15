import { formatCurrency } from "../services/format.js";

export function createProductSearch({
  container,
  onSelect,
  onBarcodeSubmit,
  onMessage,
}) {
  container.innerHTML = `
    <form class="search-form" role="search">
      <span class="search-icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" fill="none"><circle cx="8.8" cy="8.8" r="5.8" stroke="currentColor" stroke-width="1.7"/><path d="m13.2 13.2 4 4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
      </span>
      <input
        id="product-query"
        type="search"
        placeholder="Escaneá un código o buscá por nombre"
        autocomplete="off"
        aria-label="Buscar productos por nombre o código de barras"
      />
      <kbd>ENTER</kbd>
    </form>
    <div class="results-heading">
      <span>PRODUCTOS DISPONIBLES</span>
      <span class="results-hint">Seleccioná para agregar</span>
    </div>
    <div class="product-results" id="product-results"></div>
  `;

  const form = container.querySelector("form");
  const input = container.querySelector("input");
  const results = container.querySelector("#product-results");
  let products = [];

  function renderResults() {
    const query = input.value.trim().toLocaleLowerCase("es");
    const filtered = products.filter((product) => {
      const name = product.nombre.toLocaleLowerCase("es");
      const barcode = (product.codigo_barras ?? "").toLocaleLowerCase("es");
      return name.includes(query) || barcode.includes(query);
    });
    results.replaceChildren();

    if (filtered.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-search";
      empty.innerHTML = `
        <span class="empty-search-icon" aria-hidden="true">⌕</span>
        <strong>${query ? "No encontramos coincidencias" : "Tu catálogo está vacío"}</strong>
        <span>${query ? "Probá con otro nombre o código de barras." : "Agregá productos desde la pestaña Inventario."}</span>
      `;
      results.append(empty);
      return;
    }

    for (const product of filtered) {
      const card = document.createElement("article");
      card.className = "product-card";

      const info = document.createElement("div");
      info.className = "product-card-info";
      const name = document.createElement("strong");
      name.textContent = product.nombre;
      const code = document.createElement("span");
      code.className = "product-code";
      code.textContent = product.codigo_barras || "Sin código";
      info.append(name, code);

      const details = document.createElement("div");
      details.className = "product-card-details";
      const price = document.createElement("strong");
      price.className = "product-price";
      price.textContent = formatCurrency(product.precio);
      const stock = document.createElement("span");
      stock.className = `product-stock ${
        product.stock_actual === 0 ? "text-danger" : ""
      }`;
      stock.textContent =
        product.stock_actual === 0
          ? "Sin stock"
          : `${product.stock_actual} disponibles`;
      details.append(price, stock);

      const addButton = document.createElement("button");
      addButton.type = "button";
      addButton.className = "add-product-button";
      addButton.disabled = product.stock_actual < 1;
      addButton.setAttribute("aria-label", `Agregar ${product.nombre}`);
      addButton.textContent = "+";
      addButton.addEventListener("click", () => onSelect(product));

      card.append(info, details, addButton);
      results.append(card);
    }
  }

  input.addEventListener("input", renderResults);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const code = input.value.trim();
    if (!code) {
      input.focus();
      return;
    }

    const exactProduct = products.find(
      (product) => product.codigo_barras === code,
    );
    if (exactProduct) {
      onSelect(exactProduct);
      input.value = "";
      renderResults();
      return;
    }

    const nameMatches = products.some((product) =>
      product.nombre.toLocaleLowerCase("es").includes(code.toLocaleLowerCase("es")),
    );
    if (nameMatches) {
      renderResults();
      return;
    }

    await onBarcodeSubmit(code);
    input.value = "";
    renderResults();
  });

  return {
    setProducts(nextProducts) {
      products = nextProducts;
      renderResults();
    },
    focus() {
      input.focus();
    },
  };
}
