(function () {
  'use strict';
  function ready() {
    document.querySelectorAll('[data-scwb-v301-runtime-status]').forEach(function (node) {
      var router = window.SCWBPrimaryRouter;
      var expected = router && router.expectedStudios ? router.expectedStudios.length : 0;
      node.textContent = router
        ? 'Browser activation passed · ' + expected + ' studio routes available · Workbench v3.0.2 JavaScript loaded.'
        : 'Primary router unavailable · reinstall the complete Workbench v3.0.1 plugin.';
      node.classList.toggle('is-ok', !!router);
      node.classList.toggle('is-error', !router);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
