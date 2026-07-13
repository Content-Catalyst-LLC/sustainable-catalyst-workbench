<?php
/**
 * Plugin Name: Sustainable Catalyst Prototyping Workbench
 * Version: 3.0.1
 */
if (!defined('ABSPATH')) { exit; }
define('SCWB_VERSION', '3.0.1');

// Workbench v2.0.0 — Go Runner, Research Lab, and Hardware Studio Foundation.
if (!defined('SCWB_V200_PLUGIN_FILE')) {
    define('SCWB_V200_PLUGIN_FILE', __FILE__);
}
require_once __DIR__ . '/includes/scwb-v200-foundation.php';

// Workbench v2.1.0 — Raspberry Pi, TinyML, and Embedded Device Studio.
if (!defined('SCWB_V210_PLUGIN_FILE')) {
    define('SCWB_V210_PLUGIN_FILE', __FILE__);
}
require_once __DIR__ . '/includes/scwb-v210-embedded-studio.php';

// Workbench v2.2.0 — FPGA, Electronics Design, and Hardware Validation Studio.
if (!defined('SCWB_V220_PLUGIN_FILE')) {
    define('SCWB_V220_PLUGIN_FILE', __FILE__);
}
require_once __DIR__ . '/includes/scwb-v220-hardware-validation.php';

// Workbench v2.3.0 — Robotics, Controls, and Mechatronics Studio.
if (!defined('SCWB_V230_PLUGIN_FILE')) { define('SCWB_V230_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v230-robotics-controls.php';

// Workbench v2.4.0 — Instrumentation, Data Acquisition, and Signal Analysis Studio.
if (!defined('SCWB_V240_PLUGIN_FILE')) { define('SCWB_V240_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v240-instrumentation.php';

// Workbench v2.5.0 — Simulation, Digital Twin, and Systems Modeling Studio.
if (!defined('SCWB_V250_PLUGIN_FILE')) { define('SCWB_V250_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v250-simulation-digital-twin.php';

// Workbench v2.6.0 — Multi-Language Engineering Runtime Studio.
if (!defined('SCWB_V260_PLUGIN_FILE')) { define('SCWB_V260_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v260-multilanguage-runtime.php';

// Workbench v2.7.0 — Scientific Visualization and Engineering Dashboard Studio.
if (!defined('SCWB_V270_PLUGIN_FILE')) { define('SCWB_V270_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v270-visualization-dashboard.php';

// Workbench v2.8.0 — Experiment Automation and Reproducible Workflow Studio.
if (!defined('SCWB_V280_PLUGIN_FILE')) { define('SCWB_V280_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v280-experiment-automation.php';

// Workbench v2.9.0 — Technical Documentation and Product Dossier Studio.
if (!defined('SCWB_V290_PLUGIN_FILE')) { define('SCWB_V290_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v290-documentation-dossier.php';


// Workbench v3.0.0 — Unified Prototyping Workbench.
if (!defined('SCWB_V300_PLUGIN_FILE')) { define('SCWB_V300_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v300-unified-workbench.php';

// Workbench v3.0.1 — Production activation, diagnostics, and interface reliability.
if (!defined('SCWB_V301_PLUGIN_FILE')) { define('SCWB_V301_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v301-production-reliability.php';

// Canonical primary shortcode and unified studio selector.
require_once __DIR__ . '/includes/scwb-primary-shortcode.php';
