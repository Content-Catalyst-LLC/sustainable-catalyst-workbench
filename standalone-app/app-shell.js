import { WORKBENCH_CONFIG } from "./config.js";

const state = {
  manifest: null,
  routes: null,
  shell: null,
  online: false,
  error: null
};

async function json(path) {
  const response = await fetch(WORKBENCH_CONFIG.apiBaseUrl.replace(/\/+$/,"") + path, {
    headers: {"Accept":"application/json"}
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function bootstrap() {
  try {
    const [health, manifest, routes, shell] = await Promise.all([
      json("/standalone/v1/health"),
      json("/standalone/v1/app-manifest"),
      json("/standalone/v1/app-routes"),
      json("/standalone/v1/app-shell")
    ]);
    state.online = Boolean(health.ok);
    state.manifest = manifest.manifest;
    state.routes = routes.routeRegistry;
    state.shell = shell.shell;
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
        <div class="sc-status">${state.online ? "API ONLINE" : "API OFFLINE"} · ${WORKBENCH_CONFIG.version}</div>
      </header>
      <div class="sc-main">
        <nav class="sc-nav" aria-label="Workbench">
          ${routes.map(r => `<a href="${r.path}" data-route="${r.path}" data-disabled="${!r.available}" ${selected?.path===r.path?'aria-current="page"':''}>${r.label}</a>`).join("")}
        </nav>
        <main class="sc-workspace">
          <section class="sc-hero">
            <div class="sc-kicker">Standalone application shell</div>
            <h1 class="sc-title">${selected?.label || "Workbench"}</h1>
            <p class="sc-copy">FastAPI is the authoritative computational backend. This application shell runs independently of WordPress and will receive persistent projects, authentication, notebooks, renderers, and reproducibility workflows across the v12 program.</p>
          </section>
          <section class="sc-panel">
            <strong>Runtime</strong>
            <pre>${state.online ? "Connected directly to Workbench API" : "Offline shell mode — backend unavailable"}</pre>
          </section>
        </main>
      </div>
      <footer class="sc-footer">WordPress optional · authoritative computation remains server-side</footer>
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
