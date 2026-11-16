import "./style.css";
import {
  clearAuthSession,
  createProduct,
  createSale,
  deactivateProduct,
  exportInventoryPdf,
  getAuthSession,
  getProductByBarcode,
  getProducts,
  setUnauthorizedHandler,
  updateProduct,
} from "./services/api.js";
import { formatCurrency } from "./services/format.js";
import { createCartTable } from "./components/CartTable.js";
import { createInventoryForm } from "./components/InventoryForm.js";
import { createLoginModal } from "./components/LoginModal.js";
import { createProductSearch } from "./components/ProductSearch.js";
import { createSalesHistory } from "./components/SalesHistory.js";
import { createFinancialReports } from "./components/FinancialReports.js";
import { createInventoryManagement } from "./components/InventoryManagement.js";
import { createUserManagement } from "./components/UserManagement.js";

const app = document.querySelector("#app");

app.innerHTML = `
  <div id="app-shell" hidden>
  <header class="topbar">
    <a class="brand" href="#" aria-label="Mini Mercadito, inicio">
      <span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="M5 13.5h22l-2 14H7l-2-14Z" fill="currentColor" />
          <path d="M10 13.5 16 4l6 9.5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M12 19v4m8-4v4" stroke="#fff" stroke-width="2" stroke-linecap="round" />
        </svg>
      </span>
      <span class="brand-copy">
        <strong>mini mercadito</strong>
        <span>CAJA Y CONTROL DE STOCK</span>
      </span>
    </a>
    <nav class="main-nav" aria-label="Secciones principales">
      <button class="nav-tab is-active" id="tab-pos" type="button" aria-selected="true">
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 5.5h14v11H3v-11Zm3-3h8v3H6v-3Zm1 7h6m-6 3h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Punto de venta
      </button>
      <button class="nav-tab" id="tab-inventory" type="button" aria-selected="false">
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 4.5h14v12H3v-12Zm0 4h14M7 2.5v4m6-4v4m-7 5h2m3 0h2m-7 3h2m3 0h2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Inventario
      </button>
      <button class="nav-tab" id="tab-users" type="button" aria-selected="false" hidden>
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7.5 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm6.5 0a2.5 2.5 0 1 0 0-5m-11 13v-1.5A4.5 4.5 0 0 1 7.5 11h0a4.5 4.5 0 0 1 4.5 4.5V16H3Zm11-5a4 4 0 0 1 3 3.9V16h-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Usuarios
      </button>
      <button class="nav-tab" id="tab-history" type="button" aria-selected="false" hidden>
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 4v6l4 2m3-2a7 7 0 1 1-2.05-4.95M17 3v4h-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Historial
      </button>
      <button class="nav-tab" id="tab-reports" type="button" aria-selected="false" hidden>
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 16.5h14M5 13V8m5 5V3m5 10V6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Reportes
      </button>
    </nav>
    <div class="header-actions">
      <div class="connection-status" id="connection-status" role="status">
        <span class="status-dot is-loading" aria-hidden="true"></span>
        <span>Conectando</span>
      </div>
      <div class="session-controls" id="session-controls" hidden>
        <span class="session-identity" id="session-identity"></span>
        <button class="logout-button" id="logout-button" type="button">Salir</button>
      </div>
    </div>
  </header>

  <main class="page-shell">
    <section class="page-heading" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">MINI MERCADITO <span>/</span> OPERACIONES</p>
        <h1 id="page-title">Punto de venta</h1>
        <p class="page-subtitle">Escaneá, agregá al carrito y cobrá en segundos.</p>
      </div>
      <div class="today-chip">
        <span class="today-icon" aria-hidden="true">◷</span>
        <span id="today-label"></span>
      </div>
    </section>

    <section class="workspace" id="pos-screen" aria-label="Caja">
      <section class="panel catalog-panel" aria-labelledby="catalog-title">
        <div class="panel-heading">
          <div>
            <p class="section-kicker">VENTA ACTUAL</p>
            <h2 id="catalog-title">¿Qué vas a cobrar?</h2>
          </div>
          <span class="count-pill" id="product-count">0 productos</span>
        </div>
        <div id="product-search"></div>
      </section>
      <section class="panel cart-panel" id="cart-table" aria-label="Carrito de venta"></section>
    </section>

    <section class="inventory-screen" id="inventory-screen" aria-label="Inventario" hidden>
      <div class="inventory-layout">
        <section class="panel inventory-form-panel" aria-labelledby="inventory-title">
          <div class="panel-heading">
            <div>
              <p class="section-kicker">GESTIÓN RÁPIDA</p>
              <h2 id="inventory-title">Nuevo producto</h2>
            </div>
            <span class="form-icon" aria-hidden="true">＋</span>
          </div>
          <div id="inventory-form"></div>
        </section>
        <section class="panel inventory-list-panel" aria-labelledby="inventory-list-title">
          <div class="panel-heading">
            <div>
              <p class="section-kicker">ESTADO DE MERCADERÍA</p>
              <h2 id="inventory-list-title">Inventario</h2>
            </div>
            <span class="count-pill" id="inventory-count">0 productos</span>
          </div>
          <div id="inventory-list-management"></div>
        </section>
      </div>
    </section>

    <section class="users-screen" id="users-screen" aria-label="Gestión de usuarios" hidden>
      <div id="user-management"></div>
    </section>

    <section class="sales-history-screen" id="sales-history-screen" aria-label="Historial de ventas" hidden>
      <div id="sales-history"></div>
    </section>

    <section class="financial-reports-screen" id="financial-reports-screen" aria-label="Reportes financieros" hidden>
      <div id="financial-reports"></div>
    </section>

    <div class="toast" id="toast" role="status" aria-live="polite" hidden>
      <span class="toast-icon" aria-hidden="true"></span>
      <span class="toast-message"></span>
      <button class="toast-close" type="button" aria-label="Cerrar aviso">×</button>
    </div>
  </main>
  </div>
  <div id="login-modal" hidden></div>
`;

