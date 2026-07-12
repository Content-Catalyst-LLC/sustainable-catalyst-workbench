# WordPress Usage

Install `sustainable-catalyst-workbench-plugin-v1.9.1.zip` from Plugins → Add New → Upload Plugin.

Use:

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

Settings:

- Backend URL: `http://127.0.0.1:8088` for local testing.
- Production backend: use HTTPS, for example `https://api.sustainablecatalyst.com`.
- Enable scope gate.
- Keep debug mode disabled on the public site.
- Prefer backend `.env` for provider keys in production. WordPress-managed OpenAI key storage is available for controlled use.

## Browser Code Studio v1.8.0

Use the full browser Code Studio:

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default" display="full"]
```

Use the terminal-only presentation:

```text
[sc_workbench_terminal title="Workbench Terminal" project="default" display="full"]
```

The `project` value becomes the stable browser-local namespace. Files are stored in IndexedDB with a localStorage fallback. v1.8.0 does not execute project code or upload project files.



## Browser Runtime Pack v1.9.0

The Code Studio now executes `.js`, `.py`, `.R`, and `.sql` files in the visitor browser. Select a runtime in the toolbar or use terminal commands:

```text
node /src/main.js
python /src/analysis.py
Rscript /src/analysis.R
duckdb /src/query.sql
```

The first Python, R, or SQL run downloads its pinned WebAssembly runtime. Projects remain in IndexedDB or the localStorage fallback. WordPress and FastAPI do not receive or execute project source. Sites with a custom Content Security Policy must allow the pinned runtime origins and `blob:` workers described in `V190_BROWSER_PYTHON_R_JAVASCRIPT_SQL.md`.


## Editor-First Code Lab v1.9.1

The full Code Studio now opens on the **Code** panel rather than the terminal. Select JavaScript, Python, R, or SQL; choose a project file; type or paste code; and click **Run**. The open file is saved automatically before execution.

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default" display="full"]
```

The first Python, R, or SQL execution may take longer while the browser downloads its runtime. Output appears beside the editor. Structured tables and charts appear under **Tables & Charts**. The old command interface remains under **Advanced Console** and in the standalone terminal shortcode.
