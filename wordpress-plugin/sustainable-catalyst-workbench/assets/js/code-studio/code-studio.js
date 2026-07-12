(function (window, document) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};
  const starterFiles = {
    javascript: '/src/main.js',
    python: '/src/analysis.py',
    r: '/src/analysis.R',
    sql: '/src/query.sql'
  };

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, function (character) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character];
    });
  }

  function initStudio(studio) {
    if (studio.__scwbCodeStudioInitialized) return;
    studio.__scwbCodeStudioInitialized = true;

    const projectId = studio.dataset.scwbProjectId || 'default';
    const terminalOnly = studio.dataset.scwbTerminalOnly === '1';
    const fileSystem = root.FileSystem.create(projectId);
    const session = root.Session.create(projectId);
    const outputLog = root.Output.create(studio.querySelector('[data-scwb-code-events]'));
    const navButtons = Array.prototype.slice.call(studio.querySelectorAll('[data-scwb-code-tab]'));
    const panels = Array.prototype.slice.call(studio.querySelectorAll('[data-scwb-code-panel]'));
    const runtimeSelect = studio.querySelector('[data-scwb-runtime-select]');
    const fileSelect = studio.querySelector('[data-scwb-file-select]');
    const runtimeChip = studio.querySelector('[data-scwb-runtime-chip]');
    const runnerChip = studio.querySelector('[data-scwb-runner-chip]');
    const runButton = studio.querySelector('[data-scwb-run-active]');
    const stopButton = studio.querySelector('[data-scwb-stop-active]');
    const loadButton = studio.querySelector('[data-scwb-load-runtime]');
    const runOutput = studio.querySelector('[data-scwb-run-output]');
    const runState = studio.querySelector('[data-scwb-run-state]');
    const runClear = studio.querySelector('[data-scwb-run-clear]');
    const editorTextarea = studio.querySelector('[data-scwb-code-editor]');
    let terminal = null;
    let editor = null;
    let runtimeManager = null;
    let chartRenderer = null;

    function activatePanel(name) {
      if (terminalOnly && name !== 'terminal') return;
      navButtons.forEach(function (button) { button.classList.toggle('is-active', button.dataset.scwbCodeTab === name); });
      panels.forEach(function (panel) { panel.classList.toggle('is-active', panel.dataset.scwbCodePanel === name); });
      session.set('activePanel', name);
    }

    navButtons.forEach(function (button) {
      button.addEventListener('click', function () { activatePanel(button.dataset.scwbCodeTab); });
    });

    function clearRunOutput(message) {
      if (!runOutput) return;
      runOutput.innerHTML = '';
      if (message) appendRunOutput(message, 'system');
    }

    function appendRunOutput(text, type) {
      if (!runOutput) return;
      const value = String(text == null ? '' : text);
      if (!value) return;
      value.replace(/\r\n/g, '\n').split('\n').forEach(function (line, index, lines) {
        if (index === lines.length - 1 && line === '') return;
        const row = document.createElement('div');
        row.className = 'scwb-run-output-line scwb-run-output-' + (type || 'output');
        row.textContent = line || ' ';
        runOutput.appendChild(row);
      });
      runOutput.scrollTop = runOutput.scrollHeight;
    }

    function setRunState(label, status) {
      if (!runState) return;
      runState.textContent = label;
      runState.dataset.status = status || 'idle';
    }

    function updateRuntimeStatus(event) {
      if (!event) return;
      const runtime = root.RuntimeRegistry.get(event.runtime);
      const label = runtime ? runtime.label : event.runtime;
      if (runtimeChip) {
        runtimeChip.textContent = label + ': ' + event.status + (event.detail ? ' · ' + event.detail : '');
        runtimeChip.dataset.status = event.status;
      }
      if (runnerChip) runnerChip.textContent = event.status === 'running' ? 'Browser job running' : 'Local runner: v2.0.0 roadmap';
      if (runButton) runButton.disabled = event.status === 'running' || event.status === 'loading';
      if (stopButton) stopButton.disabled = event.status !== 'running';
      if (loadButton) loadButton.disabled = event.status === 'running' || event.status === 'loading';
      if (event.status === 'loading') setRunState('Loading ' + label + '…', 'loading');
      else if (event.status === 'running') setRunState('Running', 'running');
      else if (event.status === 'ready') setRunState('Ready', 'ready');
      else if (event.status === 'error') setRunState('Error', 'error');
      else if (event.status === 'stopped') setRunState('Stopped', 'stopped');
    }

    function handleStream(stream, text) {
      const type = stream === 'stderr' ? 'error' : (stream === 'system' ? 'system' : (stream === 'result' ? 'success' : 'output'));
      appendRunOutput(text, type);
      if (terminal) terminal.writeBlock(text, type);
    }

    function refreshFiles() {
      const list = studio.querySelector('[data-scwb-code-files]');
      if (!fileSystem.getProject()) return;
      const project = fileSystem.getProject();
      const paths = Object.keys(project.files).filter(function (path) { return path !== '/'; }).sort(function (a, b) {
        const aNode = project.files[a];
        const bNode = project.files[b];
        if (aNode.type !== bNode.type) return aNode.type === 'directory' ? -1 : 1;
        return a.localeCompare(b);
      });
      if (list) {
        list.innerHTML = paths.map(function (path) {
          const node = project.files[path];
          const icon = node.type === 'directory' ? 'DIR' : 'FILE';
          const action = node.type === 'file' ? '<button type="button" data-scwb-open-file="' + escapeHtml(path) + '">Open</button>' : '';
          return '<article class="scwb-code-file-row">' +
            '<span class="scwb-code-file-type">' + icon + '</span>' +
            '<code>' + escapeHtml(path) + '</code>' +
            action +
            '</article>';
        }).join('') || '<p class="scwb-code-empty">No project files.</p>';
      }
      refreshRunnableFiles();
    }

    function runtimeFiles(runtime) {
      if (!fileSystem.getProject()) return [];
      return fileSystem.allFiles().filter(function (path) {
        return root.RuntimeManager.detectRuntime(path) === runtime;
      }).sort();
    }

    function refreshRunnableFiles() {
      if (!fileSelect || !runtimeManager) return;
      const runtime = runtimeSelect ? runtimeSelect.value : runtimeManager.getSelectedRuntime();
      const files = runtimeFiles(runtime);
      fileSelect.innerHTML = files.map(function (path) {
        return '<option value="' + escapeHtml(path) + '">' + escapeHtml(path) + '</option>';
      }).join('');
      const active = editor ? editor.getActivePath() : '';
      if (files.indexOf(active) >= 0) fileSelect.value = active;
      else if (files.length) fileSelect.value = files[0];
      fileSelect.disabled = !files.length;
    }

    function openFile(path) {
      if (!editor || !path) return Promise.resolve();
      const open = function () {
        editor.open(path);
        if (fileSelect) fileSelect.value = path;
        return path;
      };
      return editor.isDirty() ? editor.save().then(open) : Promise.resolve(open());
    }

    function openRuntimeStarter(runtime) {
      const candidates = runtimeFiles(runtime);
      const target = fileSystem.exists(starterFiles[runtime]) ? starterFiles[runtime] : candidates[0];
      if (!target) return Promise.resolve();
      return openFile(target);
    }

    function runActiveFile() {
      if (!runtimeManager || !editor) return Promise.reject(new Error('Code Studio is still initializing.'));
      const runtime = runtimeSelect ? runtimeSelect.value : runtimeManager.getSelectedRuntime();
      const path = editor.getActivePath();
      if (!path || !fileSystem.exists(path)) return Promise.reject(new Error('Open a runnable source file first.'));
      const detected = root.RuntimeManager.detectRuntime(path);
      if (detected && detected !== runtime) {
        return openRuntimeStarter(runtime).then(runActiveFile);
      }
      const save = editor.isDirty() ? editor.save() : Promise.resolve(path);
      clearRunOutput();
      appendRunOutput('Running ' + path + ' with ' + runtime + '…', 'system');
      setRunState('Starting', 'loading');
      outputLog.add('Run requested', runtime + ' · ' + path, 'info');
      return save.then(function () {
        return runtimeManager.run(path, runtime);
      }).then(function (result) {
        const duration = Number(result.durationMs || 0);
        if (result.ok) {
          appendRunOutput('Program finished successfully' + (duration ? ' in ' + duration + ' ms' : '') + '.', 'success');
          setRunState('Completed', 'ready');
          const resultCount = (result.tables || []).length + (result.charts || []).length;
          if (resultCount) appendRunOutput(resultCount + ' table/chart result(s) are available in Tables & Charts.', 'system');
        } else {
          appendRunOutput(result.error || 'Execution failed.', result.stopped ? 'warning' : 'error');
          setRunState(result.stopped ? 'Stopped' : 'Error', result.stopped ? 'stopped' : 'error');
        }
        return result;
      }).catch(function (error) {
        appendRunOutput(error.message || String(error), 'error');
        setRunState('Error', 'error');
        outputLog.add('Run failed', error.message || String(error), 'error');
        throw error;
      });
    }

    fileSystem.init().then(function () {
      const storageChip = studio.querySelector('[data-scwb-storage-chip]');
      if (storageChip) storageChip.textContent = fileSystem.getStorageMode() === 'indexeddb' ? 'IndexedDB ready' : 'Local storage fallback';

      editor = root.Editor.create({
        fileSystem: fileSystem,
        session: session,
        textarea: editorTextarea,
        lineNumbers: studio.querySelector('[data-scwb-line-numbers]'),
        pathLabel: studio.querySelector('[data-scwb-editor-path]'),
        statusLabel: studio.querySelector('[data-scwb-editor-status]'),
        saveButton: studio.querySelector('[data-scwb-editor-save]'),
        downloadButton: studio.querySelector('[data-scwb-editor-download]'),
        onSaved: function (path) {
          outputLog.add('File saved', path, 'success');
          refreshFiles();
        },
        onError: function (error) {
          outputLog.add('Editor error', error.message || String(error), 'error');
        }
      });

      outputLog.render();
      chartRenderer = root.ChartRenderer.create(studio.querySelector('[data-scwb-chart-results]'));

      const manifest = root.RuntimeRegistry.manifest();
      runtimeManager = root.RuntimeManager.create({
        fileSystem: fileSystem,
        manifest: manifest,
        selectedRuntime: session.get('runtime') || 'javascript',
        callbacks: {
          stream: handleStream,
          clear: function () {
            clearRunOutput();
            if (terminal) terminal.clear();
          },
          status: function (event) {
            updateRuntimeStatus(event);
            if (runtimeSelect && event.runtime) runtimeSelect.value = event.runtime;
          },
          result: function (result, path) {
            if (chartRenderer) chartRenderer.render(result, false);
            refreshFiles();
            outputLog.add(result.ok ? 'Browser runtime result' : 'Browser runtime error', path + ' · ' + (result.durationMs || 0) + ' ms', result.ok ? 'success' : 'error');
          },
          stopped: function (job) {
            appendRunOutput('Execution stopped.', 'warning');
            outputLog.add('Execution stopped', job.runtime + ' · ' + job.path, 'warning');
          }
        }
      });

      if (runtimeSelect) {
        const browserRuntimes = root.RuntimeRegistry.all().filter(function (runtime) { return runtime.status === 'available'; });
        runtimeSelect.innerHTML = browserRuntimes.map(function (runtime) {
          return '<option value="' + escapeHtml(runtime.id) + '">' + escapeHtml(runtime.label) + '</option>';
        }).join('');
        runtimeSelect.value = runtimeManager.getSelectedRuntime();
        runtimeSelect.addEventListener('change', function () {
          const runtime = runtimeSelect.value;
          runtimeManager.setSelectedRuntime(runtime);
          session.set('runtime', runtime);
          updateRuntimeStatus({ runtime: runtime, status: 'idle', detail: 'Loads on Run' });
          refreshRunnableFiles();
          if (!terminalOnly) openRuntimeStarter(runtime).catch(function (error) { appendRunOutput(error.message || String(error), 'error'); });
        });
      }

      let editorPath = session.get('activeFile') || starterFiles[runtimeManager.getSelectedRuntime()];
      if (!fileSystem.exists(editorPath) || !root.RuntimeManager.detectRuntime(editorPath)) editorPath = starterFiles[runtimeManager.getSelectedRuntime()];
      if (fileSystem.exists(editorPath)) editor.open(editorPath);

      terminal = root.Terminal.create({
        fileSystem: fileSystem,
        session: session,
        outputElement: studio.querySelector('[data-scwb-terminal-output]'),
        input: studio.querySelector('[data-scwb-terminal-input]'),
        promptElement: studio.querySelector('[data-scwb-terminal-prompt]'),
        editor: editor,
        outputLog: outputLog,
        runtimeManager: runtimeManager,
        activatePanel: function (name) { activatePanel(name === 'charts' ? 'results' : name); },
        refreshFiles: refreshFiles,
        terminalOnly: terminalOnly
      });
      terminal.welcome();
      updateRuntimeStatus({ runtime: runtimeManager.getSelectedRuntime(), status: 'idle', detail: terminalOnly ? 'Loads on demand' : 'Loads on Run' });
      refreshFiles();

      studio.addEventListener('click', function (event) {
        const openPath = event.target && event.target.dataset ? event.target.dataset.scwbOpenFile : '';
        if (openPath) {
          openFile(openPath).then(function () { activatePanel('code'); }).catch(function (error) { appendRunOutput(error.message || String(error), 'error'); });
          return;
        }
        if (event.target && event.target.matches('[data-scwb-terminal-focus]')) terminal.focus();
        if (event.target && event.target.matches('[data-scwb-code-export]')) terminal.execute('export');
        if (event.target && event.target.matches('[data-scwb-output-clear]')) outputLog.clear();
        if (event.target && event.target.matches('[data-scwb-chart-clear]')) chartRenderer.clear();
      });

      if (fileSelect) fileSelect.addEventListener('change', function () {
        openFile(fileSelect.value).catch(function (error) { appendRunOutput(error.message || String(error), 'error'); });
      });
      if (loadButton) loadButton.addEventListener('click', function () {
        const runtime = runtimeSelect ? runtimeSelect.value : runtimeManager.getSelectedRuntime();
        appendRunOutput('Preparing ' + runtime + ' runtime…', 'system');
        runtimeManager.load(runtime).then(function (info) {
          appendRunOutput((info.id || runtime) + ' is ready.', 'success');
        }).catch(function (error) {
          appendRunOutput(error.message || String(error), 'error');
        });
      });
      if (runButton) runButton.addEventListener('click', function () {
        runActiveFile().catch(function () {});
      });
      if (stopButton) stopButton.addEventListener('click', function () {
        if (!runtimeManager.stop()) appendRunOutput('No active execution job.', 'system');
      });
      if (runClear) runClear.addEventListener('click', function () {
        clearRunOutput('Output cleared. Click Run to execute the open file.');
        setRunState('Ready', 'idle');
      });
      if (editorTextarea) editorTextarea.addEventListener('keydown', function (event) {
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
          event.preventDefault();
          runActiveFile().catch(function () {});
        }
      });

      const createForm = studio.querySelector('[data-scwb-code-create-form]');
      if (createForm) {
        createForm.addEventListener('submit', function (event) {
          event.preventDefault();
          const formData = new FormData(createForm);
          const type = formData.get('type');
          const path = fileSystem.resolvePath('/', formData.get('path'));
          const action = type === 'directory' ? fileSystem.mkdir(path) : fileSystem.touch(path);
          Promise.resolve(action).then(function () {
            createForm.reset();
            refreshFiles();
            outputLog.add(type === 'directory' ? 'Directory created' : 'File created', path, 'success');
          }).catch(function (error) {
            outputLog.add('Create failed', error.message || String(error), 'error');
          });
        });
      }

      activatePanel(terminalOnly ? 'terminal' : 'code');
      clearRunOutput(terminalOnly ? '' : 'Type or paste code, then click Run.');
    }).catch(function (error) {
      const output = runOutput || studio.querySelector('[data-scwb-terminal-output]');
      if (output) output.textContent = 'Code Studio could not initialize browser storage: ' + (error.message || error);
    });
  }

  function initAll() {
    document.querySelectorAll('[data-scwb-code-studio]').forEach(initStudio);
  }

  document.addEventListener('DOMContentLoaded', initAll);
  root.initAll = initAll;
})(window, document);
