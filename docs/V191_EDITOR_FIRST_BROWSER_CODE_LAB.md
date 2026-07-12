# Workbench v1.9.1 — Editor-First Browser Code Lab

Version 1.9.1 corrects the v1.9.0 Code Studio interaction model. The browser terminal remains available, but it is no longer the primary way to run code.

## Primary workflow

1. Select JavaScript, Python, R, or SQL.
2. Select a runnable project file.
3. Type or paste code into the black-and-green editor.
4. Click **Run** or press Ctrl/Command + Enter.
5. Read standard output, errors, and completion status beside the editor.
6. Open **Tables & Charts** for structured analytical results.

## Interface changes

- Code opens as the default panel.
- Editor and output are shown together on wide screens and stack responsively on smaller screens.
- A line-number gutter follows editor scrolling and editing.
- Runtime selection opens the matching starter file.
- Run saves the open file before execution.
- Runtime assets load automatically on first execution.
- Stop directly interrupts or resets the active browser runtime where supported.
- The command-line environment is retained under **Advanced Console**.

## Browser execution boundary

JavaScript runs in an isolated Web Worker. Python uses Pyodide, R uses webR, and SQL uses DuckDB-Wasm. Project source remains in browser-local storage unless the user downloads or exports it. WordPress and FastAPI do not execute submitted browser code.

## Compatibility

Existing v1.8 and v1.9 browser projects are upgraded in place. User-created files are preserved. A v1.9.1 README is added to the project to explain the revised interaction model.

## Shortcode

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default" display="full"]
```

The standalone terminal shortcode remains available:

```text
[sc_workbench_terminal title="Workbench Terminal" project="default" display="full"]
```
