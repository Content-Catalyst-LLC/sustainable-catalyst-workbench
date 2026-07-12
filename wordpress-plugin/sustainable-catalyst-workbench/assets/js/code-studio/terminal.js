(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function parseCommand(source) {
    const tokens = [];
    let current = '';
    let quote = '';
    let escaped = false;
    String(source || '').trim().split('').forEach(function (character) {
      if (escaped) {
        current += character;
        escaped = false;
        return;
      }
      if (character === '\\') {
        escaped = true;
        return;
      }
      if (quote) {
        if (character === quote) quote = '';
        else current += character;
        return;
      }
      if (character === '"' || character === "'") {
        quote = character;
        return;
      }
      if (/\s/.test(character)) {
        if (current) { tokens.push(current); current = ''; }
        return;
      }
      current += character;
    });
    if (current) tokens.push(current);
    return tokens;
  }

  function createTerminal(options) {
    const fileSystem = options.fileSystem;
    const session = options.session;
    const outputElement = options.outputElement;
    const input = options.input;
    const promptElement = options.promptElement;
    const editor = options.editor;
    const outputLog = options.outputLog;
    const runtimeManager = options.runtimeManager;
    const activatePanel = options.activatePanel || function () {};
    const refreshFiles = options.refreshFiles || function () {};
    const terminalOnly = !!options.terminalOnly;
    let historyIndex = (session.get('history') || []).length;

    function write(text, type) {
      if (!outputElement) return;
      const line = document.createElement('div');
      line.className = 'scwb-terminal-line scwb-terminal-line-' + (type || 'output');
      line.textContent = String(text == null ? '' : text);
      outputElement.appendChild(line);
      outputElement.scrollTop = outputElement.scrollHeight;
    }

    function writeBlock(text, type) {
      String(text == null ? '' : text).split('\n').forEach(function (line) { write(line, type); });
    }

    function clear() {
      if (outputElement) outputElement.innerHTML = '';
    }

    function updatePrompt() {
      const cwd = session.get('cwd') || '/';
      if (promptElement) promptElement.textContent = 'workbench@browser:' + (cwd === '/' ? '~' : cwd) + '$';
    }

    function resolve(path) {
      return fileSystem.resolvePath(session.get('cwd') || '/', path || '.');
    }

    function formatList(items) {
      if (!items.length) return '';
      return items.map(function (item) {
        const suffix = item.type === 'directory' ? '/' : '';
        return (item.type === 'directory' ? '[dir]  ' : '[file] ') + item.name + suffix;
      }).join('\n');
    }

    function exportProject(name) {
      const project = fileSystem.getProject();
      const filename = String(name || project.name || 'workbench-project').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '.json';
      root.Editor.download(filename, fileSystem.exportProject(), 'application/json;charset=utf-8');
      write('Exported browser project: ' + filename, 'success');
      outputLog.add('Project exported', filename, 'success');
    }

    function helpText() {
      return [
        'Workbench browser terminal commands',
        '',
        'help                          Show this command list',
        'clear                         Clear the terminal display',
        'history                       Show command history',
        'pwd                           Show the current project directory',
        'ls [path]                     List files and directories',
        'cd [path]                     Change project directory',
        'cat <file>                    Print a file',
        'edit <file>                   Open a file in the editor',
        'touch <file>                  Create an empty file',
        'mkdir <directory>             Create a directory',
        'rm [-r] <path>                Remove a file or directory',
        'echo <text>                   Print text',
        'echo <text> > file            Write text to a file',
        'files                         List every file in the project',
        'download <file>               Download one file',
        'export [name]                 Export the browser project as JSON',
        '',
        'runtime [id]                  Show or select javascript, python, r, or sql',
        'runtime load [id]             Download and initialize a runtime',
        'runtime reset [id]            Release a runtime and its memory',
        'runtimes                      Show all current and roadmap runtimes',
        'packages [id]                 Show approved browser packages',
        'run <file>                    Run by file extension',
        'run --runtime <id> <file>     Run with an explicit runtime',
        'node <file.js>                Run JavaScript',
        'python <file.py>              Run Python through Pyodide',
        'Rscript <file.R>              Run R through webR',
        'duckdb <file.sql>             Run SQL through DuckDB-Wasm',
        'stop                          Stop or interrupt the active job',
        'status                        Show browser runtime status and limits',
        'reset                         Restore the default browser project',
        '',
        'Keyboard: Up/Down history, Ctrl+L clear, Ctrl+C stop, Ctrl/Cmd+S save.'
      ].join('\n');
    }

    function findRunTarget(parts) {
      let runtime = '';
      let path = '';
      if (parts[0] === '--runtime' || parts[0] === '-r') {
        runtime = String(parts[1] || '').toLowerCase();
        path = parts[2] || '';
      } else {
        path = parts[0] || '';
      }
      if (!path) {
        const active = editor && editor.getActivePath ? editor.getActivePath() : '';
        path = active || '';
      }
      if (!path) throw new Error('Usage: run [--runtime javascript|python|r|sql] <file>');
      return { runtime: runtime, path: resolve(path) };
    }

    function runFile(path, runtime) {
      if (!runtimeManager) throw new Error('Browser runtime manager is unavailable.');
      if (!fileSystem.exists(path)) throw new Error('File not found: ' + path);
      const node = fileSystem.stat(path);
      if (!node || node.type !== 'file') throw new Error('Not a file: ' + path);
      write('Starting ' + (runtime || runtimeManager.detectRuntime(path) || 'selected') + ' runtime for ' + path + '…', 'system');
      outputLog.add('Execution started', path + (runtime ? ' [' + runtime + ']' : ''), 'info');
      return runtimeManager.run(path, runtime).then(function (result) {
        if (result.ok) {
          write('Execution completed in ' + (result.durationMs || 0) + ' ms.', 'success');
          outputLog.add('Execution completed', path + ' · ' + (result.durationMs || 0) + ' ms', 'success');
          if ((result.tables || []).length || (result.charts || []).length) {
            write('Structured results are available in the Charts panel.', 'info');
            if (!terminalOnly) activatePanel('charts');
          }
          if ((result.artifacts || []).length) {
            write((result.artifacts || []).length + ' artifact(s) written to the browser project output directory.', 'info');
            refreshFiles();
          }
        } else {
          write(result.error || 'Execution failed.', result.stopped ? 'warning' : 'error');
          outputLog.add(result.stopped ? 'Execution stopped' : 'Execution failed', result.error || path, result.stopped ? 'warning' : 'error');
        }
        return result;
      });
    }

    function runtimeCommand(parts) {
      const action = String(parts[0] || '').toLowerCase();
      if (!action) {
        write('Selected runtime: ' + runtimeManager.getSelectedRuntime());
        write('Use runtime load <id>, runtime <id>, or runtime reset <id>.');
        return Promise.resolve();
      }
      if (action === 'load') {
        const id = String(parts[1] || runtimeManager.getSelectedRuntime()).toLowerCase();
        runtimeManager.setSelectedRuntime(id);
        write('Loading ' + id + ' runtime. The first download may be large…', 'system');
        return runtimeManager.load(id).then(function (info) {
          write((info.id || id) + ' ready' + (info.version ? ': ' + info.version : '') + '.', 'success');
        });
      }
      if (action === 'reset') {
        const id = String(parts[1] || runtimeManager.getSelectedRuntime()).toLowerCase();
        runtimeManager.reset(id);
        write('Runtime reset: ' + id, 'success');
        return Promise.resolve();
      }
      if (runtimeManager.available().indexOf(action) < 0) throw new Error('Browser runtime not found: ' + action);
      runtimeManager.setSelectedRuntime(action);
      write('Selected runtime: ' + action + '. It will load lazily on first run.', 'success');
      return Promise.resolve();
    }

    function execute(source) {
      const commandLine = String(source || '').trim();
      if (!commandLine) return Promise.resolve();
      session.addHistory(commandLine);
      historyIndex = (session.get('history') || []).length;
      write((promptElement ? promptElement.textContent : '$') + ' ' + commandLine, 'command');
      const parts = parseCommand(commandLine);
      const rawCommand = parts.shift() || '';
      const command = rawCommand.toLowerCase();

      try {
        if (command === 'help') writeBlock(helpText());
        else if (command === 'clear') clear();
        else if (command === 'history') writeBlock((session.get('history') || []).map(function (item, index) { return String(index + 1).padStart(3, ' ') + '  ' + item; }).join('\n'));
        else if (command === 'pwd') write(session.get('cwd') || '/');
        else if (command === 'ls') writeBlock(formatList(fileSystem.list(resolve(parts[0] || '.'))) || '(empty)');
        else if (command === 'cd') {
          const destination = resolve(parts[0] || '/');
          const node = fileSystem.stat(destination);
          if (!node || node.type !== 'directory') throw new Error('Not a directory: ' + destination);
          session.set('cwd', destination);
          updatePrompt();
        }
        else if (command === 'cat') {
          if (!parts[0]) throw new Error('Usage: cat <file>');
          writeBlock(fileSystem.read(resolve(parts[0])));
        }
        else if (command === 'edit') {
          if (!parts[0]) throw new Error('Usage: edit <file>');
          const path = resolve(parts[0]);
          if (!fileSystem.exists(path)) return fileSystem.touch(path).then(function () {
            refreshFiles();
            if (terminalOnly) write('File created. Open the full Code Studio shortcode to use the editor: ' + path, 'info');
            else { editor.open(path); activatePanel('editor'); write('Opened in editor: ' + path, 'success'); }
          });
          if (terminalOnly) write('Use the full Code Studio interface to edit: ' + path, 'info');
          else { editor.open(path); activatePanel('editor'); write('Opened in editor: ' + path, 'success'); }
        }
        else if (command === 'touch') {
          if (!parts[0]) throw new Error('Usage: touch <file>');
          return fileSystem.touch(resolve(parts[0])).then(function () { refreshFiles(); write('Created file: ' + resolve(parts[0]), 'success'); });
        }
        else if (command === 'mkdir') {
          if (!parts[0]) throw new Error('Usage: mkdir <directory>');
          return fileSystem.mkdir(resolve(parts[0])).then(function () { refreshFiles(); write('Created directory: ' + resolve(parts[0]), 'success'); });
        }
        else if (command === 'rm') {
          const recursive = parts[0] === '-r' || parts[0] === '-rf';
          const target = recursive ? parts[1] : parts[0];
          if (!target) throw new Error('Usage: rm [-r] <path>');
          const path = resolve(target);
          return fileSystem.remove(path, recursive).then(function () { refreshFiles(); write('Removed: ' + path, 'success'); });
        }
        else if (command === 'echo') {
          const redirectIndex = parts.indexOf('>');
          if (redirectIndex >= 0) {
            const text = parts.slice(0, redirectIndex).join(' ');
            const target = parts[redirectIndex + 1];
            if (!target) throw new Error('Usage: echo <text> > <file>');
            const path = resolve(target);
            return fileSystem.write(path, text + '\n').then(function () { refreshFiles(); write('Wrote file: ' + path, 'success'); });
          }
          write(parts.join(' '));
        }
        else if (command === 'files') writeBlock(fileSystem.allFiles().join('\n') || '(no files)');
        else if (command === 'download') {
          if (!parts[0]) throw new Error('Usage: download <file>');
          const path = resolve(parts[0]);
          root.Editor.download(fileSystem.basename(path), fileSystem.read(path), 'text/plain;charset=utf-8');
          write('Downloaded: ' + path, 'success');
        }
        else if (command === 'export') exportProject(parts[0]);
        else if (command === 'status') {
          const project = fileSystem.getProject();
          const manifest = root.RuntimeRegistry.manifest();
          const limits = manifest.limits || {};
          const active = runtimeManager && runtimeManager.getActiveJob();
          writeBlock([
            'Sustainable Catalyst Workbench Code Studio v1.9.1',
            'Project: ' + project.name,
            'Storage: ' + fileSystem.getStorageMode(),
            'Files: ' + fileSystem.allFiles().length,
            'Selected runtime: ' + (runtimeManager ? runtimeManager.getSelectedRuntime() : 'unavailable'),
            'Active job: ' + (active ? active.runtime + ' ' + active.path : 'none'),
            'Execution timeout: ' + (limits.executionTimeoutMs || 15000) + ' ms',
            'Maximum source: ' + (limits.maxSourceBytes || 262144) + ' bytes',
            'Project upload: disabled',
            'FastAPI code execution: disabled',
            'Local Go runner: planned for v2.0.0'
          ].join('\n'));
        }
        else if (command === 'runtimes') writeBlock(root.RuntimeRegistry.formatTable());
        else if (command === 'packages') writeBlock(root.RuntimeRegistry.packageText(String(parts[0] || runtimeManager.getSelectedRuntime()).toLowerCase()));
        else if (command === 'runtime') return runtimeCommand(parts);
        else if (command === 'run') {
          const target = findRunTarget(parts);
          return runFile(target.path, target.runtime);
        }
        else if (command === 'node' || command === 'javascript' || command === 'js') {
          if (!parts[0]) throw new Error('Usage: node <file.js>');
          return runFile(resolve(parts[0]), 'javascript');
        }
        else if (command === 'python' || command === 'python3' || command === 'py') {
          if (!parts[0]) throw new Error('Usage: python <file.py>');
          return runFile(resolve(parts[0]), 'python');
        }
        else if (rawCommand === 'Rscript' || command === 'rscript' || command === 'r') {
          if (!parts[0]) throw new Error('Usage: Rscript <file.R>');
          return runFile(resolve(parts[0]), 'r');
        }
        else if (command === 'duckdb' || command === 'sql') {
          if (!parts[0]) throw new Error('Usage: duckdb <file.sql>');
          return runFile(resolve(parts[0]), 'sql');
        }
        else if (command === 'stop') {
          if (runtimeManager && runtimeManager.stop()) write('Stop signal sent to the active browser runtime.', 'warning');
          else write('No active execution job.', 'info');
        }
        else if (command === 'reset') {
          if (runtimeManager && runtimeManager.isRunning()) runtimeManager.stop();
          return fileSystem.reset().then(function () {
            session.reset();
            refreshFiles();
            updatePrompt();
            if (!terminalOnly) editor.open('/README.md');
            write('Browser project reset to the v1.9.1 editor-first starter project.', 'success');
            outputLog.add('Project reset', 'Default browser runtime project restored.', 'success');
          });
        }
        else if (command === 'whoami') write('workbench');
        else if (command === 'version') write('Sustainable Catalyst Workbench Code Studio v1.9.1');
        else throw new Error('Command not found: ' + rawCommand + '. Type help.');
      } catch (error) {
        write(error.message || String(error), 'error');
        outputLog.add('Terminal error', error.message || String(error), 'error');
      }
      return Promise.resolve();
    }

    function safeExecute(source) {
      return Promise.resolve(execute(source)).catch(function (error) {
        write(error.message || String(error), 'error');
        outputLog.add('Terminal error', error.message || String(error), 'error');
      });
    }

    function welcome() {
      writeBlock([
        'SUSTAINABLE CATALYST WORKBENCH',
        'Browser Code Studio v1.9.1',
        'Runtimes: JavaScript · Python · R · SQL',
        'Storage: local browser project',
        'Execution: browser workers and WebAssembly',
        '',
        'Type help for commands. Try: run src/main.js'
      ].join('\n'), 'system');
    }

    if (input) {
      input.addEventListener('keydown', function (event) {
        const history = session.get('history') || [];
        if (event.key === 'Enter') {
          event.preventDefault();
          const command = input.value;
          input.value = '';
          safeExecute(command).finally(function () { input.focus(); });
        } else if (event.key === 'ArrowUp') {
          event.preventDefault();
          if (history.length) {
            historyIndex = Math.max(0, historyIndex - 1);
            input.value = history[historyIndex] || '';
            input.setSelectionRange(input.value.length, input.value.length);
          }
        } else if (event.key === 'ArrowDown') {
          event.preventDefault();
          if (history.length) {
            historyIndex = Math.min(history.length, historyIndex + 1);
            input.value = historyIndex >= history.length ? '' : history[historyIndex];
          }
        } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'l') {
          event.preventDefault();
          clear();
        } else if (event.ctrlKey && event.key.toLowerCase() === 'c') {
          event.preventDefault();
          if (runtimeManager && runtimeManager.stop()) write('^C Stop signal sent.', 'warning');
          else write('^C No active execution job.', 'info');
        }
      });
    }

    updatePrompt();

    return {
      execute: safeExecute,
      write: write,
      writeBlock: writeBlock,
      clear: clear,
      welcome: welcome,
      focus: function () { if (input) input.focus(); },
      updatePrompt: updatePrompt
    };
  }

  root.Terminal = { create: createTerminal, parseCommand: parseCommand };
})(window);
