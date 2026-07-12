(function (window) {
  'use strict';

  const root = window.SCWBCodeStudio = window.SCWBCodeStudio || {};

  function download(name, content, type) {
    const blob = new Blob([content], { type: type || 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    document.body.appendChild(link);
    link.click();
    window.setTimeout(function () {
      URL.revokeObjectURL(link.href);
      link.remove();
    }, 300);
  }

  function createEditor(options) {
    const fileSystem = options.fileSystem;
    const session = options.session;
    const textarea = options.textarea;
    const pathLabel = options.pathLabel;
    const lineNumbers = options.lineNumbers;
    const statusLabel = options.statusLabel;
    const saveButton = options.saveButton;
    const downloadButton = options.downloadButton;
    const onSaved = options.onSaved || function () {};
    const onError = options.onError || function () {};
    let activePath = session.get('activeFile') || '/README.md';
    let dirty = false;

    function updateLineNumbers() {
      if (!lineNumbers || !textarea) return;
      const count = Math.max(1, String(textarea.value || '').split('\n').length);
      lineNumbers.textContent = Array.from({ length: count }, function (_, index) { return index + 1; }).join('\n');
      lineNumbers.scrollTop = textarea.scrollTop;
    }

    function setDirty(value) {
      dirty = !!value;
      if (statusLabel) statusLabel.textContent = dirty ? 'Unsaved changes' : 'Saved locally';
      if (saveButton) saveButton.disabled = !dirty;
    }

    function open(path) {
      const normalized = fileSystem.normalizePath(path);
      const content = fileSystem.read(normalized);
      activePath = normalized;
      session.set('activeFile', activePath);
      if (textarea) textarea.value = content;
      updateLineNumbers();
      if (pathLabel) pathLabel.textContent = activePath;
      setDirty(false);
      return activePath;
    }

    function save() {
      if (!activePath) throw new Error('No file is open.');
      return fileSystem.write(activePath, textarea ? textarea.value : '').then(function () {
        setDirty(false);
        onSaved(activePath);
        return activePath;
      });
    }

    if (textarea) {
      textarea.addEventListener('input', function () { setDirty(true); updateLineNumbers(); });
      textarea.addEventListener('scroll', function () { if (lineNumbers) lineNumbers.scrollTop = textarea.scrollTop; });
      textarea.addEventListener('keydown', function (event) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
          event.preventDefault();
          save().catch(onError);
        }
        if (event.key === 'Tab') {
          event.preventDefault();
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          textarea.value = textarea.value.slice(0, start) + '  ' + textarea.value.slice(end);
          textarea.selectionStart = textarea.selectionEnd = start + 2;
          setDirty(true);
          updateLineNumbers();
        }
      });
    }

    if (saveButton) saveButton.addEventListener('click', function () { save().catch(onError); });
    if (downloadButton) downloadButton.addEventListener('click', function () {
      if (!activePath) return;
      download(fileSystem.basename(activePath), textarea ? textarea.value : '', 'text/plain;charset=utf-8');
    });

    return {
      open: open,
      save: save,
      getActivePath: function () { return activePath; },
      isDirty: function () { return dirty; },
      getValue: function () { return textarea ? textarea.value : ''; },
      updateLineNumbers: updateLineNumbers,
      download: download
    };
  }

  root.Editor = { create: createEditor, download: download };
})(window);
