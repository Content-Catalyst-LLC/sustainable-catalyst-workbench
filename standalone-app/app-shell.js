import { WORKBENCH_CONFIG } from "./config.js";

const state = {
  manifest: null,
  routes: null,
  shell: null,
  auth: null,
  session: null,
  token: null,
  online: false,
  error: null
};

async function request(path, options = {}) {
  const init = {
    method: options.method || "GET",
    headers: Object.assign(
      {"Accept":"application/json","Content-Type":"application/json"},
      options.headers || {}
    )
  };
  if (options.body !== undefined) init.body = JSON.stringify(options.body);
  const response = await fetch(
    WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"") + path,
    init
  );
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
  return payload;
}

async function bootstrapSession() {
  state.auth = (await request("/standalone/v1/auth/config")).auth;
  if (!WORKBENCH_CONFIG.auth.anonymousBootstrap) return;
  const created = await request("/standalone/v1/auth/session/anonymous", {
    method: "POST",
    body: {ttlSeconds:3600,clientLabel:"standalone-app"}
  });
  state.token = created.token;
  state.session = created.session;
}

async function bootstrap() {
  try {
    const [health, manifest, routes, shell] = await Promise.all([
      request("/standalone/v1/health"),
      request("/standalone/v1/app-manifest"),
      request("/standalone/v1/app-routes"),
      request("/standalone/v1/app-shell")
    ]);
    state.online = Boolean(health.ok);
    state.manifest = manifest.manifest;
    state.routes = routes.routeRegistry;
    state.shell = shell.shell;
    await bootstrapSession();
  } catch (error) {
    state.online = false;
    state.error = String(error);
  }
  render();
}

function currentPath() {
  return location.pathname === "/" ? "/calculator" : location.pathname;
}

function navigate(path) {
  history.pushState({}, "", path);
  render();
}

function sessionLabel() {
  if (!state.session) return "NO SESSION";
  if (state.session.subject.type === "anonymous") return "ANONYMOUS SESSION";
  return "AUTHENTICATED SESSION";
}

function render() {
  const root = document.getElementById("sc-workbench-app");
  const routes = state.routes?.routes || [
    {path:"/calculator",label:"Calculator",available:true},
    {path:"/graphs",label:"Graphs",available:true},
    {path:"/settings",label:"Settings",available:true}
  ];
  const path = currentPath();
  const selected = routes.find(r => r.path === path && r.available)
    || routes.find(r => r.path === "/calculator")
    || routes[0];

  root.innerHTML = `
    <div class="sc-shell">
      <header class="sc-topbar">
        <div class="sc-brand">Sustainable Catalyst / Workbench</div>
        <div class="sc-status">${state.online ? "API ONLINE" : "API OFFLINE"} · ${sessionLabel()} · ${WORKBENCH_CONFIG.version}</div>
      </header>
      <div class="sc-main">
        <nav class="sc-nav" aria-label="Workbench">
          ${routes.map(r => `<a href="${r.path}" data-route="${r.path}" data-disabled="${!r.available}" ${selected?.path===r.path?'aria-current="page"':''}>${r.label}</a>`).join("")}
        </nav>
        <main class="sc-workspace">
          <section class="sc-hero">
            <div class="sc-kicker">Standalone authentication & session foundation</div>
            <h1 class="sc-title">${selected?.label || "Workbench"}</h1>
            <p class="sc-copy">The standalone application now owns its session boundary directly with FastAPI. WordPress user identity and WP REST nonces are not required. v12.1 uses signed anonymous bootstrap sessions while leaving the identity-provider boundary open for a later production authentication provider.</p>
          </section>
          <section class="sc-panel">
            <strong>Session</strong>
            <pre>${state.session ? JSON.stringify({
              type: state.session.subject.type,
              sessionId: state.session.sessionId,
              expiresAt: state.session.expiresAt,
              capabilities: state.session.capabilities
            }, null, 2) : "No active session"}</pre>
          </section>
        </main>
      </div>
      <footer class="sc-footer">Standalone session authority: FastAPI · WordPress identity not required</footer>
    </div>`;

  root.querySelectorAll("a[data-route]").forEach(a => {
    if (a.dataset.disabled === "true") return;
    a.addEventListener("click", e => {
      e.preventDefault();
      navigate(a.dataset.route);
    });
  });
}

addEventListener("popstate", render);
bootstrap();
