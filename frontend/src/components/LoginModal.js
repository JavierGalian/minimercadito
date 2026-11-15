import { login } from "../services/api.js";

export function createLoginModal({ container, onLogin }) {
  container.innerHTML = `
    <div class="login-overlay">
      <section
        class="login-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
        aria-describedby="login-description"
      >
        <div class="login-brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none">
            <path d="M5 13.5h22l-2 14H7l-2-14Z" fill="currentColor" />
            <path d="M10 13.5 16 4l6 9.5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 19v4m8-4v4" stroke="#fff" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>
        <p class="login-eyebrow">MINI MERCADITO</p>
        <h1 id="login-title">Ingresá a tu cuenta</h1>
        <p class="login-description" id="login-description">
          Iniciá sesión para acceder a la caja y al inventario.
        </p>
        <form class="login-form">
          <label class="field-label" for="login-username">Usuario</label>
          <input
            class="text-input"
            id="login-username"
            name="username"
            type="text"
            autocomplete="username"
            minlength="3"
            maxlength="64"
            required
          />
          <label class="field-label" for="login-password">Contraseña</label>
          <input
            class="text-input"
            id="login-password"
            name="password"
            type="password"
            autocomplete="current-password"
            required
          />
          <p class="login-error" id="login-error" role="alert" hidden></p>
          <button class="primary-button login-submit" type="submit">
            Iniciar sesión
          </button>
        </form>
        <p class="login-security-note">
          <span aria-hidden="true">●</span> Acceso protegido
        </p>
      </section>
    </div>
  `;

  const form = container.querySelector("form");
  const usernameInput = form.querySelector("#login-username");
  const passwordInput = form.querySelector("#login-password");
  const errorMessage = form.querySelector("#login-error");
  const submitButton = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity() || submitButton.disabled) return;

    errorMessage.hidden = true;
    submitButton.disabled = true;
    submitButton.textContent = "Verificando…";

    try {
      const session = await login(usernameInput.value.trim(), passwordInput.value);
      passwordInput.value = "";
      await onLogin(session);
    } catch (error) {
      errorMessage.textContent = error.message;
      errorMessage.hidden = false;
      passwordInput.focus();
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Iniciar sesión";
    }
  });

  return {
    show() {
      container.hidden = false;
      usernameInput.focus();
    },
    hide() {
      container.hidden = true;
      passwordInput.value = "";
    },
  };
}
