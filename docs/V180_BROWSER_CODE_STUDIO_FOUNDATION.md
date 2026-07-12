# Workbench v1.8.0 — Browser Code Studio Foundation

Workbench v1.8.0 adds the first browser-native code environment to the existing Sustainable Catalyst Workbench. The release establishes the user interface, local project model, storage boundary, terminal behavior, editor workflow, and future runner contract without executing arbitrary code on WordPress or FastAPI.

## Included interface

The main `[sc_workbench]` shortcode now includes a **Code Studio** tab with:

- black-and-green command-line terminal;
- persistent virtual project filesystem;
- browser editor with save and download controls;
- file and directory creation;
- project event log;
- reserved chart/artifact panel;
- built-in foundation documentation;
- project JSON export.

Two standalone shortcodes are also available:

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default"]
[sc_workbench_terminal title="Workbench Terminal" project="default"]
```

The `project` attribute selects the browser-local project namespace. Use a stable value when the same project should reopen on later visits.

## Storage model

The Code Studio stores one structured project record in IndexedDB. If IndexedDB is unavailable, it falls back to localStorage.

The starter project contains:

```text
/
├── README.md
├── src/
│   └── main.js
├── data/
│   └── example.csv
├── tests/
└── output/
```

Files stay within the website's browser origin until the user chooses **Download file** or **Export project**. v1.8.0 does not upload Code Studio files to WordPress, FastAPI, Gemini, or any other service.

## Terminal commands

```text
help
clear
history
pwd
ls [path]
cd [path]
cat <file>
edit <file>
touch <file>
mkdir <directory>
rm [-r] <path>
echo <text>
echo <text> > <file>
files
download <file>
export [name]
status
runtimes
run <file>
stop
reset
```

`run` and `stop` are present as stable command contracts, but execution is intentionally disabled in this foundation release.

## Keyboard behavior

- Up and Down move through command history.
- Ctrl+L clears the terminal display.
- Ctrl+C reports the current cancellation state.
- Ctrl/Cmd+S saves the open editor file.
- Tab inserts two spaces in the editor.

## Frontend modules

```text
assets/js/code-studio/
├── filesystem.js
├── session.js
├── runtime-registry.js
├── output.js
├── editor.js
├── terminal.js
└── code-studio.js
```

The modules communicate through the `window.SCWBCodeStudio` namespace and do not require a JavaScript build step.

## Manifest endpoints

WordPress:

```text
GET /wp-json/sc-workbench/v1/code-studio/manifest
```

FastAPI:

```text
GET /code-studio/manifest
```

Both describe the foundation release, planned browser runtimes, and the draft downloadable Go runner contract.

## Safety boundary

v1.8.0 is not an operating-system shell. Its commands act only on a controlled browser project. The release does not:

- call `eval` on project files;
- launch subprocesses;
- execute code through WordPress;
- execute user code through FastAPI;
- expose server environment variables;
- provide filesystem access outside browser storage;
- accept unrestricted shell commands.

## Next release contract

v1.9.0 is expected to add worker-isolated browser runtimes for JavaScript, Python, R, and SQL. The v1.8 panels and terminal commands are deliberately stable so those runtimes can be added without replacing the interface.