const state = {
  products: [],
  cart: new Map(),
  busy: false,
  user: null,
};

const toast = document.querySelector("#toast");
const toastMessage = toast.querySelector(".toast-message");
let toastTimer;
const appShell = document.querySelector("#app-shell");

function showNotice(message, type = "info") {
  window.clearTimeout(toastTimer);
  toast.className = `toast toast-${type}`;
  toast.querySelector(".toast-icon").textContent =
    type === "success" ? "✓" : type === "error" ? "!" : "i";
  toastMessage.textContent = message;
  toast.hidden = false;
  toastTimer = window.setTimeout(() => {
    toast.hidden = true;
  }, 5200);
}

toast.querySelector(".toast-close").addEventListener("click", () => {
  toast.hidden = true;
  window.clearTimeout(toastTimer);
});

function setConnectionStatus(connected, message = "") {
  const status = document.querySelector("#connection-status");
  status.classList.toggle("is-offline", !connected);
  status.querySelector(".status-dot").className = `status-dot ${
    connected ? "is-online" : "is-offline"
  }`;
  status.querySelector("span:last-child").textContent =
    message || (connected ? "API conectada" : "API desconectada");
}

function setProducts(products) {
  state.products = products;
  const productsById = new Map(products.map((product) => [product.id, product]));
  for (const [productId, item] of state.cart) {
    const updatedProduct = productsById.get(productId);
    if (updatedProduct) {
      state.cart.set(productId, { ...item, product: updatedProduct });
    }
  }
  productSearch.setProducts(products);
  inventoryManagement.setProducts(products);
  document.querySelector("#product-count").textContent =
    `${products.length} ${products.length === 1 ? "producto" : "productos"}`;
}

function cartItems() {
  return [...state.cart.values()];
}

function addToCart(product) {
  if (product.stock_actual < 1) {
    showNotice(`${product.nombre} no tiene unidades disponibles.`, "error");
    return;
  }

  const current = state.cart.get(product.id);
  const nextQuantity = (current?.quantity ?? 0) + 1;
  if (nextQuantity > product.stock_actual) {
    showNotice(`Stock máximo de ${product.nombre}: ${product.stock_actual}.`, "error");
    return;
  }

  state.cart.set(product.id, {
    product,
    quantity: nextQuantity,
  });
  renderCart();
  showNotice(`${product.nombre} agregado al carrito.`, "success");
}

function changeQuantity(productId, quantity) {
  const item = state.cart.get(productId);
  if (!item) return;

  if (!Number.isInteger(quantity) || quantity < 1) {
    showNotice("La cantidad debe ser un número entero mayor a cero.", "error");
    return;
  }
  if (quantity > item.product.stock_actual) {
    showNotice(`Stock disponible: ${item.product.stock_actual}.`, "error");
    return;
  }

  state.cart.set(productId, { ...item, quantity });
  renderCart();
}

function removeFromCart(productId) {
  state.cart.delete(productId);
  renderCart();
}

function renderCart() {
  cartTable.setItems(cartItems());
  cartTable.setBusy(state.busy);
}

