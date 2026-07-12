(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};
  const PREFIX = 'scwb_code_studio_session_';

  function createSession(projectId) {
    const key = PREFIX + projectId;
    let state = {
      cwd: '/',
      activeFile: '/src/main.js',
      history: [],
      activePanel: 'code'
    };

    try {
      const saved = window.localStorage.getItem(key);
      if (saved) state = Object.assign(state, JSON.parse(saved));
    } catch (error) {
      // Session persistence is optional; project storage remains independent.
    }

    function save() {
      try { window.localStorage.setItem(key, JSON.stringify(state)); } catch (error) {}
    }

    return {
      get: function (name) { return state[name]; },
      set: function (name, value) { state[name] = value; save(); return value; },
      addHistory: function (command) {
        const value = String(command || '').trim();
        if (!value) return;
        if (state.history[state.history.length - 1] !== value) state.history.push(value);
        if (state.history.length > 100) state.history = state.history.slice(-100);
        save();
      },
      reset: function () {
        state = { cwd: '/', activeFile: '/src/main.js', history: [], activePanel: 'code' };
        save();
      },
      snapshot: function () { return Object.assign({}, state, { history: state.history.slice() }); }
    };
  }

  root.Session = { create: createSession };
})(window);
