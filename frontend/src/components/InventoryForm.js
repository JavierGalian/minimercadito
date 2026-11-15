export function createInventoryForm({ container, onSubmit, onError }) {
  container.innerHTML = `
    <form class="inventory-form">
      <label class="field-label" for="product-name">Nombre del producto</label>
      <input
        class="text-input"
        id="product-name"
        name="nombre"
        type="text"
        maxlength="150"
        placeholder="Ej. Yerba mate 1 kg"
        required
      />

      <label class="field-label" for="product-barcode">
        Código de barras <span class="optional-label">OPCIONAL</span>
      </label>
      <input
        class="text-input"
        id="product-barcode"
        name="codigo_barras"
        type="text"
        maxlength="64"
        placeholder="Escaneá o escribí el código"
      />

      <div class="form-row">
        <div>
          <label class="field-label" for="product-price">Precio de venta</label>
          <div class="input-with-prefix">
            <span>$</span>
            <input
              class="text-input"
              id="product-price"
              name="precio"
              type="number"
              min="0.01"
              step="0.01"
              placeholder="0,00"
              required
            />
          </div>
        </div>
        <div>
          <label class="field-label" for="product-stock">Stock inicial</label>
          <input
            class="text-input"
            id="product-stock"
            name="stock_actual"
            type="number"
            min="0"
            step="1"
            value="0"
            required
          />
        </div>
      </div>

      <label class="field-label" for="product-description">
        Descripción <span class="optional-label">OPCIONAL</span>
      </label>
      <textarea
        class="text-input text-area"
        id="product-description"
        name="descripcion"
        rows="3"
        placeholder="Una nota para identificarlo mejor"
      ></textarea>

      <button class="primary-button add-inventory-button" type="submit">
        <span aria-hidden="true">＋</span> Guardar producto
      </button>
      <p class="form-caption">El producto quedará disponible de inmediato en la caja.</p>
    </form>
  `;

  const form = container.querySelector("form");
  const submitButton = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity() || submitButton.disabled) return;

    const data = new FormData(form);
    const codigoBarras = data.get("codigo_barras").trim();
    const descripcion = data.get("descripcion").trim();
    const payload = {
      nombre: data.get("nombre").trim(),
      codigo_barras: codigoBarras || null,
      descripcion: descripcion || null,
      precio: Number(data.get("precio")),
      stock_actual: Number(data.get("stock_actual")),
    };

    submitButton.disabled = true;
    submitButton.textContent = "Guardando…";
    try {
      await onSubmit(payload);
      form.reset();
      form.querySelector("#product-stock").value = "0";
      form.querySelector("#product-name").focus();
    } catch (error) {
      onError(error);
    } finally {
      submitButton.disabled = false;
      submitButton.innerHTML = "<span aria-hidden=\"true\">＋</span> Guardar producto";
    }
  });
}
