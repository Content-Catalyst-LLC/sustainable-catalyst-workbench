<?php
/**
 * Plugin Name: Sustainable Catalyst Prototyping Workbench
 * Version: 8.2.0
 */
if (!defined('ABSPATH')) { exit; }
define('SCWB_VERSION', '8.2.0');

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

// Workbench v4.3.0 — Live Data Connectors and Reproducible Dataset Pipelines.
if (!defined('SCWB_V430_PLUGIN_FILE')) { define('SCWB_V430_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v430-data-pipelines.php';


// Workbench v4.4.0 — Automated Evaluation, Benchmarking, and Comparison Laboratory.
if (!defined('SCWB_V440_PLUGIN_FILE')) { define('SCWB_V440_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v440-evaluation-laboratory.php';

// Workbench v4.5.0 — Extension SDK, Plugin Registry, and Third-Party Module Framework.
if (!defined('SCWB_V450_PLUGIN_FILE')) { define('SCWB_V450_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v450-extension-framework.php';


// Workbench v5.0.0 — Sustainable Catalyst Integrated Research and Engineering Platform.
if (!defined('SCWB_V500_PLUGIN_FILE')) { define('SCWB_V500_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v500-integrated-platform.php';

// Workbench v5.1.0 — Universal Mathematics & CAS Engine Foundation.
if (!defined('SCWB_V510_PLUGIN_FILE')) { define('SCWB_V510_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v510-mathematics.php';

// Workbench v5.2.0 — Interactive Graph Mathematics.
if (!defined('SCWB_V520_PLUGIN_FILE')) { define('SCWB_V520_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v520-graph-mathematics.php';

// Workbench v5.3.0 — Computational Blackboard, Creative Mathematics & Physical Prototyping.
if (!defined('SCWB_V530_PLUGIN_FILE')) { define('SCWB_V530_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v530-blackboard-creative-prototyping.php';

// Workbench v5.3.1 — Settings & Backend Connection Repair.
if (!defined('SCWB_V531_PLUGIN_FILE')) { define('SCWB_V531_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v531-settings-backend-repair.php';

// Workbench v5.3.2 — Compact Computational Showcase, Advanced Graph Presentation & Workbench Experience Redesign.
if (!defined('SCWB_V532_PLUGIN_FILE')) { define('SCWB_V532_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v532-compact-showcase-experience.php';

// Workbench v5.3.3 — Homepage & Workbench Experience Integration Hardening.
if (!defined('SCWB_V533_PLUGIN_FILE')) { define('SCWB_V533_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v533-integration-hardening.php';

// Workbench v5.4.0 — Advanced Graph Mathematics II.
if (!defined('SCWB_V540_PLUGIN_FILE')) { define('SCWB_V540_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v540-advanced-graph-mathematics.php';

// Workbench v5.5.0 — Dynamic Geometry & Interactive Mathematics.
if (!defined('SCWB_V550_PLUGIN_FILE')) { define('SCWB_V550_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v550-dynamic-geometry.php';

// Workbench v5.6.0 — Numerical Methods & Scientific Computing.
if (!defined('SCWB_V560_PLUGIN_FILE')) { define('SCWB_V560_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v560-numerical-scientific-computing.php';

// Workbench v5.7.0 — Signals, Systems & Control Mathematics.
if (!defined('SCWB_V570_PLUGIN_FILE')) { define('SCWB_V570_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v570-signals-systems-control-mathematics.php';


// Workbench v5.8.0 — Electronics & Embedded Systems Studio.
if (!defined('SCWB_V580_PLUGIN_FILE')) { define('SCWB_V580_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v580-electronics-embedded-systems.php';

// Workbench v5.9.0 — FPGA, PYNQ & Digital Logic Workbench.
if (!defined('SCWB_V590_PLUGIN_FILE')) { define('SCWB_V590_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v590-fpga-pynq-digital-logic.php';


// Workbench v6.0.0 — Unified Computational Workbench.
if (!defined('SCWB_V600_PLUGIN_FILE')) { define('SCWB_V600_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v600-unified-computational-workbench.php';

// Canonical primary shortcode and unified studio selector.
require_once __DIR__ . '/includes/scwb-primary-shortcode.php';


// Workbench v6.0.1 — Unified Experience, Runtime Identity & Interface Hardening.
if (!defined('SCWB_V601_PLUGIN_FILE')) { define('SCWB_V601_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v601-unified-experience-hardening.php';


// Workbench v6.2.0 — Energy Workbench Runtime.
if (!defined('SCWB_V620_PLUGIN_FILE')) { define('SCWB_V620_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v620-energy-workbench-runtime.php';

// Workbench v6.3.0 — Grid, Storage & Reliability Analysis.
if (!defined('SCWB_V630_PLUGIN_FILE')) { define('SCWB_V630_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v630-grid-storage-reliability.php';


// Workbench v6.4.0 — Platform Core Connectivity Foundation.
if (!defined('SCWB_V640_PLUGIN_FILE')) { define('SCWB_V640_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v640-platform-core-connectivity.php';


// Workbench v6.5.0 — Unified Runtime Contract Adapter.
if (!defined('SCWB_V650_PLUGIN_FILE')) { define('SCWB_V650_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v650-unified-runtime-contract-adapter.php';

// Workbench v6.6.0 — Unified Research Project & Session Bridge.
require_once __DIR__ . '/includes/scwb-v660-unified-research-session-bridge.php';

// Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge.
require_once __DIR__ . '/includes/scwb-v670-computation-execution-lineage.php';


// Workbench v6.8.0 — Scenario & Uncertainty Compute Runtime Integration.
require_once __DIR__ . '/includes/scwb-v680-scenario-uncertainty-runtime.php';

// Workbench v6.9.0 — Core Visual Reasoning Runtime Adapter.
require_once __DIR__ . '/includes/scwb-v690-core-visual-reasoning-runtime.php';

// Workbench v6.10.0 — Predictive Intelligence Runtime Integration.
require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';

require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';

// Workbench v6.12.0 — Research State, Reproduction & Snapshot Integration.
require_once __DIR__ . '/includes/scwb-v6120-research-state-reproduction-snapshot.php';

// Workbench v6.13.0 — Core-Aware Workbench Experience.
require_once __DIR__ . '/includes/scwb-v6130-core-aware-experience.php';


// Workbench v6.14.0 — Platform Integration Certification.
require_once __DIR__ . '/includes/scwb-v6140-platform-integration-certification.php';


// Workbench v7.0.0 — Unified Scientific & Engineering Execution Runtime.
require_once __DIR__ . '/includes/scwb-v700-unified-execution-runtime.php';


// Workbench v7.1.0 — Unified Execution Object Model.
require_once __DIR__ . '/includes/scwb-v710-unified-execution-object-model.php';

// Workbench v7.2.0 — Scientific Runtime Orchestrator.
require_once __DIR__ . '/includes/scwb-v720-scientific-runtime-orchestrator.php';

// Workbench v7.3.0 — Dataset, Variable & Parameter Workspace.
require_once __DIR__ . '/includes/scwb-v730-data-variable-parameter-workspace.php';

// Workbench v7.4.0 — Numerical Methods & Solver Runtime.
require_once __DIR__ . '/includes/scwb-v740-numerical-methods-solver-runtime.php';


// Workbench v7.5.0 — Simulation & Dynamical Systems Runtime.
require_once __DIR__ . '/includes/scwb-v750-simulation-dynamical-systems-runtime.php';


// Workbench v7.6.0 — Engineering Systems Runtime.
require_once __DIR__ . '/includes/scwb-v760-engineering-systems-runtime.php';


// Workbench v7.7.0 — Optimization & Design Space Exploration.
require_once __DIR__ . '/includes/scwb-v770-optimization-design-space.php';
// Workbench v7.8.0 — Model Validation & Verification Framework.
require_once __DIR__ . '/includes/scwb-v780-model-validation-verification.php';

// Workbench v7.9.0 — Scientific Workflow Graph.
require_once __DIR__ . '/includes/scwb-v790-scientific-workflow-graph.php';

// Workbench v7.10.0 — Interactive Computational Notebook Runtime.
require_once __DIR__ . '/includes/scwb-v7100-interactive-computational-notebook.php';

// Workbench v7.11.0 — Visual Scientific Computing Workspace.
require_once __DIR__ . '/includes/scwb-v7110-visual-scientific-computing-workspace.php';

// Workbench v7.12.0 — Reproducible Experiment & Engineering Package.
require_once __DIR__ . '/includes/scwb-v7120-reproducible-experiment-engineering-package.php';

// Workbench v8.0.0 — Unified Computational Research Environment.
require_once __DIR__ . '/includes/scwb-v800-unified-computational-research-environment.php';

// Workbench v8.1.0 — Research Environment Persistence & Recovery.
require_once __DIR__ . '/includes/scwb-v810-research-environment-persistence-recovery.php';

// Workbench v8.2.0 — Unified Research Project Workspace.
require_once __DIR__ . '/includes/scwb-v820-unified-research-project-workspace.php';
