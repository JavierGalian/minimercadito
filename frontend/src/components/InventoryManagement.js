import { formatCurrency } from "../services/format.js";

const dateFormatter = new Intl.DateTimeFormat("es-AR", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "No disponible" : dateFormatter.format(date);
}

function stockDescription(stock) {
  if (stock === 0) return "Sin stock";
  return `${stock} ${stock === 1 ? "unidad" : "unidades"}`;
}

function createButton(label, className, action, product) {
  const button = document.createElement("button");
  button.className = className;
  button.type = "button";
  button.dataset.action = action;
  button.dataset.productId = String(product.id);
  button.textContent = label;
  return button;
}

export function createInventoryManagement({
  container,
  getCurrentRole,
  onSaveProduct,
  onDeactivateProduct,
  onNotice,
}) {
  container.innerHTML = `
    <div class="inventory-toolbar">
      <label class="sr-only" for="inventory-filter-text">Buscar producto</label>
      <input
        class="text-input"
        id="inventory-filter-text"
        type="search"
        placeholder="Buscar por nombre o código"
        autocomplete="off"
      />
      <label class="sr-only" for="inventory-stock-filter">Filtrar por stock</label>
      <select class="text-input" id="inventory-stock-filter">
        <option value="all">Todos los niveles</option>
        <option value="low">Stock bajo (5 o menos)</option>
        <option value="empty">Sin stock</option>
      </select>
    </div>
    <p class="inventory-feedback" id="inventory-feedback" role="status" aria-live="polite">
      Cargando inventario…
    </p>
    <div class="inventory-table-wrap">
      <table class="inventory-table">
        <thead>
          <tr>
            <th scope="col">Producto</th>
            <th scope="col">Precio</th>
            <th scope="col">Stock</th>
            <th scope="col">Registrado</th>
            <th scope="col"><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody id="inventory-table-body"></tbody>
      </table>
    </div>
  `;

  const queryInput = container.querySelector("#inventory-filter-text");
  const stockFilter = container.querySelector("#inventory-stock-filter");
  const feedback = container.querySelector("#inventory-feedback");
  const tableBody = container.querySelector("#inventory-table-body");
  let products = [];
  let isLoading = false;
  let errorMessage = "";
  let editingProductId = null;
  let busyProductId = null;

  function setFeedback(message, isError = false) {
    feedback.textContent = message;
    feedback.classList.toggle("is-error", isError);
    feedback.hidden = !message;
  }

  function getFilteredProducts() {
    const query = queryInput.value.trim().toLocaleLowerCase("es");
    const filter = stockFilter.value;
    return products.filter((product) => {
      const matchesQuery =
        !query ||
        product.nombre.toLocaleLowerCase("es").includes(query) ||
        (product.codigo_barras || "").toLocaleLowerCase("es").includes(query);
      const matchesStock =
        filter === "all" ||
        (filter === "low" && product.stock_actual > 0 && product.stock_actual <= 5) ||
        (filter === "empty" && product.stock_actual === 0);
      return matchesQuery && matchesStock;
    });
  }

  function renderRow(product) {
    const row = document.createElement("tr");
    const isEditing = editingProductId === product.id;
    const isBusy = busyProductId === product.id;

    const productCell = document.createElement("th");
    productCell.scope = "row";
    const productName = document.createElement("strong");
    productName.className = "inventory-table-name";
    productName.textContent = product.nombre;
    const productDetails = document.createElement("span");
    productDetails.className = "inventory-table-details";
    productDetails.textContent = product.codigo_barras || "Sin código de barras";
    productCell.append(productName, productDetails);

    const priceCell = document.createElement("td");
    if (isEditing) {
      const priceInput = document.createElement("input");
      priceInput.className = "text-input inventory-edit-input";
      priceInput.type = "number";
      priceInput.min = "0.01";
      priceInput.step = "0.01";
      priceInput.required = true;
      priceInput.value = String(product.precio);
      priceInput.dataset.field = "precio";
      priceInput.setAttribute("aria-label", `Precio de ${product.nombre}`);
      priceCell.append(priceInput);
    } else {
      priceCell.textContent = formatCurrency(product.precio);
    }

    const stockCell = document.createElement("td");
    if (isEditing) {
      const stockInput = document.createElement("input");
      stockInput.className = "text-input inventory-edit-input";
      stockInput.type = "number";
      stockInput.min = "0";
      stockInput.step = "1";
      stockInput.required = true;
      stockInput.value = String(product.stock_actual);
      stockInput.dataset.field = "stock_actual";
      stockInput.setAttribute(
        "aria-label",
        `Stock final de ${product.nombre}`,
      );
      stockCell.append(stockInput);
    } else {
      const stockBadge = document.createElement("span");
      stockBadge.className = `stock-badge ${
        product.stock_actual === 0
          ? "stock-empty"
          : product.stock_actual <= 5
            ? "stock-low"
            : "stock-good"
      }`;
      stockBadge.textContent = stockDescription(product.stock_actual);
      stockCell.append(stockBadge);
    }

    const auditCell = document.createElement("td");
    auditCell.className = "inventory-audit-cell";
    auditCell.textContent = `${formatDate(product.creado_en)} · ${
      product.creado_por || "Sin usuario"
    }`;

    const actionCell = document.createElement("td");
    actionCell.className = "inventory-actions-cell";
    if (isEditing) {
      const saveButton = createButton(
        isBusy ? "Guardando…" : "Guardar",
        "table-action-button table-action-primary",
        "save",
        product,
      );
      saveButton.disabled = isBusy;
      const cancelButton = createButton(
        "Cancelar",
        "table-action-button",
        "cancel",
        product,
      );
      cancelButton.disabled = isBusy;
      actionCell.append(saveButton, cancelButton);
    } else if (getCurrentRole() === "ADMIN" || getCurrentRole() === "REPOSITOR") {
      const editButton = createButton(
        "Editar",
        "table-action-button",
        "edit",
        product,
      );
      editButton.disabled = busyProductId !== null;
      const deactivateButton = createButton(
        "Dar de baja",
        "table-action-button table-action-danger",
        "deactivate",
        product,
      );
      deactivateButton.disabled = busyProductId !== null;
      actionCell.append(editButton, deactivateButton);
    }

    row.append(productCell, priceCell, stockCell, auditCell, actionCell);
    return row;
  }

  function render() {
    tableBody.replaceChildren();
    const filteredProducts = getFilteredProducts().sort((a, b) =>
      a.nombre.localeCompare(b.nombre, "es"),
    );
    container.closest(".inventory-list-panel")
      .querySelector("#inventory-count").textContent =
        `${filteredProducts.length} / ${products.length} ${
          products.length === 1 ? "producto" : "productos"
        }`;

    if (isLoading) {
      setFeedback("Cargando inventario…");
    } else if (errorMessage) {
      setFeedback(errorMessage, true);
    } else if (products.length === 0) {
      setFeedback("Todavía no hay productos cargados.");
    } else if (filteredProducts.length === 0) {
      setFeedback("No hay productos que coincidan con el filtro.");
    } else {
      setFeedback("");
    }

    for (const product of filteredProducts) {
      tableBody.append(renderRow(product));
    }
  }

  async function saveProduct(productId, row) {
    const product = products.find((item) => item.id === productId);
    const priceInput = row.querySelector('[data-field="precio"]');
    const stockInput = row.querySelector('[data-field="stock_actual"]');
    const price = Number(priceInput.value);
    const stock = Number(stockInput.value);

    if (!Number.isFinite(price) || price <= 0) {
      priceInput.setCustomValidity("Ingresá un precio mayor a cero.");
      priceInput.reportValidity();
      priceInput.setCustomValidity("");
      return;
    }
    if (!Number.isInteger(stock) || stock < 0) {
      stockInput.setCustomValidity("Ingresá un stock entero igual o mayor a cero.");
      stockInput.reportValidity();
      stockInput.setCustomValidity("");
      return;
    }

    busyProductId = productId;
    render();
    try {
      const updatedProduct = await onSaveProduct(product, {
        nombre: product.nombre,
        descripcion: product.descripcion,
        codigo_barras: product.codigo_barras,
        precio: price,
        stock_actual: stock,
      });
      products = products.map((item) =>
        item.id === updatedProduct.id ? updatedProduct : item,
      );
      editingProductId = null;
      onNotice(`${updatedProduct.nombre} se actualizó correctamente.`, "success");
    } catch (error) {
      onNotice(error.message, "error");
    } finally {
      busyProductId = null;
      render();
    }
  }

  container.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;
    const productId = Number(button.dataset.productId);
    const product = products.find((item) => item.id === productId);
    if (!product) return;

    if (button.dataset.action === "edit") {
      editingProductId = productId;
      render();
      container.querySelector('[data-field="precio"]')?.focus();
      return;
    }
    if (button.dataset.action === "cancel") {
      editingProductId = null;
      render();
      return;
    }
    if (button.dataset.action === "save") {
      await saveProduct(productId, button.closest("tr"));
      return;
    }
    if (button.dataset.action === "deactivate") {
      if (!window.confirm(`¿Dar de baja ${product.nombre}?`)) return;
      busyProductId = productId;
      render();
      try {
        await onDeactivateProduct(product);
        products = products.filter((item) => item.id !== productId);
        onNotice(`${product.nombre} se dio de baja.`, "success");
      } catch (error) {
        onNotice(error.message, "error");
      } finally {
        busyProductId = null;
        render();
      }
    }
  });

  queryInput.addEventListener("input", render);
  stockFilter.addEventListener("change", render);

  return {
    setProducts(nextProducts) {
      products = nextProducts;
      errorMessage = "";
      render();
    },
    setLoading(loading) {
      isLoading = loading;
      if (loading) errorMessage = "";
      render();
    },
    setError(error) {
      errorMessage = error;
      isLoading = false;
      render();
    },
    replaceProduct(updatedProduct) {
      products = products.map((product) =>
        product.id === updatedProduct.id ? updatedProduct : product,
      );
      render();
    },
    removeProduct(productId) {
      products = products.filter((product) => product.id !== productId);
      render();
    },
  };
}
