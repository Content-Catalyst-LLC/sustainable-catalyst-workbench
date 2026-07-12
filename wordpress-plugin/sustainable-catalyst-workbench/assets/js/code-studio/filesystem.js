(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};
  const DB_NAME = 'sc_workbench_code_studio';
  const DB_VERSION = 1;
  const STORE_NAME = 'projects';
  const FALLBACK_PREFIX = 'scwb_code_studio_project_';

  function nowIso() {
    return new Date().toISOString();
  }

  function normalizePath(path) {
    const source = String(path || '/').replace(/\\/g, '/');
    const parts = [];
    source.split('/').forEach(function (part) {
      if (!part || part === '.') return;
      if (part === '..') {
        parts.pop();
        return;
      }
      parts.push(part);
    });
    return '/' + parts.join('/');
  }

  function dirname(path) {
    const normalized = normalizePath(path);
    if (normalized === '/') return '/';
    const parts = normalized.split('/');
    parts.pop();
    return normalizePath(parts.join('/') || '/');
  }

  function basename(path) {
    const normalized = normalizePath(path);
    if (normalized === '/') return '/';
    return normalized.split('/').pop();
  }

  function resolvePath(cwd, path) {
    const raw = String(path || '').trim();
    if (!raw) return normalizePath(cwd || '/');
    return raw.charAt(0) === '/' ? normalizePath(raw) : normalizePath((cwd || '/') + '/' + raw);
  }

  function defaultProject(id) {
    const timestamp = nowIso();
    return {
      id: id,
      name: 'Workbench Browser Project',
      version: '1.9.1',
      createdAt: timestamp,
      updatedAt: timestamp,
      files: {
        '/': { type: 'directory', createdAt: timestamp, updatedAt: timestamp },
        '/README.md': {
          type: 'file',
          language: 'markdown',
          content: '# Sustainable Catalyst Workbench Browser Project\n\nWorkbench v1.9.1 uses an editor-first browser lab: choose a language, type or paste code, and click Run. Project files remain in browser storage unless you explicitly download or export them.\n\n## Run code\n\nOpen a starter file, edit the code, and click Run. Use Ctrl/Command + Enter as a keyboard shortcut.\n',
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/src': { type: 'directory', createdAt: timestamp, updatedAt: timestamp },
        '/src/main.js': {
          type: 'file',
          language: 'javascript',
          content: 'const values = [12, 18, 25, 31];\nconsole.log("Mean:", values.reduce((a, b) => a + b, 0) / values.length);\nworkbench.table("Values", values.map((value, index) => ({ period: index + 1, value })));\nworkbench.chart("Values by period", { type: "line", x: [1, 2, 3, 4], y: values });\n',
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/src/analysis.py': {
          type: 'file',
          language: 'python',
          content: 'import statistics\nimport workbench\n\nvalues = [12, 18, 25, 31]\nprint("Mean:", statistics.mean(values))\nworkbench.table("Python values", [{"period": i + 1, "value": value} for i, value in enumerate(values)])\nworkbench.chart("Python values by period", {"type": "line", "x": [1, 2, 3, 4], "y": values})\n',
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/src/analysis.R': {
          type: 'file',
          language: 'r',
          content: 'values <- c(12, 18, 25, 31)\nprint(mean(values))\nplot(values, type = "b", main = "Values by period", xlab = "Period", ylab = "Value")\n',
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/src/query.sql': {
          type: 'file',
          language: 'sql',
          content: "SELECT period, value, value - LAG(value) OVER (ORDER BY period) AS change\nFROM read_csv_auto('data/example.csv')\nORDER BY period;\n",
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/data': { type: 'directory', createdAt: timestamp, updatedAt: timestamp },
        '/data/example.csv': {
          type: 'file',
          language: 'csv',
          content: 'period,value\n1,12\n2,18\n3,25\n',
          createdAt: timestamp,
          updatedAt: timestamp
        },
        '/tests': { type: 'directory', createdAt: timestamp, updatedAt: timestamp },
        '/output': { type: 'directory', createdAt: timestamp, updatedAt: timestamp }
      }
    };
  }


  function upgradeProject(project) {
    if (!project || !project.files) return project;
    if (project.version === '1.9.1') return project;
    const stamp = nowIso();
    const additions = defaultProject(project.id || 'default');
    ['/src/analysis.py', '/src/analysis.R', '/src/query.sql'].forEach(function (path) {
      if (!project.files[path]) project.files[path] = additions.files[path];
    });
    if (!project.files['/README-v1.9.1.md']) {
      project.files['/README-v1.9.1.md'] = {
        type: 'file',
        language: 'markdown',
        content: '# Workbench v1.9.1 Editor-First Run Experience\n\nChoose a language, edit its starter file, and click Run. The advanced terminal remains available as an optional console. Existing project files were preserved during the upgrade.\n',
        createdAt: stamp,
        updatedAt: stamp
      };
    }
    project.version = '1.9.1';
    project.updatedAt = stamp;
    return project;
  }

  function openDb() {
    return new Promise(function (resolve, reject) {
      if (!('indexedDB' in window)) {
        reject(new Error('IndexedDB unavailable'));
        return;
      }
      const request = window.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = function () {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error || new Error('Unable to open IndexedDB')); };
    });
  }

  function indexedDbGet(id) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        const transaction = db.transaction(STORE_NAME, 'readonly');
        const request = transaction.objectStore(STORE_NAME).get(id);
        request.onsuccess = function () { resolve(request.result || null); };
        request.onerror = function () { reject(request.error || new Error('Unable to read browser project')); };
        transaction.oncomplete = function () { db.close(); };
      });
    });
  }

  function indexedDbPut(project) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        const transaction = db.transaction(STORE_NAME, 'readwrite');
        transaction.objectStore(STORE_NAME).put(project);
        transaction.oncomplete = function () { db.close(); resolve(project); };
        transaction.onerror = function () { reject(transaction.error || new Error('Unable to save browser project')); };
      });
    });
  }

  function fallbackGet(id) {
    try {
      const raw = window.localStorage.getItem(FALLBACK_PREFIX + id);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      return null;
    }
  }

  function fallbackPut(project) {
    window.localStorage.setItem(FALLBACK_PREFIX + project.id, JSON.stringify(project));
    return project;
  }

  function createFileSystem(projectId) {
    let project = null;
    let storageMode = 'indexeddb';

    function persist() {
      project.updatedAt = nowIso();
      return indexedDbPut(project).catch(function () {
        storageMode = 'localstorage';
        return fallbackPut(project);
      });
    }

    function ensureParentDirectories(path) {
      let current = dirname(path);
      const pending = [];
      while (current !== '/' && !project.files[current]) {
        pending.push(current);
        current = dirname(current);
      }
      pending.reverse().forEach(function (directory) {
        const stamp = nowIso();
        project.files[directory] = { type: 'directory', createdAt: stamp, updatedAt: stamp };
      });
      if (!project.files['/']) {
        const stamp = nowIso();
        project.files['/'] = { type: 'directory', createdAt: stamp, updatedAt: stamp };
      }
    }

    return {
      init: function () {
        return indexedDbGet(projectId).then(function (stored) {
          project = upgradeProject(stored || defaultProject(projectId));
          return stored ? persist() : persist();
        }).catch(function () {
          storageMode = 'localstorage';
          project = upgradeProject(fallbackGet(projectId) || defaultProject(projectId));
          fallbackPut(project);
          return project;
        });
      },
      getStorageMode: function () { return storageMode; },
      getProject: function () { return project; },
      normalizePath: normalizePath,
      resolvePath: resolvePath,
      dirname: dirname,
      basename: basename,
      exists: function (path) {
        return !!project.files[normalizePath(path)];
      },
      stat: function (path) {
        return project.files[normalizePath(path)] || null;
      },
      list: function (path) {
        const directory = normalizePath(path || '/');
        const node = project.files[directory];
        if (!node || node.type !== 'directory') throw new Error('Not a directory: ' + directory);
        return Object.keys(project.files).filter(function (candidate) {
          if (candidate === directory) return false;
          return dirname(candidate) === directory;
        }).map(function (candidate) {
          const item = project.files[candidate];
          return {
            path: candidate,
            name: basename(candidate),
            type: item.type,
            size: item.type === 'file' ? String(item.content || '').length : 0,
            updatedAt: item.updatedAt || ''
          };
        }).sort(function (a, b) {
          if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
          return a.name.localeCompare(b.name);
        });
      },
      read: function (path) {
        const normalized = normalizePath(path);
        const node = project.files[normalized];
        if (!node) throw new Error('File not found: ' + normalized);
        if (node.type !== 'file') throw new Error('Not a file: ' + normalized);
        return String(node.content || '');
      },
      write: function (path, content, language) {
        const normalized = normalizePath(path);
        ensureParentDirectories(normalized);
        const previous = project.files[normalized];
        if (previous && previous.type === 'directory') throw new Error('Cannot overwrite directory: ' + normalized);
        const stamp = nowIso();
        project.files[normalized] = {
          type: 'file',
          language: language || (previous && previous.language) || '',
          content: String(content == null ? '' : content),
          createdAt: previous && previous.createdAt ? previous.createdAt : stamp,
          updatedAt: stamp
        };
        return persist().then(function () { return project.files[normalized]; });
      },
      touch: function (path) {
        const normalized = normalizePath(path);
        if (project.files[normalized] && project.files[normalized].type === 'directory') {
          throw new Error('Cannot touch a directory: ' + normalized);
        }
        const existing = project.files[normalized];
        return this.write(normalized, existing ? existing.content : '', existing ? existing.language : '');
      },
      mkdir: function (path) {
        const normalized = normalizePath(path);
        if (project.files[normalized]) throw new Error('Path already exists: ' + normalized);
        ensureParentDirectories(normalized);
        const stamp = nowIso();
        project.files[normalized] = { type: 'directory', createdAt: stamp, updatedAt: stamp };
        return persist();
      },
      remove: function (path, recursive) {
        const normalized = normalizePath(path);
        if (normalized === '/') throw new Error('The project root cannot be removed.');
        const node = project.files[normalized];
        if (!node) throw new Error('Path not found: ' + normalized);
        const descendants = Object.keys(project.files).filter(function (candidate) {
          return candidate.indexOf(normalized + '/') === 0;
        });
        if (node.type === 'directory' && descendants.length && !recursive) {
          throw new Error('Directory is not empty. Use rm -r ' + normalized);
        }
        descendants.forEach(function (candidate) { delete project.files[candidate]; });
        delete project.files[normalized];
        return persist();
      },
      reset: function () {
        project = defaultProject(projectId);
        return persist();
      },
      exportProject: function () {
        return JSON.stringify(project, null, 2);
      },
      allFiles: function () {
        return Object.keys(project.files).filter(function (path) {
          return project.files[path].type === 'file';
        }).sort();
      }
    };
  }

  root.FileSystem = {
    create: createFileSystem,
    normalizePath: normalizePath,
    resolvePath: resolvePath,
    dirname: dirname,
    basename: basename
  };
})(window);
