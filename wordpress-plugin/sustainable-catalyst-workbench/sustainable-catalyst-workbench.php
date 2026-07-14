<?php
/**
 * Plugin Name: Sustainable Catalyst Prototyping Workbench
 * Version: 4.2.0
 */
if (!defined('ABSPATH')) { exit; }
define('SCWB_VERSION', '4.2.0');

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


// Workbench v3.0.2 — Project Migration, Storage, and Recovery.
if (!defined('SCWB_V302_PLUGIN_FILE')) { define('SCWB_V302_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v302-project-migration-recovery.php';

// Workbench v3.1.0 — Persistent Project Workspace.
if (!defined('SCWB_V310_PLUGIN_FILE')) { define('SCWB_V310_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v310-persistent-project-workspace.php';


// Workbench v3.2.0 — Knowledge Library and Article Integration.
if (!defined('SCWB_V320_PLUGIN_FILE')) { define('SCWB_V320_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v320-knowledge-library-integration.php';


// Workbench v3.3.0 — Platform Handoffs and Shared Evidence.
// Workbench v3.3.1 — Embedded Studio Shortcode Display Repair.
if (!defined('SCWB_V330_PLUGIN_FILE')) { define('SCWB_V330_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v330-platform-handoffs.php';


// Workbench v3.4.0 — Collaboration, Review, and Technical Sign-Off.
if (!defined('SCWB_V340_PLUGIN_FILE')) { define('SCWB_V340_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v340-collaboration-review.php';


// Workbench v3.5.0 — Advanced Device and Instrument Orchestration.
if (!defined('SCWB_V350_PLUGIN_FILE')) { define('SCWB_V350_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v350-device-orchestration.php';


// Workbench v3.6.0 — Computational Intelligence and Predictive Analytics.
if (!defined('SCWB_V360_PLUGIN_FILE')) { define('SCWB_V360_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v360-computational-intelligence.php';


// Workbench v3.7.0 — Domain Laboratory Integration.
if (!defined('SCWB_V370_PLUGIN_FILE')) { define('SCWB_V370_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v370-domain-laboratory-integration.php';

// Workbench v3.8.0 — Offline and Installable Workbench.
if (!defined('SCWB_V380_PLUGIN_FILE')) { define('SCWB_V380_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v380-offline-installable-workbench.php';

// Workbench v3.9.0 — Production Evaluation and Public Release Hardening.
if (!defined('SCWB_V390_PLUGIN_FILE')) { define('SCWB_V390_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v390-production-hardening.php';



// Workbench v4.0.0 — Connected Scientific and Engineering Workbench.
if (!defined('SCWB_V400_PLUGIN_FILE')) { define('SCWB_V400_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v400-connected-workbench.php';

// Workbench v4.0.1 — Connected Environment Activation and Integration Reliability.
if (!defined('SCWB_V401_PLUGIN_FILE')) { define('SCWB_V401_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v401-connected-reliability.php';

// Workbench v4.0.2 — Project Graph, Synchronization, and Recovery Hardening.
if (!defined('SCWB_V402_PLUGIN_FILE')) { define('SCWB_V402_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v402-graph-sync-recovery.php';


// Workbench v4.1.0 — Hosted Collaborative Workspace and Authenticated Team Projects.
if (!defined('SCWB_V410_PLUGIN_FILE')) { define('SCWB_V410_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v410-team-workspace.php';

// Workbench v4.2.0 — Workflow Templates and Guided Scientific/Engineering Project Creation.
if (!defined('SCWB_V420_PLUGIN_FILE')) { define('SCWB_V420_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v420-guided-projects.php';

// Canonical primary shortcode and unified studio selector.
require_once __DIR__ . '/includes/scwb-primary-shortcode.php';