function updateSessionUI() {
  const isAdmin = state.user?.rol === "ADMIN";
  const canManageInventory = isAdmin || state.user?.rol === "REPOSITOR";
  const canOperatePos = isAdmin || state.user?.rol === "CAJERO";
  document.querySelector("#tab-pos").hidden = !canOperatePos;
  document.querySelector("#tab-inventory").hidden = !canManageInventory;
  document.querySelector("#tab-users").hidden = !isAdmin;
  document.querySelector("#tab-history").hidden = !canOperatePos;
  document.querySelector("#tab-reports").hidden = !isAdmin;
  document.querySelector("#session-controls").hidden = !state.user;
  document.querySelector("#session-identity").textContent = state.user
    ? `${state.user.username || "Usuario"} · ${state.user.rol}`
    : "";
  if (
    (!canManageInventory &&
      !document.querySelector("#inventory-screen").hidden) ||
    (!isAdmin &&
      (!document.querySelector("#users-screen").hidden ||
        !document.querySelector("#financial-reports-screen").hidden)) ||
    (!canOperatePos &&
      (!document.querySelector("#pos-screen").hidden ||
        !document.querySelector("#sales-history-screen").hidden))
  ) {
    switchView(canManageInventory ? "inventory" : "pos");
  }
}

async function refreshProducts() {
  inventoryManagement.setLoading(true);
  try {
    const products = await getProducts();
    setProducts(products);
  } catch (error) {
    inventoryManagement.setError(error.message);
    throw error;
  } finally {
    inventoryManagement.setLoading(false);
  }
}

async function activateSession(session) {
  state.user = session;
  appShell.hidden = false;
  loginModal.hide();
  switchView(session.rol === "REPOSITOR" ? "inventory" : "pos");
  updateSessionUI();
  try {
    await refreshProducts();
    setConnectionStatus(true);
  } catch (error) {
    if (error.status !== 401) {
      setConnectionStatus(false);
      showNotice(error.message, "error");
    }
  }
}

async function handleBarcodeSearch(code) {
  const existing = state.products.find(
    (product) => product.codigo_barras === code,
  );
  if (existing) {
    addToCart(existing);
    return;
  }

  const matchesName = state.products.some((product) =>
    product.nombre.toLocaleLowerCase("es").includes(code.toLocaleLowerCase("es")),
  );
  if (matchesName) return;

  try {
    const product = await getProductByBarcode(code);
    setProducts([
      product,
      ...state.products.filter((item) => item.id !== product.id),
    ]);
    addToCart(product);
  } catch (error) {
    showNotice(error.message, "error");
  }
}

async function submitSale() {
  const items = cartItems();
  if (items.length === 0 || state.busy) return;

  state.busy = true;
  renderCart();
  try {
    const sale = await createSale({
      detalles: items.map(({ product, quantity }) => ({
        producto_id: product.id,
        cantidad: quantity,
      })),
    });

    const soldQuantities = new Map(
      items.map(({ product, quantity }) => [product.id, quantity]),
    );
    setProducts(
      state.products.map((product) => ({
        ...product,
        stock_actual: Math.max(
          0,
          product.stock_actual - (soldQuantities.get(product.id) ?? 0),
        ),
      })),
    );
    state.cart.clear();
    showNotice(
      `Venta #${sale.id} registrada por ${formatCurrency(sale.total)}.`,
      "success",
    );
  } catch (error) {
    try {
      await refreshProducts();
      showNotice(error.message, "error");
    } catch (refreshError) {
      showNotice(
        `${error.message} Además, no se pudo actualizar el inventario: ${refreshError.message}`,
        "error",
      );
    }
  } finally {
    state.busy = false;
    renderCart();
  }
}

async function submitProduct(payload) {
  const product = await createProduct(payload);
  setProducts([
    product,
    ...state.products.filter((item) => item.id !== product.id),
  ]);
  showNotice(`${product.nombre} se agregó al inventario.`, "success");
}

const inventoryManagement = createInventoryManagement({
  container: document.querySelector("#inventory-list-management"),
  getCurrentRole: () => state.user?.rol,
  onSaveProduct: async (product, payload) => {
    const updatedProduct = await updateProduct(product.id, payload);
    setProducts(
      state.products.map((item) =>
        item.id === updatedProduct.id ? updatedProduct : item,
      ),
    );
    return updatedProduct;
  },
  onDeactivateProduct: async (product) => {
    await deactivateProduct(product.id);
    state.cart.delete(product.id);
    renderCart();
    setProducts(state.products.filter((item) => item.id !== product.id));
  },
  onExportPdf: exportInventoryPdf,
  onNotice: showNotice,
});

const productSearch = createProductSearch({
  container: document.querySelector("#product-search"),
  onSelect: addToCart,
  onBarcodeSubmit: handleBarcodeSearch,
  onMessage: showNotice,
});

const cartTable = createCartTable({
  container: document.querySelector("#cart-table"),
  onQuantityChange: changeQuantity,
  onRemove: removeFromCart,
  onCheckout: submitSale,
});

createInventoryForm({
  container: document.querySelector("#inventory-form"),
  onSubmit: submitProduct,
  onError: (error) => showNotice(error.message, "error"),
});

const userManagement = createUserManagement({
  container: document.querySelector("#user-management"),
  getCurrentUsername: () => state.user?.username,
  getCurrentRole: () => state.user?.rol,
  onNotice: showNotice,
});

