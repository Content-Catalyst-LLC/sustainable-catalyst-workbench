# Workbench v1.9.0 — Browser Python, R, JavaScript, and SQL

Workbench v1.9.0 turns the v1.8 Code Studio foundation into a browser execution environment. JavaScript runs in a dedicated Web Worker, Python runs through Pyodide, R runs through webR, and analytical SQL runs through DuckDB-Wasm. The runtime assets load only when requested.

## Execution boundary

- Programs run on the visitor device.
- WordPress does not evaluate submitted code.
- FastAPI exposes a descriptive manifest but no code-execution endpoint.
- Code Studio project files stay in IndexedDB or the localStorage fallback unless explicitly downloaded or exported.
- Browser runtimes receive a copy of the active browser project for the current run.
- Network and system-facing APIs are blocked or rejected by runtime-specific checks.

This is controlled browser execution, not a perfect hostile-code security boundary. Only run code you understand. The future Go runner will add stronger local container isolation for native languages.

## Runtime versions

- JavaScript: browser ECMAScript in a dedicated worker.
- Python: Pyodide 314.0.2.
- R: webR 0.6.0 with R 4.6.0.
- SQL: DuckDB-Wasm 1.30.0.

Versions are pinned in the WordPress Code Studio manifest so runtime changes are intentional and testable.

## Terminal commands

```text
runtime
runtime python
runtime load python
runtime reset python
runtimes
packages python
run /src/main.js
run --runtime python /src/analysis.py
node /src/main.js
python /src/analysis.py
Rscript /src/analysis.R
duckdb /src/query.sql
stop
```

The toolbar provides the same Load, Run active file, and Stop actions.

## Starter project

New projects include:

```text
/README.md
/src/main.js
/src/analysis.py
/src/analysis.R
/src/query.sql
/data/example.csv
/output/
/tests/
```

Existing v1.8 projects are migrated without overwriting user files. A v1.9 readme and missing runtime examples are added.

## JavaScript runtime

The dedicated worker captures `console.log`, `console.warn`, and `console.error`. It exposes a small `workbench` helper:

```javascript
workbench.readFile('/data/example.csv');
workbench.writeFile('/output/result.txt', 'complete');
workbench.table('Results', [{ label: 'A', value: 4 }]);
workbench.chart('Trend', {
  type: 'line',
  labels: ['A', 'B', 'C'],
  values: [2, 5, 4]
});
```

Direct DOM access, browser storage, network APIs, dynamic imports, and dynamic code construction are rejected.

## Python runtime

The Pyodide worker exposes the browser project at `/workbench`. Approved packages include NumPy, pandas, SciPy, SymPy, Matplotlib, scikit-learn, and statsmodels. Packages load only when imports require them.

A local helper module is available:

```python
import workbench
workbench.table("Summary", [{"metric": "mean", "value": 4.2}])
workbench.chart("Trend", "line", ["A", "B", "C"], [2, 5, 4])
workbench.artifact("/output/summary.txt", "complete")
```

Matplotlib figures are saved to `/output` and returned to the Charts panel. Arbitrary package installation, network modules, subprocesses, and the Python-to-JavaScript bridge are blocked.

## R runtime

R uses webR with its base, stats, graphics, grDevices, utils, datasets, and methods packages. Printed output is streamed to the terminal, and plots are returned to the Charts panel. On ordinary WordPress pages it explicitly uses webR's PostMessage channel; sites configured with COOP/COEP cross-origin isolation can use SharedArrayBuffer communication and true interruption.

```r
data <- read.csv("/workbench/data/example.csv")
print(summary(data))
plot(data$value, type = "b", main = "Example values")
```

System commands, network functions, and arbitrary package installation are blocked.

## SQL runtime

DuckDB-Wasm registers project CSV, JSON, NDJSON, and text files using paths without the leading slash.

```sql
SELECT category, AVG(value) AS average_value
FROM read_csv_auto('data/example.csv')
GROUP BY category
ORDER BY category;
```

Query results are rendered as a table. Remote URLs, extension installation, attached databases, external import/export, and runtime configuration statements are blocked.

## Time and size limits

Default public limits:

```text
Execution timeout: 15 seconds
Maximum source file: 256 KiB
Displayed table rows: 500
Network access: restricted
Project upload: disabled by default
```

Stopping JavaScript, Python, or SQL resets the active worker/runtime. Cross-origin-isolated R pages use webR interrupt support. In PostMessage mode, where interruption is unavailable, Stop closes and resets the R runtime.

## Content Security Policy

A strict custom CSP may need these sources in addition to the site origin:

```text
script-src: https://cdn.jsdelivr.net https://webr.r-wasm.org
worker-src: 'self' blob: https://cdn.jsdelivr.net https://webr.r-wasm.org
connect-src: 'self' https://cdn.jsdelivr.net https://webr.r-wasm.org
```

Exact directives depend on the site and security plugin. Do not weaken an existing policy broadly; allow only the pinned origins needed by Code Studio. Optional `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers improve webR communication and make interruption available, but can affect third-party embeds and authentication popups and therefore should be tested before deployment.

## Shortcodes

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default" display="full"]
[sc_workbench_terminal title="Workbench Terminal" project="default" display="full"]
```

The main `[sc_workbench]` shortcode also includes the Code Studio tab.

## Deferred to later releases

v1.9.0 does not compile C, C++, Go, Rust, Java, Haskell, Fortran, Julia, or embedded firmware. Those native and hardware runtimes remain assigned to the downloadable Go runner roadmap.
