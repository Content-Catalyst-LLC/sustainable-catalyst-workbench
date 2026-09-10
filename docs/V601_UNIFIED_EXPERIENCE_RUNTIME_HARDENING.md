# Workbench v6.0.1 — Unified Experience, Runtime Identity & Interface Hardening

The v6.0.1 interface is organized around a dense application shell rather than a long feature index. The complete 39-studio registry remains available, with Project, Math, Model, Engineer, Data, and Record filters plus search, favorites, and recent-studio state.

The canonical public Workbench experience is `[sc_workbench_experience]`. It opens the full Workbench, the unified computational project, Advanced Graph Mathematics, a compact capability matrix, and the connected workflow. It intentionally does **not** embed `[sc_workbench_homepage_instrument]`.

Advanced Graph Mathematics observes container size and redraws after activation/visibility events so canvases do not retain stale dimensions when the user changes studios, resizes the viewport, enters/exits fullscreen, or returns to the page.

Current-release identity is `6.0.1` across the WordPress plugin, primary studio shell, FastAPI application, Docker image, `/v601/status`, and the unified public experience. The bounded unified computational-project endpoints remain under `/v600/*` for compatibility.