const salesHistory = createSalesHistory({
  container: document.querySelector("#sales-history"),
  onError: (error) => showNotice(error.message, "error"),
});

const financialReports = createFinancialReports({
  container: document.querySelector("#financial-reports"),
  onError: (error) => showNotice(error.message, "error"),
});

function switchView(view) {
  const isAdmin = state.user?.rol === "ADMIN";
  const canManageInventory = isAdmin || state.user?.rol === "REPOSITOR";
  const canOperatePos = isAdmin || state.user?.rol === "CAJERO";
  const isForbidden =
    (view === "inventory" && !canManageInventory) ||
    (["users", "reports"].includes(view) && !isAdmin) ||
    (["pos", "history"].includes(view) && !canOperatePos);
  if (isForbidden) {
    if (state.user) {
      showNotice("Tu rol no tiene permiso para acceder a esta sección.", "error");
      switchView(state.user.rol === "REPOSITOR" ? "inventory" : "pos");
    }
    return;
  }

  const isPos = view === "pos";
  const isInventory = view === "inventory";
  const isUsers = view === "users";
  const isHistory = view === "history";
  const isReports = view === "reports";
  document.querySelector("#pos-screen").hidden = !isPos;
  document.querySelector("#inventory-screen").hidden = !isInventory;
  document.querySelector("#users-screen").hidden = !isUsers;
  document.querySelector("#sales-history-screen").hidden = !isHistory;
  document.querySelector("#financial-reports-screen").hidden = !isReports;
  document.querySelector("#tab-pos").classList.toggle("is-active", isPos);
  document
    .querySelector("#tab-inventory")
    .classList.toggle("is-active", isInventory);
  document.querySelector("#tab-users").classList.toggle("is-active", isUsers);
  document.querySelector("#tab-history").classList.toggle("is-active", isHistory);
  document.querySelector("#tab-reports").classList.toggle("is-active", isReports);
  document.querySelector("#tab-pos").setAttribute("aria-selected", String(isPos));
  document
    .querySelector("#tab-inventory")
    .setAttribute("aria-selected", String(isInventory));
  document
    .querySelector("#tab-users")
    .setAttribute("aria-selected", String(isUsers));
  document
    .querySelector("#tab-history")
    .setAttribute("aria-selected", String(isHistory));
  document
    .querySelector("#tab-reports")
    .setAttribute("aria-selected", String(isReports));
  document.querySelector("#page-title").textContent = isPos
    ? "Punto de venta"
    : isInventory
      ? "Inventario"
      : isUsers
        ? "Usuarios"
        : isHistory
          ? "Historial de ventas"
          : "Reportes financieros";
  document.querySelector(".page-subtitle").textContent = isPos
    ? "Escaneá, agregá al carrito y cobrá en segundos."
    : isInventory
      ? "Mantené tus productos y niveles de stock al día."
      : isUsers
        ? "Administrá las cuentas y los permisos del equipo."
        : isHistory
          ? "Consultá las ventas registradas y sus productos."
          : "Revisá la recaudación mensual y anual.";
  if (isPos) productSearch.focus();
  if (isUsers) void userManagement.load();
  if (isHistory) void salesHistory.load();
  if (isReports) financialReports.load();
}

document.querySelector("#tab-pos").addEventListener("click", () => {
  if (state.user?.rol !== "REPOSITOR") switchView("pos");
});
document.querySelector("#tab-inventory").addEventListener("click", () => {
  if (["ADMIN", "REPOSITOR"].includes(state.user?.rol)) {
    switchView("inventory");
    void refreshProducts().catch((error) => showNotice(error.message, "error"));
  }
});
document.querySelector("#tab-users").addEventListener("click", () => {
  if (state.user?.rol === "ADMIN") switchView("users");
});
document.querySelector("#tab-history").addEventListener("click", () => {
  if (state.user) switchView("history");
});
document.querySelector("#tab-reports").addEventListener("click", () => {
  if (state.user?.rol === "ADMIN") switchView("reports");
});
document.querySelector("#logout-button").addEventListener("click", () => {
  clearAuthSession();
  state.user = null;
  state.cart.clear();
  renderCart();
  switchView("pos");
  appShell.hidden = true;
  loginModal.show();
});
document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(
  "es-AR",
  { dateStyle: "long" },
).format(new Date());

const loginModal = createLoginModal({
  container: document.querySelector("#login-modal"),
  onLogin: activateSession,
});

setUnauthorizedHandler(() => {
  state.user = null;
  state.cart.clear();
  renderCart();
  appShell.hidden = true;
  setConnectionStatus(false, "Sesión vencida");
  loginModal.show();
});

const existingSession = getAuthSession();
if (existingSession) {
  void activateSession(existingSession);
} else {
  loginModal.show();
}
