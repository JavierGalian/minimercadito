const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";
const AUTH_STORAGE_KEY = "mini-mercadito-auth";
let unauthorizedHandler = () => {};

export function getAuthSession() {
  let serializedSession;
  try {
    serializedSession = localStorage.getItem(AUTH_STORAGE_KEY);
  } catch {
    throw new ApiError("El navegador no permite acceder al almacenamiento local.");
  }
  if (!serializedSession) return null;

  try {
    const session = JSON.parse(serializedSession);
    if (
      typeof session.token === "string" &&
      session.token.length > 0 &&
      ["ADMIN", "CAJERO", "REPOSITOR"].includes(session.rol)
    ) {
      return session;
    }
  } catch {
    clearAuthSession();
    return null;
  }

  clearAuthSession();
  return null;
}

export function saveAuthSession(session, username) {
  if (
    typeof session.access_token !== "string" ||
    !["ADMIN", "CAJERO", "REPOSITOR"].includes(session.rol)
  ) {
    throw new ApiError("La API devolvió una sesión no válida.");
  }
  try {
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        token: session.access_token,
        rol: session.rol,
        username,
      }),
    );
  } catch {
    throw new ApiError("No se pudo guardar la sesión en este navegador.");
  }
}

export function clearAuthSession() {
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch {
    throw new ApiError("No se pudo cerrar la sesión en este navegador.");
  }
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function formatDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((issue) => {
        const field = Array.isArray(issue.loc)
          ? issue.loc.filter((part) => part !== "body").join(".")
          : "";
        return field ? `${field}: ${issue.msg}` : issue.msg;
      })
      .filter(Boolean)
      .join(" · ");
  }
  return "La solicitud no pudo completarse.";
}

async function request(path, options = {}) {
  const {
    skipAuth = false,
    responseType = "json",
    ...fetchOptions
  } = options;
  const authSession = skipAuth ? null : getAuthSession();
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      headers: {
        Accept: responseType === "blob" ? "application/pdf" : "application/json",
        ...(fetchOptions.body ? { "Content-Type": "application/json" } : {}),
        ...(authSession
          ? { Authorization: `Bearer ${authSession.token}` }
          : {}),
        ...fetchOptions.headers,
      },
    });
  } catch {
    throw new ApiError(
      "No se pudo conectar con el servidor. Verificá que la API esté disponible.",
    );
  }

  let body = null;
  if (!(response.ok && responseType === "blob")) {
    const responseText = await response.text();
    if (responseText) {
      try {
        body = JSON.parse(responseText);
      } catch {
        throw new ApiError(
          "El servidor devolvió una respuesta que no se pudo interpretar.",
          response.status,
        );
      }
    }
  }

  if (response.status === 401 && authSession) {
    clearAuthSession();
    unauthorizedHandler();
  }

  if (!response.ok) {
    throw new ApiError(
      formatDetail(body?.detail),
      response.status,
      body?.detail ?? body,
    );
  }
  if (responseType === "blob") {
    return {
      blob: await response.blob(),
      contentDisposition: response.headers.get("Content-Disposition"),
    };
  }
  return body;
}

export async function login(username, password) {
  const session = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    skipAuth: true,
  });
  saveAuthSession(session, username);
  return getAuthSession();
}

export function getProducts() {
  return request("/productos");
}

export async function exportInventoryPdf() {
  const { blob, contentDisposition } = await request(
    "/inventory/export/pdf",
    { responseType: "blob" },
  );
  const filename = /filename="?([^";]+)"?/i.exec(contentDisposition || "")?.[1];
  if (!filename) {
    throw new ApiError("El servidor no indicó el nombre del archivo PDF.");
  }
  return { blob, filename };
}

export function getProductByBarcode(code) {
  return request(`/productos/codigo-barras/${encodeURIComponent(code)}`);
}

export function createProduct(product) {
  return request("/productos", {
    method: "POST",
    body: JSON.stringify(product),
  });
}

export function updateProduct(productId, product) {
  return request(`/productos/${encodeURIComponent(productId)}`, {
    method: "PUT",
    body: JSON.stringify(product),
  });
}

export function deactivateProduct(productId) {
  return request(`/productos/${encodeURIComponent(productId)}`, {
    method: "DELETE",
  });
}

export function createSale(sale) {
  return request("/ventas", {
    method: "POST",
    body: JSON.stringify(sale),
  });
}

export function getUsers() {
  return request("/users");
}

export function createUser(user) {
  return request("/users", {
    method: "POST",
    body: JSON.stringify(user),
  });
}

export function updateUser(userId, user) {
  return request(`/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: JSON.stringify(user),
  });
}

export function deactivateUser(userId) {
  return request(`/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
}

export function getSalesHistory(limit = 21, offset = 0) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return request(`/ventas/historial?${query}`);
}

export function getMonthlySalesReport(year, month) {
  const query = new URLSearchParams({
    anio: String(year),
    mes: String(month),
  });
  return request(`/ventas/reportes/mensual?${query}`);
}

export function getAnnualSalesReport(year) {
  const query = new URLSearchParams({ anio: String(year) });
  return request(`/ventas/reportes/anual?${query}`);
}
