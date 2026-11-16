import {
  createUser,
  deactivateUser,
  getUsers,
  updateUser,
} from "../services/api.js";

export function createUserManagement({
  container,
  getCurrentUsername,
  getCurrentRole,
  onNotice,
}) {
  container.innerHTML = `
    <p class="user-access-denied" id="user-access-denied" role="alert" hidden></p>
    <div class="user-management-layout">
      <section class="panel user-form-panel" aria-labelledby="user-form-title">
        <div class="panel-heading">
          <div>
            <p class="section-kicker">ACCESOS DEL EQUIPO</p>
            <h2 id="user-form-title">Crear usuario</h2>
          </div>
          <span class="form-icon" aria-hidden="true">＋</span>
        </div>
        <form class="inventory-form" id="user-create-form">
          <input id="user-id" name="user_id" type="hidden" />
          <label class="field-label" for="user-username">Nombre de usuario</label>
          <input
            class="text-input"
            id="user-username"
            name="username"
            type="text"
            minlength="3"
            maxlength="64"
            pattern="[a-zA-Z0-9_.\\-]+"
            autocomplete="username"
            required
          />

          <label class="field-label" for="user-password">Contraseña inicial</label>
          <input
            class="text-input"
            id="user-password"
            name="password"
            type="password"
            minlength="12"
            maxlength="72"
            autocomplete="new-password"
            required
            aria-describedby="user-password-help"
          />

          <label class="field-label" for="user-role">Rol</label>
          <select class="text-input user-role-select" id="user-role" name="rol" required>
            <option value="CAJERO">Cajero</option>
            <option value="REPOSITOR">Repositor</option>
            <option value="ADMIN">Administrador</option>
          </select>

          <button class="primary-button add-inventory-button" type="submit">
            Crear usuario
          </button>
          <button class="secondary-button user-cancel-edit" id="user-cancel-edit" type="button" hidden>
            Cancelar edición
          </button>
          <p class="form-caption" id="user-password-help">
            La contraseña se almacena protegida en el servidor.
          </p>
        </form>
      </section>

      <section class="panel users-list-panel" aria-labelledby="users-list-title">
        <div class="panel-heading">
          <div>
            <p class="section-kicker">CUENTAS REGISTRADAS</p>
            <h2 id="users-list-title">Usuarios</h2>
          </div>
          <span class="count-pill" id="users-count">0 usuarios</span>
        </div>
        <p class="users-feedback" id="users-feedback" role="status" aria-live="polite">
          Cargando usuarios…
        </p>
        <div class="users-table-wrap" id="users-table-container"></div>
      </section>
    </div>
  `;

  const form = container.querySelector("#user-create-form");
  const submitButton = form.querySelector('button[type="submit"]');
  const usernameInput = form.querySelector("#user-username");
  const passwordInput = form.querySelector("#user-password");
  const roleInput = form.querySelector("#user-role");
  const userIdInput = form.querySelector("#user-id");
  const formTitle = container.querySelector("#user-form-title");
  const cancelEditButton = container.querySelector("#user-cancel-edit");
  const feedback = container.querySelector("#users-feedback");
  const tableContainer = container.querySelector("#users-table-container");
  const count = container.querySelector("#users-count");
  const accessDenied = container.querySelector("#user-access-denied");
  let users = [];
  let isLoading = false;
  let editingUserId = null;

  function setFeedback(message) {
    feedback.textContent = message;
    feedback.hidden = !message;
  }

  function renderUsers() {
    count.textContent = `${users.length} ${
      users.length === 1 ? "usuario" : "usuarios"
    }`;
    tableContainer.replaceChildren();

    if (users.length === 0) {
      const empty = document.createElement("p");
      empty.className = "inventory-empty";
      empty.textContent = "Todavía no hay usuarios registrados.";
      tableContainer.append(empty);
      return;
    }

    const table = document.createElement("table");
    table.className = "users-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th scope="col">Usuario</th>
          <th scope="col">Rol</th>
          <th scope="col">Estado</th>
          <th scope="col"><span class="sr-only">Acciones</span></th>
        </tr>
      </thead>
    `;
    const body = document.createElement("tbody");

    for (const user of users) {
      const row = document.createElement("tr");
      const username = document.createElement("th");
      username.scope = "row";
      username.textContent = user.username;

      const roleCell = document.createElement("td");
      const roleBadge = document.createElement("span");
      roleBadge.className = `user-role-badge ${
        user.rol === "ADMIN" ? "user-role-admin" : ""
      }`;
      roleBadge.textContent =
        user.rol === "ADMIN"
          ? "Administrador"
          : user.rol === "REPOSITOR"
            ? "Repositor"
            : "Cajero";
      roleCell.append(roleBadge);

      const statusCell = document.createElement("td");
      const statusBadge = document.createElement("span");
      statusBadge.className = `user-status-badge ${
        user.activo ? "user-status-active" : "user-status-inactive"
      }`;
      statusBadge.textContent = user.activo ? "Activo" : "Desactivado";
      statusCell.append(statusBadge);

      const actionCell = document.createElement("td");
      const isCurrentUser = user.username === getCurrentUsername();
      if (user.activo) {
        const editButton = document.createElement("button");
        editButton.className = "user-edit-button";
        editButton.type = "button";
        editButton.textContent = "Editar";
        editButton.dataset.action = "edit";
        editButton.dataset.userId = String(user.id);
        editButton.setAttribute("aria-label", `Editar usuario ${user.username}`);
        actionCell.append(editButton);
      }
      if (user.activo && !isCurrentUser) {
        const deactivateButton = document.createElement("button");
        deactivateButton.className = "user-deactivate-button";
        deactivateButton.type = "button";
        deactivateButton.textContent = "Desactivar";
        deactivateButton.dataset.action = "deactivate";
        deactivateButton.dataset.userId = String(user.id);
        deactivateButton.setAttribute(
          "aria-label",
          `Desactivar usuario ${user.username}`,
        );
        actionCell.append(deactivateButton);
      } else if (isCurrentUser) {
        const currentLabel = document.createElement("span");
        currentLabel.className = "user-current-label";
        currentLabel.textContent = "Sesión actual";
        actionCell.append(currentLabel);
      }

      row.append(username, roleCell, statusCell, actionCell);
      body.append(row);
    }

    table.append(body);
    tableContainer.append(table);
  }

  function resetForm() {
    editingUserId = null;
    userIdInput.value = "";
    form.reset();
    usernameInput.readOnly = false;
    passwordInput.required = true;
    passwordInput.placeholder = "";
    roleInput.disabled = false;
    formTitle.textContent = "Crear usuario";
    submitButton.textContent = "Crear usuario";
    cancelEditButton.hidden = true;
    container.querySelector("#user-password-help").textContent =
      "La contraseña se almacena protegida en el servidor.";
  }

  function startEditing(user) {
    editingUserId = user.id;
    userIdInput.value = String(user.id);
    usernameInput.value = user.username;
    usernameInput.readOnly = user.username === getCurrentUsername();
    passwordInput.value = "";
    passwordInput.required = false;
    passwordInput.placeholder = "Dejar vacío para conservarla";
    roleInput.value = user.rol;
    roleInput.disabled = user.username === getCurrentUsername();
    formTitle.textContent = `Editar ${user.username}`;
    submitButton.textContent = "Guardar cambios";
    cancelEditButton.hidden = false;
    container.querySelector("#user-password-help").textContent =
      "Deja la contraseña vacía si no quieres cambiarla.";
    usernameInput.focus();
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity() || submitButton.disabled) return;

    const data = new FormData(form);
    const payload = { username: data.get("username").trim() };
    const password = data.get("password");
    const isEditing = editingUserId !== null;
    if (!isEditing || password) payload.password = password;
    if (!roleInput.disabled) payload.rol = data.get("rol");

    submitButton.disabled = true;
    submitButton.textContent = isEditing ? "Guardando…" : "Creando…";
    try {
      const user = isEditing
        ? await updateUser(editingUserId, payload)
        : await createUser({ ...payload, rol: data.get("rol") });
      users = isEditing
        ? users.map((item) => (item.id === user.id ? user : item))
        : [user, ...users.filter((item) => item.id !== user.id)];
      renderUsers();
      resetForm();
      onNotice(
        isEditing
          ? `Se actualizó el usuario ${user.username}.`
          : `Se creó el usuario ${user.username}.`,
        "success",
      );
    } catch (error) {
      onNotice(error.message, "error");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = editingUserId
        ? "Guardar cambios"
        : "Crear usuario";
    }
  });

  cancelEditButton.addEventListener("click", resetForm);

  tableContainer.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;

    const user = users.find((item) => item.id === Number(button.dataset.userId));
    if (!user) return;
    if (button.dataset.action === "edit") {
      startEditing(user);
      return;
    }
    if (
      button.dataset.action !== "deactivate" ||
      !window.confirm(`¿Desactivar al usuario ${user.username}?`)
    ) {
      return;
    }

    button.disabled = true;
    button.textContent = "Desactivando…";
    try {
      await deactivateUser(user.id);
      users = users.map((item) =>
        item.id === user.id ? { ...item, activo: false } : item,
      );
      renderUsers();
      onNotice(`Se desactivó el usuario ${user.username}.`, "success");
    } catch (error) {
      button.disabled = false;
      button.textContent = "Desactivar";
      onNotice(error.message, "error");
    }
  });

  return {
    async load() {
      if (isLoading) return;
      if (getCurrentRole() !== "ADMIN") {
        accessDenied.textContent =
          "Acceso restringido: solo ADMIN puede gestionar usuarios.";
        accessDenied.hidden = false;
        container.querySelector(".user-form-panel").hidden = true;
        container.querySelector(".users-list-panel").hidden = true;
        return;
      }
      accessDenied.hidden = true;
      container.querySelector(".user-form-panel").hidden = false;
      container.querySelector(".users-list-panel").hidden = false;
      isLoading = true;
      setFeedback("Cargando usuarios…");
      try {
        users = await getUsers();
        renderUsers();
        setFeedback("");
        if (users.length === 0) {
          setFeedback("No hay usuarios registrados.");
        }
      } catch (error) {
        setFeedback(error.message);
        onNotice(error.message, "error");
      } finally {
        isLoading = false;
      }
    },
  };
}
