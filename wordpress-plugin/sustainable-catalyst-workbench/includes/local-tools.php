<?php
if (!defined('ABSPATH')) { exit; }
return [
    [
        'id' => 'chalkboard-symbolic-math',
        'title' => 'Chalkboard Translator + Symbolic Math',
        'domain' => 'Mathematical Modeling',
        'topic' => 'Symbolic Math and Engineering Units',
        'family' => 'symbolic_math',
        'engine' => 'python/sympy + pint',
        'description' => 'Translate keyboard math into chalkboard notation, LaTeX, SymPy code, symbolic operations, unit-aware engineering notes, and optional function graphs.',
        'inputs' => [
            [
                'name' => 'input',
                'label' => 'Keyboard math / engineering expression',
                'type' => 'textarea',
                'default' => "F = m*a
m = 12 kg
a = 3.5 m/s^2",
                'help' => 'Use keyboard syntax such as x^2 + 3x - 4, y = sin(x), or engineering lines with units.'
            ],
            [
                'name' => 'action',
                'label' => 'Action',
                'type' => 'select',
                'default' => 'translate',
                'options' => ['translate', 'simplify', 'solve', 'differentiate', 'integrate', 'factor', 'expand', 'graph'],
                'help' => ''
            ],
            [
                'name' => 'variable',
                'label' => 'Variable',
                'type' => 'text',
                'default' => 'x',
                'help' => ''
            ],
            [
                'name' => 'x_min',
                'label' => 'Graph x min',
                'type' => 'number',
                'default' => '-10',
                'help' => ''
            ],
            [
                'name' => 'x_max',
                'label' => 'Graph x max',
                'type' => 'number',
                'default' => '10',
                'help' => ''
            ]
        ],
        'graph_types' => ['function_curve', 'symbolic_translation', 'unit_check'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'linear-system-solver',
        'title' => 'Linear System Solver',
        'domain' => 'Mathematical Modeling',
        'topic' => 'Linear Algebra',
        'family' => 'linear_algebra',
        'engine' => 'python/numpy',
        'description' => 'Solve Ax=b, inspect rank, residual, condition number, determinant, eigenvalues, and stability warnings.',
        'inputs' => [
            [
                'name' => 'A',
                'label' => 'Matrix A',
                'type' => 'textarea',
                'default' => '[[3,2],[1,2]]',
                'help' => ''
            ],
            [
                'name' => 'b',
                'label' => 'Vector b',
                'type' => 'text',
                'default' => '[5,5]',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'residual_bar',
            'eigen_plot'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'calculus-function-analyzer',
        'title' => 'Calculus Function Analyzer',
        'domain' => 'Mathematical Modeling',
        'topic' => 'Calculus',
        'family' => 'calculus',
        'engine' => 'python/sympy-lite',
        'description' => 'Analyze a single-variable function numerically: derivative, accumulation, slope, extrema scan, and sensitivity graph.',
        'inputs' => [
            [
                'name' => 'expression',
                'label' => 'Function f(x)',
                'type' => 'text',
                'default' => 'x**2 - 4*x + 3',
                'help' => ''
            ],
            [
                'name' => 'x_min',
                'label' => 'x min',
                'type' => 'number',
                'default' => '-5',
                'help' => ''
            ],
            [
                'name' => 'x_max',
                'label' => 'x max',
                'type' => 'number',
                'default' => '5',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'function_curve',
            'derivative_curve'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'statistics-analyzer',
        'title' => 'Statistics Analyzer',
        'domain' => 'Statistics',
        'topic' => 'Statistics',
        'family' => 'statistics',
        'engine' => 'python/scipy + optional R',
        'description' => 'Descriptive statistics, distribution shape, confidence interval, and histogram.',
        'inputs' => [
            [
                'name' => 'data',
                'label' => 'Data values',
                'type' => 'textarea',
                'default' => '12,14,15,19,21,22,24,30',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'histogram',
            'boxplot'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'regression-analyzer',
        'title' => 'Regression Analyzer',
        'domain' => 'Statistics',
        'topic' => 'Regression',
        'family' => 'statistics',
        'engine' => 'python/scipy + optional R',
        'description' => 'Fit linear regression, estimate r-squared, p-values, residuals, and graph fit.',
        'inputs' => [
            [
                'name' => 'x',
                'label' => 'X values',
                'type' => 'text',
                'default' => '1,2,3,4,5',
                'help' => ''
            ],
            [
                'name' => 'y',
                'label' => 'Y values',
                'type' => 'text',
                'default' => '2,4,5,4,7',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'scatter_fit',
            'residuals'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'probability-distribution-calculator',
        'title' => 'Probability Distribution Calculator',
        'domain' => 'Probability',
        'topic' => 'Probability',
        'family' => 'probability',
        'engine' => 'python/scipy',
        'description' => 'Normal, binomial, Poisson, and beta distribution probabilities with visualizations.',
        'inputs' => [
            [
                'name' => 'distribution',
                'label' => 'Distribution',
                'type' => 'select',
                'default' => 'normal',
                'help' => '',
                'options' => [
                    'normal',
                    'binomial',
                    'poisson',
                    'beta'
                ]
            ],
            [
                'name' => 'params',
                'label' => 'Parameters',
                'type' => 'text',
                'default' => 'mean=0;sd=1',
                'help' => ''
            ],
            [
                'name' => 'value',
                'label' => 'Value',
                'type' => 'number',
                'default' => '1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'distribution_curve'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'differential-equation-simulator',
        'title' => 'Differential Equation Simulator',
        'domain' => 'Mathematical Modeling',
        'topic' => 'Differential Equations',
        'family' => 'differential_equations',
        'engine' => 'python/scipy + optional Julia',
        'description' => 'Simulate exponential, logistic, oscillator, and predator-prey systems.',
        'inputs' => [
            [
                'name' => 'model',
                'label' => 'Model',
                'type' => 'select',
                'default' => 'logistic',
                'help' => '',
                'options' => [
                    'logistic',
                    'exponential_decay',
                    'harmonic_oscillator',
                    'predator_prey'
                ]
            ],
            [
                'name' => 'initial',
                'label' => 'Initial state',
                'type' => 'text',
                'default' => '10',
                'help' => ''
            ],
            [
                'name' => 'rate',
                'label' => 'Rate',
                'type' => 'number',
                'default' => '0.25',
                'help' => ''
            ],
            [
                'name' => 't_end',
                'label' => 'Time horizon',
                'type' => 'number',
                'default' => '30',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'trajectory'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'decision-analysis-tool',
        'title' => 'Decision Analysis Tool',
        'domain' => 'Decision Science',
        'topic' => 'Decision Thinking',
        'family' => 'decision',
        'engine' => 'python',
        'description' => 'Weighted decision matrix, expected value, uncertainty, sensitivity, and regret.',
        'inputs' => [
            [
                'name' => 'options',
                'label' => 'Options',
                'type' => 'textarea',
                'default' => 'Option A,8,6,7\nOption B,6,9,8',
                'help' => ''
            ],
            [
                'name' => 'weights',
                'label' => 'Weights',
                'type' => 'text',
                'default' => '0.4,0.35,0.25',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'score_bar',
            'sensitivity'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'economics-calculator',
        'title' => 'Economics Calculator',
        'domain' => 'Economics',
        'topic' => 'Economic Systems',
        'family' => 'economics',
        'engine' => 'python + optional R/Julia',
        'description' => 'Supply-demand equilibrium, elasticity, NPV, break-even, multiplier, inequality, and input-output analysis.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'npv',
                'help' => '',
                'options' => [
                    'npv',
                    'elasticity',
                    'supply_demand',
                    'break_even',
                    'input_output',
                    'inequality_gini'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'rate=0.08; cashflows=-1000,300,400,500',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'curve',
            'bar',
            'lorenz'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'energy-systems-calculator',
        'title' => 'Energy Systems Calculator',
        'domain' => 'Energy',
        'topic' => 'Energy Systems',
        'family' => 'energy',
        'engine' => 'python + optional Julia/EnergyPlus',
        'description' => 'Demand, cost, emissions, solar PV, battery autonomy, LCOE, building energy, and scenario curves.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'electricity_cost_emissions',
                'help' => '',
                'options' => [
                    'electricity_cost_emissions',
                    'solar_pv',
                    'battery_autonomy',
                    'lcoe',
                    'building_eui',
                    'energy_mix'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'kwh=500;rate=0.16;kgco2_per_kwh=0.4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'load_curve',
            'scenario',
            'stacked'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'psychology-scale-analyzer',
        'title' => 'Psychology Scale Analyzer',
        'domain' => 'Psychology',
        'topic' => 'Psychology and Grit',
        'family' => 'psychology',
        'engine' => 'python + optional R',
        'description' => 'Scale scoring, Cronbach alpha, item profile, grit/persistence curve, and intervention effect sizes.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'scale_reliability',
                'help' => '',
                'options' => [
                    'scale_reliability',
                    'grit_profile',
                    'effect_size',
                    'memory_decay',
                    'signal_detection'
                ]
            ],
            [
                'name' => 'responses',
                'label' => 'Responses / values',
                'type' => 'textarea',
                'default' => '4,5,4,3\n3,4,4,2\n5,5,4,4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'boxplot',
            'profile',
            'curve'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'scientific-calculator',
        'title' => 'Scientific Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Physics, Chemistry, Biology',
        'family' => 'science',
        'engine' => 'python + optional Julia',
        'description' => 'Physics, chemistry, biology, astronomy, materials, and environmental calculations.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'ideal_gas',
                'help' => '',
                'options' => [
                    'ideal_gas',
                    'kinetic_energy',
                    'stress_strain',
                    'dilution',
                    'logistic_population',
                    'orbital_period',
                    'reynolds_number'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'n=1;R=8.314;T=298;V=0.024',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'curve',
            'bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'engineering-calculator',
        'title' => 'Engineering Calculator',
        'domain' => 'Engineering',
        'topic' => 'Engineering',
        'family' => 'engineering',
        'engine' => 'python + optional C++',
        'description' => 'Beam bending, shear/moment, truss basics, factor of safety, Reynolds number, voltage drop, and reliability.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'beam_uniform_load',
                'help' => '',
                'options' => [
                    'beam_uniform_load',
                    'column_buckling',
                    'factor_of_safety',
                    'reynolds_number',
                    'voltage_drop',
                    'heat_transfer'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'span=6;load=10;E=200e9;I=8e-6',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'shear_moment',
            'deflection'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'architecture-building-calculator',
        'title' => 'Architecture & Building Calculator',
        'domain' => 'Architecture',
        'topic' => 'Built Environment',
        'family' => 'architecture',
        'engine' => 'python + optional EnergyPlus/IfcOpenShell',
        'description' => 'Space planning, occupancy, EUI, embodied carbon, solar orientation, daylight proxy, and adjacency matrices.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'space_program',
                'help' => '',
                'options' => [
                    'space_program',
                    'occupancy_load',
                    'building_eui',
                    'embodied_carbon',
                    'solar_shading',
                    'adjacency_matrix'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'area_m2=1000;annual_kwh=180000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'program_bar',
            'carbon_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'sustainability-resilience-scorecard',
        'title' => 'Sustainability & Resilience Scorecard',
        'domain' => 'Sustainability',
        'topic' => 'Risk & Resilience',
        'family' => 'sustainability',
        'engine' => 'python',
        'description' => 'Weighted resilience, exposure, sensitivity, adaptive capacity, governance, equity, and recovery diagnostics.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Scores',
                'type' => 'textarea',
                'default' => 'exposure=4;sensitivity=3;adaptive_capacity=2;governance=3;equity=2;recovery=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'radar_proxy',
            'bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'ai-governance-audit',
        'title' => 'AI Governance Audit',
        'domain' => 'Governance',
        'topic' => 'AI Systems',
        'family' => 'governance',
        'engine' => 'python + optional Haskell',
        'description' => 'Risk, accountability, documentation, human oversight, dataset quality, transparency, and contestability audit.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Scores',
                'type' => 'textarea',
                'default' => 'data_quality=3;transparency=2;human_oversight=4;contestability=2;impact=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'risk_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'haskell-rule-checker',
        'title' => 'Haskell Rule Checker',
        'domain' => 'Formal Logic',
        'topic' => 'Rules and Constraints',
        'family' => 'formal_logic',
        'engine' => 'python + optional Haskell',
        'description' => 'Constraint consistency checker for governance, ethics, engineering rules, and institutional logic.',
        'inputs' => [
            [
                'name' => 'rules',
                'label' => 'Rules',
                'type' => 'textarea',
                'default' => 'IF high_impact THEN human_review\nIF human_review THEN audit_log',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'logic_trace'
        ],
        'audience_modes' => [
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'qualitative-interpretation-matrix',
        'title' => 'Qualitative Interpretation Matrix',
        'domain' => 'Meaning',
        'topic' => 'Interpretation',
        'family' => 'interpretation',
        'engine' => 'python + AI',
        'description' => 'Structured interpretation for narrative, symbols, mythology, philosophy, ethics, culture, and institutions.',
        'inputs' => [
            [
                'name' => 'text',
                'label' => 'Text or case',
                'type' => 'textarea',
                'default' => 'Describe the case, symbol, narrative, or institution to interpret.',
                'help' => ''
            ],
            [
                'name' => 'lens',
                'label' => 'Lens',
                'type' => 'select',
                'default' => 'systems',
                'help' => '',
                'options' => [
                    'systems',
                    'ethics',
                    'symbolism',
                    'narrative',
                    'governance',
                    'religion',
                    'culture'
                ]
            ]
        ],
        'graph_types' => [
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'music-frequency-calculator',
        'title' => 'Music Frequency Calculator',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Music Theory',
        'family' => 'music_pattern',
        'engine' => 'python/numpy',
        'description' => 'Equal temperament, MIDI frequency, cents, harmonic series, beat frequency, and tempo timing analytics.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'midi_to_frequency',
                'help' => '',
                'options' => [
                    'midi_to_frequency',
                    'equal_temperament',
                    'cents_between',
                    'tempo',
                    'harmonic_series'
                ]
            ],
            [
                'name' => 'midi',
                'label' => 'MIDI note',
                'type' => 'number',
                'default' => '69',
                'help' => ''
            ],
            [
                'name' => 'f0',
                'label' => 'Base frequency',
                'type' => 'number',
                'default' => '440',
                'help' => ''
            ],
            [
                'name' => 'f1',
                'label' => 'Frequency 1',
                'type' => 'number',
                'default' => '440',
                'help' => ''
            ],
            [
                'name' => 'f2',
                'label' => 'Frequency 2',
                'type' => 'number',
                'default' => '466.1638',
                'help' => ''
            ],
            [
                'name' => 'bpm',
                'label' => 'Tempo BPM',
                'type' => 'number',
                'default' => '120',
                'help' => ''
            ],
            [
                'name' => 'fundamental',
                'label' => 'Fundamental Hz',
                'type' => 'number',
                'default' => '110',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'frequency_curve',
            'harmonic_bar',
            'tempo_grid'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'chord-scale-identifier',
        'title' => 'Chord and Scale Identifier',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Music Theory',
        'family' => 'music_pattern',
        'engine' => 'python',
        'description' => 'Identify pitch-class sets, common chords, scale candidates, and mode relationships.',
        'inputs' => [
            [
                'name' => 'notes',
                'label' => 'Notes or pitch classes',
                'type' => 'text',
                'default' => 'C E G',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'pitch_class_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'color-contrast-calculator',
        'title' => 'Color Contrast and Luminance Calculator',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Color Theory and Design',
        'family' => 'color_design',
        'engine' => 'python',
        'description' => 'HEX/RGB luminance, contrast ratio, accessibility checks, and color distance analytics.',
        'inputs' => [
            [
                'name' => 'foreground',
                'label' => 'Foreground HEX',
                'type' => 'text',
                'default' => '#111111',
                'help' => ''
            ],
            [
                'name' => 'background',
                'label' => 'Background HEX',
                'type' => 'text',
                'default' => '#fff8e7',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'luminance_bar',
            'contrast_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'color-harmony-generator',
        'title' => 'Color Harmony Generator',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Color Theory and Design',
        'family' => 'color_design',
        'engine' => 'python',
        'description' => 'Generate complementary, analogous, and triadic palettes with luminance profile.',
        'inputs' => [
            [
                'name' => 'base',
                'label' => 'Base HEX',
                'type' => 'text',
                'default' => '#ff0000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'palette_luminance'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'vector-geometry-calculator',
        'title' => 'Vector Geometry Calculator',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Vector Geometry',
        'family' => 'linear_algebra_geometry',
        'engine' => 'python/numpy',
        'description' => 'Vector magnitude, dot product, angle, distance, projection, cross product, and transformation-ready geometry.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'dot_angle_projection',
                'help' => '',
                'options' => [
                    'dot_angle_projection',
                    'projection',
                    'cross_product'
                ]
            ],
            [
                'name' => 'a',
                'label' => 'Vector a',
                'type' => 'text',
                'default' => '1,2,3',
                'help' => ''
            ],
            [
                'name' => 'b',
                'label' => 'Vector b',
                'type' => 'text',
                'default' => '4,5,6',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'vector_plot',
            'component_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'embedding-similarity-tool',
        'title' => 'Embedding Similarity Tool',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'AI Representation',
        'family' => 'ai_geometry',
        'engine' => 'python/numpy',
        'description' => 'Cosine similarity, Euclidean distance, Manhattan distance, dot product, and embedding component comparison.',
        'inputs' => [
            [
                'name' => 'a',
                'label' => 'Embedding A',
                'type' => 'textarea',
                'default' => '0.2,0.1,0.9,0.4',
                'help' => ''
            ],
            [
                'name' => 'b',
                'label' => 'Embedding B',
                'type' => 'textarea',
                'default' => '0.1,0.3,0.8,0.5',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'component_line'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'pca-dimensionality-explorer',
        'title' => 'PCA / Dimensionality Reduction Explorer',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Mathematical Pattern',
        'family' => 'dimensionality_reduction',
        'engine' => 'python/numpy',
        'description' => 'SVD-based PCA, explained variance, component loadings, and score plots for pattern structure.',
        'inputs' => [
            [
                'name' => 'data',
                'label' => 'Data matrix',
                'type' => 'textarea',
                'default' => '1,2,3\n2,3,4\n3,4,6\n4,5,8\n5,7,10',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'explained_variance',
            'score_plot'
        ],
        'audience_modes' => [
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'fourier-frequency-analysis-tool',
        'title' => 'Fourier / Frequency Analysis Tool',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Mathematical Pattern',
        'family' => 'frequency_analysis',
        'engine' => 'python/numpy',
        'description' => 'Discrete Fourier spectrum for sound, signals, cyclical patterns, and frequency-domain reasoning.',
        'inputs' => [
            [
                'name' => 'data',
                'label' => 'Signal samples',
                'type' => 'textarea',
                'default' => '0,1,0,-1,0,1,0,-1,0,1,0,-1',
                'help' => ''
            ],
            [
                'name' => 'sample_rate',
                'label' => 'Sample rate',
                'type' => 'number',
                'default' => '1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'frequency_spectrum'
        ],
        'audience_modes' => [
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'ai-classification-metrics-calculator',
        'title' => 'AI Classification Metrics Calculator',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'AI Representation',
        'family' => 'ai_evaluation',
        'engine' => 'python',
        'description' => 'Accuracy, precision, recall, specificity, F1, and confusion-matrix visualization.',
        'inputs' => [
            [
                'name' => 'tp',
                'label' => 'True positives',
                'type' => 'number',
                'default' => '50',
                'help' => ''
            ],
            [
                'name' => 'fp',
                'label' => 'False positives',
                'type' => 'number',
                'default' => '10',
                'help' => ''
            ],
            [
                'name' => 'tn',
                'label' => 'True negatives',
                'type' => 'number',
                'default' => '80',
                'help' => ''
            ],
            [
                'name' => 'fn',
                'label' => 'False negatives',
                'type' => 'number',
                'default' => '5',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'metrics_bar',
            'confusion_matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'multimodal-pattern-comparison-tool',
        'title' => 'Multimodal Pattern Comparison Tool',
        'domain' => 'Pattern, Geometry, Design, Music, and AI',
        'topic' => 'Multimodal Analysis',
        'family' => 'pattern_similarity',
        'engine' => 'python/numpy',
        'description' => 'Compare numeric representations of visual, musical, textual, or design patterns using correlation and similarity metrics.',
        'inputs' => [
            [
                'name' => 'pattern_a',
                'label' => 'Pattern A',
                'type' => 'textarea',
                'default' => '1,3,2,5,4,6',
                'help' => ''
            ],
            [
                'name' => 'pattern_b',
                'label' => 'Pattern B',
                'type' => 'textarea',
                'default' => '2,4,3,6,5,7',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'pattern_line'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'environmental-monitoring-qaqc-tool',
        'title' => 'Environmental Monitoring QA/QC Tool',
        'domain' => 'Earth, Ocean, Climate, and Environmental Monitoring',
        'topic' => 'Environmental Monitoring Systems',
        'family' => 'environmental_monitoring',
        'engine' => 'python/numpy + optional R',
        'description' => 'Sensor QA/QC, threshold exceedance, outlier detection, trend screening, data-quality flags, and monitoring visualizations.',
        'inputs' => [
            [
                'name' => 'values',
                'label' => 'Monitoring values',
                'type' => 'textarea',
                'default' => '12,12.4,12.2,19.8,12.1,12.0,11.9',
                'help' => ''
            ],
            [
                'name' => 'lower_threshold',
                'label' => 'Lower threshold',
                'type' => 'number',
                'default' => '10',
                'help' => ''
            ],
            [
                'name' => 'upper_threshold',
                'label' => 'Upper threshold',
                'type' => 'number',
                'default' => '15',
                'help' => ''
            ],
            [
                'name' => 'z_limit',
                'label' => 'Outlier z limit',
                'type' => 'number',
                'default' => '3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'time_series',
            'threshold_flags'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'global-impact-assessment-matrix',
        'title' => 'Global Impact Assessment Matrix',
        'domain' => 'Global Impact',
        'topic' => 'Public Systems and Global Risk',
        'family' => 'impact_assessment',
        'engine' => 'python + AI',
        'description' => 'Heavy multidomain impact matrix across climate, biodiversity, water, health, rights, economics, governance, equity, reversibility, and uncertainty.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Impact scores',
                'type' => 'textarea',
                'default' => 'climate=4;biodiversity=4;water=3;public_health=4;human_rights=3;economic_disruption=3;governance=4;reversibility=2;uncertainty=4;equity=4',
                'help' => ''
            ],
            [
                'name' => 'weights',
                'label' => 'Optional weights',
                'type' => 'textarea',
                'default' => '',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'impact_bar',
            'ranked_contributors'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'climate-change-scenario-tool',
        'title' => 'Climate Change Scenario Tool',
        'domain' => 'Earth, Ocean, Climate, and Environmental Monitoring',
        'topic' => 'Climate Change',
        'family' => 'climate_scenarios',
        'engine' => 'python + optional Julia',
        'description' => 'Climate scenario proxy tool for warming pathways, carbon-budget framing, and sea-level proxy analysis with curves and uncertainty caveats.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'warming_pathway',
                'help' => '',
                'options' => [
                    'warming_pathway',
                    'carbon_budget',
                    'sea_level_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'baseline_temp=1.2;annual_change=0.025;years=80',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'scenario_curve'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'earth-science-hazard-analyzer',
        'title' => 'Earth Science Hazard Analyzer',
        'domain' => 'Earth, Ocean, Climate, and Environmental Monitoring',
        'topic' => 'Earth Science',
        'family' => 'hazard_risk',
        'engine' => 'python + optional GIS',
        'description' => 'Educational hazard-risk proxy using probability, exposure, vulnerability, adaptive capacity, and warning-time factors.',
        'inputs' => [
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'probability=0.15;exposure=4;vulnerability=3;capacity=2;warning_time=1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'hazard_factor_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'marine-biology-ocean-health-tool',
        'title' => 'Marine Biology and Ocean Health Tool',
        'domain' => 'Earth, Ocean, Climate, and Environmental Monitoring',
        'topic' => 'Marine Biology',
        'family' => 'ocean_health',
        'engine' => 'python + optional R',
        'description' => 'Ocean-health stress proxy using temperature anomaly, pH, dissolved oxygen, nutrients, plastic pressure, and biodiversity buffer.',
        'inputs' => [
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'temperature_anomaly=1.4;ph=8.0;dissolved_oxygen=5.5;nutrients=3.0;plastic_index=2.0;biodiversity=3.5',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'ocean_stress_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'astronomy-calculator',
        'title' => 'Astronomy Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Astronomy',
        'family' => 'astronomy',
        'engine' => 'python/numpy',
        'description' => 'Orbital period, escape velocity, luminosity-distance relation, and habitable-zone proxy calculations.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'orbital_period',
                'help' => '',
                'options' => [
                    'orbital_period',
                    'escape_velocity',
                    'luminosity_distance',
                    'habitable_zone_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'central_mass=1.989e30;semi_major_axis=1.496e11',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'bar',
            'units_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'materials-science-calculator',
        'title' => 'Materials Science Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Materials Science',
        'family' => 'materials',
        'engine' => 'python + optional C++',
        'description' => 'Stress-strain, diffusion length, thermal conduction, and fatigue-risk proxy tools with professional-review warning.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'stress_strain',
                'help' => '',
                'options' => [
                    'stress_strain',
                    'diffusion',
                    'thermal_conduction',
                    'fatigue_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'force=1000;area=0.0005;delta_length=0.001;length=1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'stress_bar',
            'risk_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'health-medical-public-health-tool',
        'title' => 'Health and Medical/Public Health Analytics Tool',
        'domain' => 'Health and Medical',
        'topic' => 'Public Health and Medical Analytics',
        'family' => 'public_health',
        'engine' => 'python + optional R',
        'description' => 'Educational public-health analytics: incidence, relative risk, screening-test predictive values, and SIR proxy curves.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'public_health_risk',
                'help' => '',
                'options' => [
                    'public_health_risk',
                    'relative_risk',
                    'screening_test',
                    'sir_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'population=100000;cases=250;sensitivity=0.9;specificity=0.95;prevalence=0.02',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'risk_bar',
            'sir_curve'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'international-law-issue-mapper',
        'title' => 'International Law Issue Mapper',
        'domain' => 'Global Governance',
        'topic' => 'International Law',
        'family' => 'legal_issue_spotting',
        'engine' => 'python + AI',
        'description' => 'Educational international-law issue mapper for jurisdiction, state responsibility, treaties, custom, human rights, environmental harm, remedies, evidence, and forums.',
        'inputs' => [
            [
                'name' => 'case',
                'label' => 'Case description',
                'type' => 'textarea',
                'default' => 'A cross-border environmental harm affects coastal communities and critical habitats.',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'issue_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'legal-traditions-comparator',
        'title' => 'Legal Traditions Comparator',
        'domain' => 'Global Governance',
        'topic' => 'Legal Traditions',
        'family' => 'comparative_law',
        'engine' => 'python + qualitative framework',
        'description' => 'Comparative legal-tradition matrix for common law, civil law, Islamic law, customary/indigenous law, religious traditions, socialist systems, and legal pluralism.',
        'inputs' => [
            [
                'name' => 'traditions',
                'label' => 'Traditions to compare',
                'type' => 'text',
                'default' => 'common law, civil law, islamic law',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'comparison_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'metaphysics-framework-tool',
        'title' => 'Metaphysics Framework Tool',
        'domain' => 'Meaning and Philosophy',
        'topic' => 'Metaphysics',
        'family' => 'metaphysical_analysis',
        'engine' => 'python + AI',
        'description' => 'Structured metaphysical inquiry for ontology, causation, time, identity, mind/matter, freedom, agency, and determinism.',
        'inputs' => [
            [
                'name' => 'question',
                'label' => 'Question or problem',
                'type' => 'textarea',
                'default' => 'What changes while something remains the same?',
                'help' => ''
            ],
            [
                'name' => 'lens',
                'label' => 'Lens',
                'type' => 'select',
                'default' => 'ontology',
                'help' => '',
                'options' => [
                    'ontology',
                    'causation',
                    'time',
                    'identity',
                    'mind_matter',
                    'freedom'
                ]
            ]
        ],
        'graph_types' => [
            'conceptual_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'physics-calculator',
        'title' => 'Physics Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Physics',
        'family' => 'physics',
        'engine' => 'python/numpy',
        'description' => 'Mechanics, energy, waves, electricity, fluids, and thermodynamics calculations with unit-aware summaries and SVG graphs.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'mechanics',
                'help' => '',
                'options' => [
                    'mechanics',
                    'energy_work',
                    'waves',
                    'electricity',
                    'fluids',
                    'thermodynamics'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'mass=2;velocity=12;height=5;force=10;distance=3;angle_deg=0',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'curve',
            'bar',
            'units_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'chemistry-calculator',
        'title' => 'Chemistry Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Chemistry',
        'family' => 'chemistry',
        'engine' => 'python',
        'description' => 'Molarity, stoichiometry, pH, ideal gas, percent yield, and Beer-Lambert calculations for chemistry learning and analysis.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'molarity',
                'help' => '',
                'options' => [
                    'molarity',
                    'stoichiometry',
                    'ph',
                    'ideal_gas',
                    'percent_yield',
                    'beer_lambert'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'moles=0.5;volume_l=1.0;mass_g=10;molar_mass_g_mol=58.44',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'bar',
            'units_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'biology-calculator',
        'title' => 'Biology Calculator',
        'domain' => 'Natural Science',
        'topic' => 'Biology',
        'family' => 'biology',
        'engine' => 'python/numpy',
        'description' => 'Population growth, enzyme kinetics, Hardy-Weinberg proportions, biodiversity indexes, and photosynthesis proxy analysis.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'population_growth',
                'help' => '',
                'options' => [
                    'population_growth',
                    'enzyme_kinetics',
                    'hardy_weinberg',
                    'biodiversity',
                    'photosynthesis_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'initial=100;rate=0.25;carrying_capacity=1000;time=30',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'curve',
            'bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'environmental-science-calculator',
        'title' => 'Environmental Science Calculator',
        'domain' => 'Environmental Science',
        'topic' => 'Environmental Systems',
        'family' => 'environmental_science',
        'engine' => 'python/numpy',
        'description' => 'Water-quality, air-quality, carbon-footprint, habitat-fragmentation, and composite environmental-risk proxy calculations.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'water_quality_index',
                'help' => '',
                'options' => [
                    'water_quality_index',
                    'air_quality_proxy',
                    'carbon_footprint',
                    'habitat_fragmentation',
                    'environmental_risk_profile'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'do=7;ph=7.4;turbidity=3;nitrate=2;phosphate=0.1;temperature=18',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'bar',
            'risk_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'earth-science-calculator',
        'title' => 'Earth Science Calculator',
        'domain' => 'Earth Science',
        'topic' => 'Earth Systems',
        'family' => 'earth_science',
        'engine' => 'python/numpy',
        'description' => 'Watershed runoff, earthquake energy proxy, erosion risk, rock density, and water-balance calculations.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'watershed_runoff',
                'help' => '',
                'options' => [
                    'watershed_runoff',
                    'earthquake_energy',
                    'erosion_risk',
                    'rock_density',
                    'water_balance'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'rainfall_mm=50;area_km2=10;runoff_coefficient=0.35;slope=8;soil_erodibility=0.3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'bar',
            'units_summary'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'content-frameworks-analyzer',
        'title' => 'Content Frameworks Analyzer',
        'domain' => 'Content Frameworks',
        'topic' => 'Knowledge Architecture',
        'family' => 'content_frameworks',
        'engine' => 'python + AI',
        'description' => 'Maps briefs to purpose, audience, problem, evidence, structure, voice, action, ethics, and measurement dimensions.',
        'inputs' => [
            [
                'name' => 'brief',
                'label' => 'Brief or content problem',
                'type' => 'textarea',
                'default' => 'Explain a complex public-interest tool to a mixed audience and connect it to research, ethics, and action.',
                'help' => ''
            ],
            [
                'name' => 'lens',
                'label' => 'Lens',
                'type' => 'select',
                'default' => 'knowledge_architecture',
                'help' => '',
                'options' => [
                    'knowledge_architecture',
                    'educational',
                    'persuasive',
                    'institutional',
                    'measurement'
                ]
            ]
        ],
        'graph_types' => [
            'framework_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'storytelling-structure-analyzer',
        'title' => 'Storytelling Structure Analyzer',
        'domain' => 'Content Frameworks',
        'topic' => 'Storytelling',
        'family' => 'storytelling',
        'engine' => 'python + qualitative framework',
        'description' => 'Analyzes narrative arc, stakes, conflict, character movement, resolution, and meaning without reducing story to formula.',
        'inputs' => [
            [
                'name' => 'story',
                'label' => 'Story, draft, or scenario',
                'type' => 'textarea',
                'default' => 'A researcher builds a public-interest tool, faces uncertainty, tests it with users, and turns it into shared infrastructure.',
                'help' => ''
            ],
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'narrative_arc',
                'help' => '',
                'options' => [
                    'narrative_arc',
                    'institutional_story',
                    'ethical_story',
                    'systems_story'
                ]
            ]
        ],
        'graph_types' => [
            'story_bar',
            'arc'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'social-psychology-analyzer',
        'title' => 'Social Psychology Analyzer',
        'domain' => 'Psychology',
        'topic' => 'Social Psychology',
        'family' => 'social_psychology',
        'engine' => 'python + qualitative framework',
        'description' => 'Maps scenarios to norms, identity, trust, authority, conformity, cooperation, persuasion, polarization, and adoption mechanisms.',
        'inputs' => [
            [
                'name' => 'scenario',
                'label' => 'Scenario',
                'type' => 'textarea',
                'default' => 'A group is deciding whether to adopt a new tool while norms, trust, authority, incentives, and uncertainty shape behavior.',
                'help' => ''
            ],
            [
                'name' => 'lens',
                'label' => 'Lens',
                'type' => 'select',
                'default' => 'group_dynamics',
                'help' => '',
                'options' => [
                    'group_dynamics',
                    'norms',
                    'trust',
                    'persuasion',
                    'cooperation',
                    'diffusion'
                ]
            ]
        ],
        'graph_types' => [
            'mechanism_bar',
            'matrix'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'grit-resilience-analyzer',
        'title' => 'Grit and Resilience Analyzer',
        'domain' => 'Psychology',
        'topic' => 'Grit, Motivation, and Persistence',
        'family' => 'grit_resilience',
        'engine' => 'python + optional R',
        'description' => 'Reflective grit, persistence, recovery, deliberate-practice, and purpose-alignment profile with non-clinical caveats.',
        'inputs' => [
            [
                'name' => 'responses',
                'label' => 'Self-rating values',
                'type' => 'textarea',
                'default' => '4,5,4,3,5,4,4,5',
                'help' => ''
            ],
            [
                'name' => 'context',
                'label' => 'Context',
                'type' => 'textarea',
                'default' => 'Long-term learning, career transition, creative work, and sustained project execution.',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'profile_bar',
            'reflection'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'nuclear-physics-calculator',
        'title' => 'Nuclear Physics Calculator',
        'domain' => 'Advanced Physical Systems',
        'topic' => 'Nuclear Physics',
        'family' => 'nuclear_physics',
        'engine' => 'python/numpy',
        'description' => 'Radioactive decay, decay constants, binding energy, mean lifetime, and educational radiation-dose proxies with strict non-weapons safety boundaries.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'radioactive_decay',
                'help' => '',
                'options' => [
                    'radioactive_decay',
                    'binding_energy',
                    'radiation_dose_proxy',
                    'mean_lifetime'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'initial_activity_bq=1000;half_life_s=3600;time_s=7200;mass_defect_u=0.01',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'decay_curve',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'restricted_educational'
    ],
    [
        'id' => 'particle-physics-calculator',
        'title' => 'Particle Physics Calculator',
        'domain' => 'Advanced Physical Systems',
        'topic' => 'Particle Physics',
        'family' => 'particle_physics',
        'engine' => 'python/numpy',
        'description' => 'Relativistic energy/momentum, event-rate estimates, detector-resolution proxies, and lifetime-width relationships for educational high-energy physics.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'relativistic_energy_momentum',
                'help' => '',
                'options' => [
                    'relativistic_energy_momentum',
                    'event_rate',
                    'uncertainty_resolution',
                    'lifetime_width'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'mass_mev_c2=0.511;momentum_mev_c=1;luminosity_cm2_s=1e34;cross_section_pb=1;time_s=3600',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'energy_momentum_curve',
            'resolution_curve',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'restricted_educational'
    ],
    [
        'id' => 'neurophysics-calculator',
        'title' => 'Neurophysics Calculator',
        'domain' => 'Advanced Physical Systems',
        'topic' => 'Neurophysics and Biophysics',
        'family' => 'neurophysics',
        'engine' => 'python/numpy',
        'description' => 'Membrane RC time constants, Nernst potentials, integrate-and-fire proxies, and conduction delay for educational neurophysics.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'membrane_rc',
                'help' => '',
                'options' => [
                    'membrane_rc',
                    'nernst_potential',
                    'integrate_and_fire',
                    'conduction_delay'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'resistance_mohm=100;capacitance_pf=100;temperature_c=37;z=1;outside_mm=145;inside_mm=15',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'membrane_curve',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'rocket-science-calculator',
        'title' => 'Rocket Science and Orbital Mechanics Calculator',
        'domain' => 'Engineering',
        'topic' => 'Aerospace and Rocket Science',
        'family' => 'aerospace',
        'engine' => 'python/numpy',
        'description' => 'Tsiolkovsky delta-v, thrust-to-weight, circular orbital velocity, period, and mass-ratio estimates for educational aerospace analysis.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'delta_v',
                'help' => '',
                'options' => [
                    'delta_v',
                    'thrust_to_weight',
                    'orbital_velocity',
                    'mass_ratio_required'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'isp_s=300;initial_mass_kg=1000;final_mass_kg=500;thrust_n=15000;altitude_m=400000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'delta_v_curve',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'restricted_educational'
    ],
    [
        'id' => 'electronics-engineering-calculator',
        'title' => 'Electronics Engineering Calculator',
        'domain' => 'Engineering',
        'topic' => 'Electronics Engineering',
        'family' => 'electronics',
        'engine' => 'python/numpy',
        'description' => 'Ohm/power calculations, RC filters, RLC resonance, op-amp gain, ADC resolution, and circuit-summary graphs.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'ohms_law_power',
                'help' => '',
                'options' => [
                    'ohms_law_power',
                    'rc_filter',
                    'rlc_resonance',
                    'op_amp_gain',
                    'adc_resolution'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'voltage=12;resistance=100;capacitance_f=1e-6;frequency_hz=1000;inductance_h=0.01',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'filter_response',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'rf-antenna-calculator',
        'title' => 'RF and Antenna Calculator',
        'domain' => 'Engineering',
        'topic' => 'RF, Antenna, and Wireless Systems',
        'family' => 'rf_antenna',
        'engine' => 'python/numpy',
        'description' => 'Frequency/wavelength conversion, free-space path loss, Friis-style link budgets, antenna dimension estimates, and regulatory/safety caveats.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'wavelength_frequency',
                'help' => '',
                'options' => [
                    'wavelength_frequency',
                    'free_space_path_loss',
                    'link_budget',
                    'antenna_gain'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'frequency_hz=915e6;distance_km=1;tx_power_dbm=20;tx_gain_dbi=2;rx_gain_dbi=2;losses_db=2',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'path_loss_curve',
            'link_budget',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'restricted_educational'
    ],
    [
        'id' => 'full-stack-engineering-tool',
        'title' => 'Full-Stack Engineering Tool',
        'domain' => 'Engineering',
        'topic' => 'Engineering Systems',
        'family' => 'engineering_stack',
        'engine' => 'python/numpy',
        'description' => 'FMEA risk, factor of safety, reliability curves, systems-engineering maturity, and multidisciplinary engineering review support.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'fmea_risk',
                'help' => '',
                'options' => [
                    'fmea_risk',
                    'factor_of_safety',
                    'reliability',
                    'systems_maturity'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'severity=4;occurrence=3;detection=2;load=1000;capacity=2500;mtbf_hours=10000;time_hours=1000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'risk_bar',
            'reliability_curve',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'lab-science-calculator',
        'title' => 'Lab Science Calculator',
        'domain' => 'Lab Science',
        'topic' => 'Biology, Chemistry, and Laboratory QA/QC',
        'family' => 'lab_science',
        'engine' => 'python/numpy',
        'description' => 'Serial dilution, CFU counts, qPCR efficiency, dose-response research curves, replicate QA/QC, and lab-science calculations for biologists and chemists.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'serial_dilution',
                'help' => '',
                'options' => [
                    'serial_dilution',
                    'cfu_count',
                    'qpcr_efficiency',
                    'dose_response_research',
                    'replicate_qaqc'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'c1=1.0;v1_ml=1.0;v2_ml=10;od=0.8;dilution_factor=100;colony_count=80;plated_ml=0.1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'dose_response_curve',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'clinical-research-calculator',
        'title' => 'Clinical Research Calculator',
        'domain' => 'Health and Medical',
        'topic' => 'Physician and Public-Health Research',
        'family' => 'clinical_research',
        'engine' => 'python/numpy',
        'description' => 'Diagnostic metrics, NNT, odds ratio, effect size, and clinical/public-health research calculations with non-diagnostic guardrails.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'diagnostic_metrics',
                'help' => '',
                'options' => [
                    'diagnostic_metrics',
                    'nnt',
                    'odds_ratio',
                    'effect_size'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'tp=80;fp=10;tn=900;fn=20;event_rate_control=0.2;event_rate_treatment=0.12',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'metrics_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'predictive-analytics-forecasting-tool',
        'title' => 'Predictive Analytics Forecasting Tool',
        'domain' => 'Predictive Analytics',
        'topic' => 'Forecasting and Decision Support',
        'family' => 'forecasting',
        'engine' => 'python/numpy + optional R/Julia',
        'description' => 'Moving average, exponential smoothing, linear trend forecasts, confidence proxies, forecast diagnostics, and downloadable graph/report outputs.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'linear_trend',
                'help' => '',
                'options' => [
                    'linear_trend',
                    'moving_average',
                    'exponential_smoothing'
                ]
            ],
            [
                'name' => 'series',
                'label' => 'Historical series',
                'type' => 'textarea',
                'default' => '120,128,133,140,145,151,160,171,178,190,203,215',
                'help' => ''
            ],
            [
                'name' => 'horizon',
                'label' => 'Forecast horizon',
                'type' => 'number',
                'default' => '6',
                'help' => ''
            ],
            [
                'name' => 'alpha',
                'label' => 'Smoothing alpha',
                'type' => 'number',
                'default' => '0.35',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'forecast_curve',
            'confidence_band',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'time-series-diagnostics-tool',
        'title' => 'Time-Series Diagnostics Tool',
        'domain' => 'Predictive Analytics',
        'topic' => 'Time-Series Diagnostics',
        'family' => 'time_series',
        'engine' => 'python/numpy + optional statsmodels',
        'description' => 'Trend, rolling mean, volatility, autocorrelation, anomaly flags, and stationarity-warning proxies for monitoring and forecasting workflows.',
        'inputs' => [
            [
                'name' => 'series',
                'label' => 'Time series',
                'type' => 'textarea',
                'default' => '10,11,13,12,15,18,17,21,24,23,26,30',
                'help' => ''
            ],
            [
                'name' => 'max_lag',
                'label' => 'Max autocorrelation lag',
                'type' => 'number',
                'default' => '8',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'series_curve',
            'rolling_mean',
            'acf_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'economics-forecasting-scenario-tool',
        'title' => 'Economics Forecasting and Scenario Tool',
        'domain' => 'Economics',
        'topic' => 'Economic Forecasting and Scenarios',
        'family' => 'economic_forecasting',
        'engine' => 'python/numpy + optional R',
        'description' => 'Macro scenario indices, demand forecasting, fiscal multiplier scenarios, cost-benefit streams, uncertainty framing, and policy-analysis outputs.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'macro_scenario',
                'help' => '',
                'options' => [
                    'macro_scenario',
                    'demand_forecast',
                    'fiscal_multiplier',
                    'cost_benefit'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'gdp_growth=0.02;inflation=0.03;unemployment=0.05;policy_rate=0.04;demand=1000;price=10;elasticity=-1.2;shock=-0.1;multiplier=1.5',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'scenario_curve',
            'demand_curve',
            'bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'econometrics-policy-model-tool',
        'title' => 'Econometrics and Policy Model Tool',
        'domain' => 'Economics',
        'topic' => 'Econometrics and Policy Evaluation',
        'family' => 'econometrics',
        'engine' => 'python/numpy + optional R',
        'description' => 'OLS, elasticity regression, difference-in-differences decomposition, fitted values, residuals, and identification warnings for policy/economic analysis.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'ols',
                'help' => '',
                'options' => [
                    'ols',
                    'elasticity_regression',
                    'difference_in_differences'
                ]
            ],
            [
                'name' => 'data',
                'label' => 'Rows: predictors then outcome',
                'type' => 'textarea',
                'default' => '1,2\n2,4\n3,5\n4,7\n5,8',
                'help' => ''
            ],
            [
                'name' => 'x',
                'label' => 'X values',
                'type' => 'text',
                'default' => '10,11,12,13,14,15',
                'help' => ''
            ],
            [
                'name' => 'y',
                'label' => 'Y values',
                'type' => 'text',
                'default' => '100,94,90,82,78,73',
                'help' => ''
            ],
            [
                'name' => 'inputs',
                'label' => 'Policy contrast inputs',
                'type' => 'textarea',
                'default' => 'pre_treated=10;post_treated=16;pre_control=9;post_control=11',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'fit_curve',
            'residuals',
            'did_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'fpga-digital-systems-tool',
        'title' => 'FPGA and Digital Systems Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'FPGA and Digital Design',
        'family' => 'fpga',
        'engine' => 'python/numpy + HDL workflow adapters',
        'description' => 'Timing slack, estimated Fmax, fixed-point range/quantization, pipeline throughput, resource pressure, and CDC-risk proxies for FPGA programmers.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'timing_slack',
                'help' => '',
                'options' => [
                    'timing_slack',
                    'fixed_point',
                    'pipeline_throughput',
                    'resource_pressure'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'clock_mhz=100;critical_path_ns=7.5;lut_count=20000;bram_kb=1024;dsp_blocks=80;word_bits=16;pipeline_stages=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'timing_bar',
            'resource_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'power-systems-engineering-tool',
        'title' => 'Power Systems Engineering Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Electrical Power Engineering',
        'family' => 'power_systems',
        'engine' => 'python/numpy',
        'description' => 'Three-phase power, voltage drop, power-factor correction, transformer/loading, and fault-current proxy calculations for electrical engineers.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'three_phase_power',
                'help' => '',
                'options' => [
                    'three_phase_power',
                    'voltage_drop',
                    'power_factor_correction',
                    'fault_current_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'voltage_v=480;current_a=100;power_factor=0.85;length_m=100;resistance_ohm_per_km=0.2;reactance_ohm_per_km=0.08',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'power_bar',
            'load_curve',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'mechanical-systems-engineering-tool',
        'title' => 'Mechanical Systems Engineering Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Mechanical Engineering',
        'family' => 'mechanical_systems',
        'engine' => 'python/numpy',
        'description' => 'Shaft torsion, vibration frequency, fatigue proxies, conduction heat transfer, and mechanical-system interpretation with professional caveats.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'shaft_torsion',
                'help' => '',
                'options' => [
                    'shaft_torsion',
                    'vibration_frequency',
                    'fatigue_proxy',
                    'conduction_heat_transfer'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'torque_nm=500;radius_m=0.025;polar_j_m4=6.14e-7;length_m=1;shear_modulus_pa=79e9;mass_kg=10;stiffness_n_m=10000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'vibration_curve',
            'stress_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'structural-engineering-tool',
        'title' => 'Structural Engineering Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Structural Engineering',
        'family' => 'structural_engineering',
        'engine' => 'python/numpy',
        'description' => 'Beam deflection, moment/shear proxies, Euler buckling, load combinations, and seismic base-shear proxy calculations with strict safety caveats.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'beam_deflection',
                'help' => '',
                'options' => [
                    'beam_deflection',
                    'column_buckling',
                    'load_combination',
                    'seismic_base_shear_proxy'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'span_m=6;uniform_load_kn_m=10;E_pa=200e9;I_m4=8e-6;dead_load=100;live_load=75;wind_load=40',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'moment_curve',
            'load_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'civil-infrastructure-planning-tool',
        'title' => 'Civil Infrastructure Planning Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Civil Infrastructure',
        'family' => 'civil_infrastructure',
        'engine' => 'python/numpy',
        'description' => 'Stormwater storage, water demand, capacity utilization, asset-risk priority, and infrastructure planning metrics.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'stormwater_storage',
                'help' => '',
                'options' => [
                    'stormwater_storage',
                    'water_demand',
                    'capacity_utilization',
                    'asset_condition_risk'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'area_ha=2;rainfall_mm=50;runoff_coefficient=0.7;population=10000;daily_l_per_capita=180;capacity=12000;demand=9000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'risk_bar',
            'capacity_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'urban-planning-analytics-tool',
        'title' => 'Urban Planning Analytics Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Urban Planning',
        'family' => 'urban_planning',
        'engine' => 'python/numpy + GIS-ready',
        'description' => 'Density, jobs-housing balance, land-use mix entropy, housing affordability, accessibility proxies, and planning-equity caveats.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'land_use_mix',
                'help' => '',
                'options' => [
                    'land_use_mix',
                    'density_access',
                    'housing_affordability'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'population=50000;area_km2=12;jobs=25000;housing_units=22000;income=65000;housing_cost_monthly=1600;residential=0.45;commercial=0.25;industrial=0.1;civic=0.1;open_space=0.1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'land_use_bar',
            'density_table',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'architecture-building-science-tool',
        'title' => 'Architecture and Building Science Tool',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Architecture and Building Science',
        'family' => 'building_science',
        'engine' => 'python/numpy + EnergyPlus/IFC-ready',
        'description' => 'HVAC load proxies, daylight ratios, egress/occupancy metrics, envelope performance, embodied carbon, and building-science reports.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'hvac_load_proxy',
                'help' => '',
                'options' => [
                    'hvac_load_proxy',
                    'egress_occupancy',
                    'daylight_proxy',
                    'embodied_carbon'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'area_m2=1000;u_value=0.35;delta_t_k=20;window_area_m2=150;shgc=0.35;solar_w_m2=500;occupants=120;floor_area_m2=1000',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'building_load_bar',
            'daylight_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'astrophysics-research-calculator',
        'title' => 'Astrophysics Research Calculator',
        'domain' => 'Professional Systems Layer',
        'topic' => 'Astrophysics and Space Science',
        'family' => 'astrophysics',
        'engine' => 'python/numpy',
        'description' => 'Blackbody spectra, luminosity, low-redshift Hubble estimates, Kepler orbital periods, and astrophysical research calculators.',
        'inputs' => [
            [
                'name' => 'mode',
                'label' => 'Mode',
                'type' => 'select',
                'default' => 'blackbody',
                'help' => '',
                'options' => [
                    'blackbody',
                    'luminosity',
                    'redshift_hubble',
                    'kepler_orbit'
                ]
            ],
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'temperature_k=5778;radius_m=6.957e8;redshift=0.05;period_days=365.25;semi_major_axis_au=1',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'spectrum_curve',
            'orbital_summary',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'cognitive-psychology-tool',
        'title' => 'Cognitive Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Cognitive Psychology',
        'family' => 'cognitive_psychology',
        'engine' => 'python/numpy',
        'description' => 'Attention, working memory, mental models, cognitive load, and transfer analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'attention=4;working_memory=3;mental_models=4;cognitive_load=2;transfer=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'profile_bar',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'developmental-psychology-tool',
        'title' => 'Developmental Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Developmental Psychology',
        'family' => 'developmental_psychology',
        'engine' => 'python/numpy',
        'description' => 'Developmental dimensions across cognition, social development, language, emotion regulation, and context support.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'cognitive_development=3;social_development=4;language=3;emotion_regulation=3;context_support=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'profile_bar'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'personality-psychology-tool',
        'title' => 'Personality Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Personality Psychology',
        'family' => 'personality_psychology',
        'engine' => 'python/numpy',
        'description' => 'Big-Five-style reflective personality profile for education and self-analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Trait scores',
                'type' => 'textarea',
                'default' => 'openness=4;conscientiousness=4;extraversion=3;agreeableness=4;emotional_stability=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'trait_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'positive-psychology-tool',
        'title' => 'Positive Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Positive Psychology',
        'family' => 'positive_psychology',
        'engine' => 'python/numpy',
        'description' => 'PERMA-style wellbeing, strengths, meaning, engagement, relationships, and accomplishment profile.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'meaning=4;engagement=3;relationships=4;accomplishment=3;positive_emotion=3;strengths_use=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'wellbeing_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'organizational-psychology-tool',
        'title' => 'Organizational Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Organizational Psychology',
        'family' => 'organizational_psychology',
        'engine' => 'python/numpy',
        'description' => 'Role clarity, psychological safety, motivation, coordination, feedback, and burnout-risk review.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'role_clarity=3;psychological_safety=3;motivation=4;coordination=3;feedback=2;burnout_risk_inverse=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'organization_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'institutional-psychology-tool',
        'title' => 'Institutional Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Institutional Psychology',
        'family' => 'institutional_psychology',
        'engine' => 'python/numpy',
        'description' => 'Trust, legitimacy, norms, accountability, institutional learning, and symbolic coherence.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'trust=3;legitimacy=3;norm_clarity=3;accountability=3;learning_capacity=3;symbolic_coherence=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'institution_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'analytical-psychology-symbolism-tool',
        'title' => 'Analytical Psychology, Symbolism, and Depth Mind Tool',
        'domain' => 'Psychology',
        'topic' => 'Analytical Psychology, Symbolism & the Depth Mind',
        'family' => 'analytical_psychology',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Symbolic, archetypal, shadow, integration, and narrative-depth analysis for stories, myths, images, and institutions.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'symbol_density=4;archetypal_pattern=4;shadow_tension=3;integration_potential=3;narrative_depth=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'symbol_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'behavioral-science-psychology-hub-tool',
        'title' => 'Behavioral Science and Psychology Hub Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Behavioral Science & Psychology Hub',
        'family' => 'behavioral_science',
        'engine' => 'python/numpy',
        'description' => 'Behavior definition, context mapping, measurement, intervention fit, ethics, and evaluation.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'behavior_definition=4;context_mapping=3;measurement=3;intervention_fit=3;ethics=4;evaluation=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'behavior_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'behavioral-economics-tool',
        'title' => 'Behavioral Economics Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Behavioral Economics',
        'family' => 'behavioral_economics',
        'engine' => 'python/numpy',
        'description' => 'Loss aversion, present bias, framing, status quo bias, social proof, and choice friction.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'loss_aversion=3;present_bias=4;status_quo_bias=3;framing_effect=4;social_proof=3;choice_friction=2',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'bias_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'behavior-change-habit-tool',
        'title' => 'Behavior Change and Habit Formation Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Behavior Change and Habit Formation',
        'family' => 'behavior_change',
        'engine' => 'python/numpy',
        'description' => 'Cue, routine, reward, friction, identity, and feedback-loop habit analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'cue_clarity=3;routine_feasibility=3;reward_strength=3;friction_reduction=3;identity_alignment=4;feedback_loop=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'habit_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'motivation-reinforcement-learning-tool',
        'title' => 'Motivation, Reinforcement, and Learning Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Motivation, Reinforcement, and Learning',
        'family' => 'motivation_learning',
        'engine' => 'python/numpy',
        'description' => 'Intrinsic motivation, reinforcement schedule, competence feedback, autonomy, and mastery progress.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'intrinsic_motivation=4;extrinsic_support=3;reinforcement_schedule=3;competence_feedback=3;autonomy=4;mastery_progress=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'motivation_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'choice-architecture-nudging-tool',
        'title' => 'Choice Architecture and Nudging Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Choice Architecture and Nudging',
        'family' => 'choice_architecture',
        'engine' => 'python/numpy',
        'description' => 'Default design, salience, friction, transparency, agency, and equity analysis for ethical nudging.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'default_design=3;salience=3;friction=2;transparency=4;user_agency=4;equity=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'choice_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'ethics_review_required'
    ],
    [
        'id' => 'social-norms-influence-tool',
        'title' => 'Social Norms and Behavioral Influence Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Social Norms and Behavioral Influence',
        'family' => 'social_norms',
        'engine' => 'python/numpy',
        'description' => 'Descriptive norms, injunctive norms, reference groups, visibility, trust, and backfire risk.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'descriptive_norms=3;injunctive_norms=3;reference_group_fit=3;visibility=3;trust=3;backfire_risk_inverse=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'norm_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'behavioral-public-policy-tool',
        'title' => 'Behavioral Public Policy Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Behavioral Public Policy',
        'family' => 'behavioral_public_policy',
        'engine' => 'python/numpy',
        'description' => 'Behavioral public-policy evaluation across evidence, equity, transparency, feasibility, and evaluation.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'problem_definition=4;evidence_base=3;distributional_equity=4;consent_transparency=4;administrative_feasibility=3;evaluation_plan=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'policy_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'behavioral-research-methods-tool',
        'title' => 'Behavioral Research Methods Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Behavioral Research Methods',
        'family' => 'behavioral_methods',
        'engine' => 'python/numpy',
        'description' => 'Construct validity, sampling, reliability, experimental design, confounding control, and replicability.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'construct_validity=3;sampling=3;measurement_reliability=3;experimental_design=3;confounding_control=3;replicability=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'methods_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'ethics-behavioral-intervention-tool',
        'title' => 'Ethics of Behavioral Intervention Tool',
        'domain' => 'Behavioral Science & Psychology',
        'topic' => 'Ethics of Behavioral Intervention',
        'family' => 'behavioral_ethics',
        'engine' => 'python/numpy',
        'description' => 'Autonomy, beneficence, nonmaleficence, justice, transparency, and contestability safeguards.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'autonomy=4;beneficence=4;nonmaleficence=4;justice=3;transparency=4;contestability=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'ethics_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'ethics_review_required'
    ],
    [
        'id' => 'moral-psychology-tool',
        'title' => 'Moral Psychology Tool',
        'domain' => 'Psychology',
        'topic' => 'Moral Psychology',
        'family' => 'moral_psychology',
        'engine' => 'python/numpy',
        'description' => 'Moral foundations, empathy, fairness, authority, liberty, harm/care, and institutional judgment analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'harm_care=4;fairness=4;loyalty=3;authority=2;sanctity=2;liberty=4;empathy=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'moral_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'knowledge-architecture-tool',
        'title' => 'Knowledge Architecture Tool',
        'domain' => 'Thinking',
        'topic' => 'Knowledge Architecture',
        'family' => 'knowledge_architecture',
        'engine' => 'python/numpy',
        'description' => 'Taxonomy, navigation, metadata, source traceability, learning pathways, and governance analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'taxonomy=4;navigation=3;metadata=3;source_traceability=4;learning_pathways=3;governance=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'architecture_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'design-thinking-tool',
        'title' => 'Design Thinking Tool',
        'domain' => 'Thinking',
        'topic' => 'Design Thinking',
        'family' => 'design_thinking',
        'engine' => 'python/numpy',
        'description' => 'Empathy, problem framing, ideation, prototyping, testing, and iteration analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'empathy=3;problem_framing=4;ideation=4;prototyping=3;testing=3;iteration=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'design_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'mathematical-thinking-tool',
        'title' => 'Mathematical Thinking Tool',
        'domain' => 'Thinking',
        'topic' => 'Mathematical Thinking',
        'family' => 'mathematical_thinking',
        'engine' => 'python/numpy',
        'description' => 'Abstraction, formalization, proof logic, model fit, edge cases, and interpretation.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'abstraction=4;formalization=3;proof_logic=3;model_fit=3;edge_cases=4;interpretation=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'math_thinking_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'systems-thinking-tool',
        'title' => 'Systems Thinking Tool',
        'domain' => 'Thinking',
        'topic' => 'Systems Thinking',
        'family' => 'systems_thinking',
        'engine' => 'python/numpy',
        'description' => 'Boundaries, stocks, flows, feedback loops, delays, leverage points, emergence, and unintended consequences.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'boundaries=4;stocks_flows=3;feedback_loops=4;delays=3;leverage_points=3;emergence=3;unintended_consequences=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'systems_profile',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'algorithms-computational-reasoning-tool',
        'title' => 'Algorithms and Computational Reasoning Tool',
        'domain' => 'Thinking',
        'topic' => 'Algorithms & Computational Reasoning',
        'family' => 'computational_reasoning',
        'engine' => 'python/numpy',
        'description' => 'Problem formalization, data structures, complexity, correctness, testing, and accountability.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'problem_formalization=4;data_structures=3;complexity=3;correctness=4;testing=3;accountability=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'computational_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'resilience-thinking-tool',
        'title' => 'Resilience Thinking Tool',
        'domain' => 'Thinking',
        'topic' => 'Resilience Thinking',
        'family' => 'resilience_thinking',
        'engine' => 'python/numpy',
        'description' => 'Exposure, sensitivity, adaptive capacity, redundancy, learning, recovery, and transformability.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'exposure=4;sensitivity_inverse=3;adaptive_capacity=3;redundancy=3;learning=4;recovery=3;transformability=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'resilience_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'futures-thinking-tool',
        'title' => 'Futures Thinking Tool',
        'domain' => 'Thinking',
        'topic' => 'Futures Thinking',
        'family' => 'futures_thinking',
        'engine' => 'python/numpy',
        'description' => 'Drivers, uncertainties, scenarios, early signals, robust options, and adaptation pathways.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'drivers=4;uncertainties=4;scenarios=3;early_signals=3;robust_options=3;adaptation_pathways=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'futures_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'strategic-ideation-tool',
        'title' => 'Strategic Ideation Tool',
        'domain' => 'Problem Solving',
        'topic' => 'Strategic Ideation',
        'family' => 'strategic_ideation',
        'engine' => 'python/numpy',
        'description' => 'Problem clarity, option diversity, constraints, differentiation, feasibility, and learning value.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'problem_clarity=4;option_diversity=4;constraint_awareness=3;differentiation=4;feasibility=3;learning_value=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'strategy_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'beauty-aesthetics-meaning-tool',
        'title' => 'Beauty, Aesthetics, and Meaning Tool',
        'domain' => 'Meaning',
        'topic' => 'Beauty, Aesthetics, and Meaning',
        'family' => 'aesthetics_meaning',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Form, pattern, harmony, symbolic depth, emotional resonance, and transcendence analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'form=4;pattern=4;harmony=3;symbolic_depth=4;emotional_resonance=4;transcendence=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'meaning_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'aesthetics-philosophy-art-tool',
        'title' => 'Aesthetics and Philosophy of Art Tool',
        'domain' => 'Meaning',
        'topic' => 'Aesthetics and the Philosophy of Art',
        'family' => 'philosophy_art',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Representation, expression, formal structure, interpretive openness, historical context, and judgment.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'representation=3;expression=4;formalist_structure=4;interpretive_openness=4;historical_context=3;judgment=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'art_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'mathematics-art-music-pattern-tool',
        'title' => 'Mathematics, Art, Music, and Pattern Tool',
        'domain' => 'Meaning',
        'topic' => 'Mathematics, Art, Music, and Pattern',
        'family' => 'math_art_music_pattern',
        'engine' => 'python/numpy',
        'description' => 'Symmetry, ratio, recursion, rhythm, variation, and emergent pattern analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'symmetry=4;ratio=4;recursion=3;rhythm=4;variation=3;emergent_pattern=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'pattern_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'symbolism-style-cultural-meaning-tool',
        'title' => 'Symbolism, Style, and Cultural Meaning Tool',
        'domain' => 'Meaning',
        'topic' => 'Symbolism, Style, and Cultural Meaning',
        'family' => 'symbolism_style',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Symbol density, style coherence, cultural context, ritual association, memory, and ambiguity.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'symbol_density=4;style_coherence=3;cultural_context=4;ritual_association=3;memory=4;ambiguity=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'symbolism_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'creative-form-composition-interpretation-tool',
        'title' => 'Creative Form, Composition, and Interpretation Tool',
        'domain' => 'Meaning',
        'topic' => 'Creative Form, Composition, and Interpretation',
        'family' => 'creative_form',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Structure, tension, contrast, unity, movement, and interpretive depth analysis.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'structure=4;tension=3;contrast=4;unity=3;movement=3;interpretive_depth=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'composition_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'story-myth-meaning-tool',
        'title' => 'Story, Myth, and Meaning Tool',
        'domain' => 'Meaning',
        'topic' => 'Story, Myth, and Meaning',
        'family' => 'story_myth_meaning',
        'engine' => 'python/numpy + AI-ready',
        'description' => 'Mythic structure, ritual depth, archetypal motif, memory, suffering/hope, and sacred order.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'mythic_structure=4;ritual_depth=3;archetypal_motif=4;memory=4;suffering_hope=3;sacred_order=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'myth_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'systems-modeling-tool',
        'title' => 'Systems Modeling Tool',
        'domain' => 'Systems Modeling',
        'topic' => 'Systems Modeling',
        'family' => 'systems_modeling',
        'engine' => 'python/numpy',
        'description' => 'Boundary definition, variable quality, causal structure, feedback representation, calibration, validation, and scenario design.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'boundary_definition=4;variable_quality=3;causal_structure=4;feedback_representation=3;data_calibration=3;validation=3;scenario_design=4',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'modeling_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'predictive-modeling-tool',
        'title' => 'Predictive Analytics',
        'domain' => 'Predictive Modeling',
        'topic' => 'predictive_modeling',
        'family' => 'predictive_modeling',
        'engine' => 'python/numpy',
        'description' => 'Target definition, feature quality, training data, validation design, calibration, uncertainty, and deployment monitoring.',
        'inputs' => [
            [
                'name' => 'scores',
                'label' => 'Dimension scores',
                'type' => 'textarea',
                'default' => 'target_definition=4;feature_quality=3;training_data=3;validation_design=4;calibration=3;uncertainty=3;deployment_monitoring=3',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'predictive_readiness_profile'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'limits-to-growth-system-dynamics-tool',
        'title' => 'Limits to Growth System Dynamics Tool',
        'domain' => 'Systems Modeling',
        'topic' => 'Limits to Growth',
        'family' => 'limits_to_growth',
        'engine' => 'python/numpy',
        'description' => 'Simplified stocks, flows, feedback, resource depletion, pollution, overshoot, and collapse-risk scenario modeling.',
        'inputs' => [
            [
                'name' => 'inputs',
                'label' => 'Inputs',
                'type' => 'textarea',
                'default' => 'population=1.0;capital=1.0;resources=1.0;pollution=0.05;birth_rate=0.025;death_rate=0.01;investment_rate=0.04;depletion_rate=0.015;pollution_rate=0.02;years=80',
                'help' => ''
            ]
        ],
        'graph_types' => [
            'system_dynamics_curve',
            'pdf_report'
        ],
        'audience_modes' => [
            'guided',
            'analyst',
            'expert'
        ],
        'safety_level' => 'professional_review_required'
    ],
    // v0.9.8 equation-derived feature tools built from the Feature Builder CSV.
    [
        'id' => 'article-equation-tool-router',
        'title' => 'Article Equation-to-Tool Router',
        'domain' => 'Workbench infrastructure',
        'topic' => 'calculator/backlog',
        'family' => 'article_router',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Map each article’s equations to the most relevant calculator modules and hide irrelevant tools.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'post_slug=sample-article;equation=S_{t+1}=S_t+I_t-O_t;suggested_domain=Systems Modeling;context=stock flow recurrence and system dynamics', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'equation-registry-cleaner',
        'title' => 'Equation Registry Cleaner and Feature Builder',
        'domain' => 'Workbench infrastructure',
        'topic' => 'calculator/backlog',
        'family' => 'registry_cleaner',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Clean, deduplicate, classify, and export equations from WordPress for future tools.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'equations=S_{t+1}=S_t+I_t-O_t; x_{t+1}=x_t(1+r); \\)</td> <td>bad fragment</td>; A; R=P(H)\\times C(H)', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'economics-systems-policy-calculator',
        'title' => 'Economics, Welfare, and Policy Systems Calculator',
        'domain' => 'Economics',
        'topic' => 'calculator/backlog',
        'family' => 'economics_policy',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Model prosperity beyond GDP, welfare tradeoffs, inequality, institutional quality, and ecological cost.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'output=0.8;health=0.78;education=0.74;institutions=0.66;ecology=0.52;inequality=0.35;weights=0.25,0.2,0.18,0.17,0.2', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'weighted-composite-index-builder',
        'title' => 'Weighted Composite Index Builder',
        'domain' => 'Decision science / indicators',
        'topic' => 'calculator/module',
        'family' => 'weighted_index',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Build indices for prosperity, resilience, policy coherence, content completeness, governance capacity, and risk.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'health=0.82;education=0.76;institutions=0.68;ecology=0.55;resilience=0.72;weights=0.25,0.2,0.2,0.2,0.15', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'electrical-rf-power-design-tool',
        'title' => 'Electrical, RF, and Power Design Tool',
        'domain' => 'Electrical / RF / power',
        'topic' => 'calculator/module',
        'family' => 'rf_link',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support circuits, impedance, filters, RF, antenna, link budgets, and power systems.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'frequency_hz=915e6;distance_km=1;tx_power_dbm=20;tx_gain_dbi=2;rx_gain_dbi=2;losses_db=2', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'weighted-index-builder',
        'title' => 'Weighted Index and Composite Score Builder',
        'domain' => 'Decision science / indicators',
        'topic' => 'calculator/backlog',
        'family' => 'weighted_index',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Build composite indicators from weighted components for prosperity, resilience, policy coherence, and governance.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'health=0.82;education=0.76;institutions=0.68;ecology=0.55;resilience=0.72;weights=0.25,0.2,0.2,0.2,0.15', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'predictive-forecasting-suite',
        'title' => 'Predictive Analytics Forecasting Suite',
        'domain' => 'Predictive analytics',
        'topic' => 'calculator/backlog',
        'family' => 'forecasting',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Forecast trends, compare scenarios, inspect model fit, and evaluate uncertainty.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'series=120,128,133,140,145,151,160,171,178,190,203,215;horizon=6;mode=linear_trend', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'environmental-monitoring-threshold-tool',
        'title' => 'Environmental Monitoring Threshold and QA/QC Tool',
        'domain' => 'Environmental monitoring',
        'topic' => 'calculator/backlog',
        'family' => 'environmental_qaqc',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Evaluate sensor series, thresholds, exceedances, outliers, missing data, and monitoring quality.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'series=7.1,7.4,8.0,12.5,7.9,7.6,7.5,,7.3,13.0;threshold=10;lower_limit=6;upper_limit=10', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'recurrence-dynamics-calculator',
        'title' => 'Discrete-Time Recurrence and Feedback Calculator',
        'domain' => 'Systems modeling',
        'topic' => 'calculator/backlog',
        'family' => 'recurrence',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Simulate discrete-time updates, feedback response, compounding growth, and constrained dynamics.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'x0=10;rate=0.08;inflow=1;outflow=0.2;steps=24;capacity=100', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'ode-phase-stability-tool',
        'title' => 'ODE, Phase Plane, and Stability Analyzer',
        'domain' => 'Differential equations',
        'topic' => 'calculator/backlog',
        'family' => 'ode',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Solve and visualize ordinary differential equations, equilibria, and stability behavior.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'model=logistic;x0=10;rate=0.25;carrying_capacity=100;time=30;dt=0.1', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'risk-impact-resilience-calculator',
        'title' => 'Risk, Impact, and Resilience Matrix Calculator',
        'domain' => 'Risk / resilience',
        'topic' => 'calculator/backlog',
        'family' => 'risk_matrix',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compute risk from probability, consequence, exposure, vulnerability, resilience, and uncertainty.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'probability=0.25;consequence=80;exposure=0.7;vulnerability=0.6;adaptive_capacity=0.4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'stock-flow-systems-simulator',
        'title' => 'Stock-Flow and Accumulation Simulator',
        'domain' => 'Systems modeling',
        'topic' => 'calculator/backlog',
        'family' => 'stock_flow',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Model stocks, inflows, outflows, depletion, replenishment, leakage, and carrying capacity.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'initial=100;inflows=12,14,13,15,16,15;outflows=8,9,10,11,10,12;steps=6', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'graphable-function-explorer',
        'title' => 'Graphable Function and Symbolic Relationship Explorer',
        'domain' => 'Mathematical modeling',
        'topic' => 'calculator/backlog',
        'family' => 'ode',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Plot and explain symbolic functions from article equations when variables are defined.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'model=logistic;x0=10;rate=0.25;carrying_capacity=100;time=30;dt=0.1', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'planetary-boundaries-pressure-index',
        'title' => 'Planetary Boundaries and Anthropocene Pressure Index',
        'domain' => 'Sustainability / Earth systems',
        'topic' => 'calculator/backlog',
        'family' => 'weighted_index',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Estimate cumulative Earth-system pressure across climate, biosphere, freshwater, land, nutrients, and pollution.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'health=0.82;education=0.76;institutions=0.68;ecology=0.55;resilience=0.72;weights=0.25,0.2,0.2,0.2,0.15', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'time-series-diagnostics-toolkit',
        'title' => 'Time-Series Diagnostics and Change Detection Tool',
        'domain' => 'Predictive analytics',
        'topic' => 'calculator/backlog',
        'family' => 'forecasting',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Check trend, autocorrelation, seasonality, structural breaks, lag effects, and forecast readiness.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'series=120,128,133,140,145,151,160,171,178,190,203,215;horizon=6;mode=linear_trend', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'limits-to-growth-system-dynamics',
        'title' => 'Limits to Growth Scenario Simulator',
        'domain' => 'Systems dynamics',
        'topic' => 'calculator/backlog',
        'family' => 'limits_growth',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Simulate population, resources, pollution, capital, food, and feedback delays under scenarios.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'population=1.0;capital=1.0;resources=1.0;pollution=0.05;birth_rate=0.025;death_rate=0.01;investment_rate=0.04;depletion_rate=0.015;pollution_rate=0.02;years=80', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'climate-energy-balance-tool',
        'title' => 'Climate Forcing and Energy Balance Calculator',
        'domain' => 'Climate / energy',
        'topic' => 'calculator/backlog',
        'family' => 'climate_balance',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze simplified radiative forcing, warming response, emissions trajectories, and energy-balance assumptions.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'co2_ppm=425;baseline_co2_ppm=280;climate_sensitivity_c=3.0;forcing_other=0.4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'population-ecology-growth-tool',
        'title' => 'Population, Ecology, and Logistic Growth Tool',
        'domain' => 'Biology / ecology',
        'topic' => 'calculator/backlog',
        'family' => 'population_ecology',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Model exponential/logistic growth, carrying capacity, population pressure, and ecological limits.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'initial=100;rate=0.22;carrying_capacity=1000;time=40;harvest_rate=0.02', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'predictive-model-diagnostics-suite',
        'title' => 'Predictive Model Diagnostics Suite',
        'domain' => 'Predictive analytics',
        'topic' => 'calculator/module',
        'family' => 'forecasting',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support forecasting, regression, residuals, uncertainty, validation, and model interpretation.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'series=120,128,133,140,145,151,160,171,178,190,203,215;horizon=6;mode=linear_trend', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'content-framework-coverage-scorer',
        'title' => 'Content Framework Coverage and Evidence Scorer',
        'domain' => 'Content frameworks',
        'topic' => 'calculator/module',
        'family' => 'weighted_index',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Turn content-framework equations into article quality, completeness, support, and balance tools.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'health=0.82;education=0.76;institutions=0.68;ecology=0.55;resilience=0.72;weights=0.25,0.2,0.2,0.2,0.15', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'chemistry-lab-equilibrium-calculator',
        'title' => 'Chemistry Lab, Equilibrium, and Solution Calculator',
        'domain' => 'Chemistry / lab science',
        'topic' => 'calculator/module',
        'family' => 'chemistry_lab',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support chemistry articles with solutions, equilibrium, thermodynamics, and lab prep calculations.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mode=molarity;moles=0.5;volume_l=1.0;acid_m=0.01;ka=1.8e-5;initial_a=1.0;initial_b=1.0;k_eq=4.0', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'relativity-cosmology-calculator',
        'title' => 'Relativity and Cosmology Calculator',
        'domain' => 'Astrophysics / cosmology',
        'topic' => 'calculator/module',
        'family' => 'relativity_cosmology',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support spacetime, curvature, cosmology, expansion, and large-scale structure articles.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass_kg=5.972e24;radius_m=6371000;redshift=0.1;h0_km_s_mpc=70;distance_mpc=100', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'recurrence-feedback-simulator',
        'title' => 'Discrete Recurrence and Feedback Simulator',
        'domain' => 'Systems dynamics',
        'topic' => 'calculator/module',
        'family' => 'recurrence',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze feedback, lag, state-transition, and scenario behavior in discrete time.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'x0=10;rate=0.08;inflow=1;outflow=0.2;steps=24;capacity=100', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'chemistry-equilibrium-acid-base-tool',
        'title' => 'Chemistry Equilibrium and Acid-Base Calculator',
        'domain' => 'Chemistry',
        'topic' => 'calculator/backlog',
        'family' => 'chemistry_lab',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Solve weak acid/base equilibrium, pH, buffers, titration, and reaction balance examples.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mode=molarity;moles=0.5;volume_l=1.0;acid_m=0.01;ka=1.8e-5;initial_a=1.0;initial_b=1.0;k_eq=4.0', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'physics-field-theory-workbench',
        'title' => 'Physics Field Theory and Lagrangian Workbench',
        'domain' => 'Advanced physics',
        'topic' => 'calculator/module',
        'family' => 'advanced_physics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support advanced physics articles with Lagrangian, Hamiltonian, field, and variational reasoning.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass_mev_c2=0.511;momentum_mev_c=1.0;half_life_s=3600;time_s=7200;lagrangian_terms=kinetic_minus_potential', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'optimization-constraint-solver',
        'title' => 'Optimization and Constraint Solver',
        'domain' => 'Optimization',
        'topic' => 'calculator/module',
        'family' => 'optimization',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Evaluate constrained tradeoffs, feasible sets, and objective-function choices.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'objective=3,2;constraints=1,1,10;2,1,14;0,1,8;maximize=true', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'optimization-constraint-tool',
        'title' => 'Optimization and Constraint Calculator',
        'domain' => 'Optimization',
        'topic' => 'calculator/backlog',
        'family' => 'optimization',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Solve constrained decision problems, tradeoffs, feasible sets, and objective functions.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'objective=3,2;constraints=1,1,10;2,1,14;0,1,8;maximize=true', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'linear-algebra-model-diagnostics',
        'title' => 'Linear Algebra Model Diagnostics',
        'domain' => 'Linear algebra',
        'topic' => 'calculator/backlog',
        'family' => 'forecasting',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Solve systems and inspect rank, conditioning, eigenstructure, SVD, and model identifiability.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'series=120,128,133,140,145,151,160,171,178,190,203,215;horizon=6;mode=linear_trend', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'causal-inference-effect-tool',
        'title' => 'Causal Effect and Counterfactual Calculator',
        'domain' => 'Causal inference',
        'topic' => 'calculator/backlog',
        'family' => 'causal',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Estimate and explain treatment effects, counterfactuals, confounding, and matched comparisons.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'treated=12,14,16,18,19;control=10,11,13,13,14', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'algorithmic-complexity-calculator',
        'title' => 'Algorithmic Complexity and Scaling Calculator',
        'domain' => 'Algorithms',
        'topic' => 'calculator/backlog',
        'family' => 'complexity',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compare computational growth rates, runtime scaling, throughput, latency budgets, and bottlenecks.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'n=10,100,1000,10000;model=nlogn;unit_cost=1', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'bayesian-evidence-updater',
        'title' => 'Bayesian Evidence and Belief Update Calculator',
        'domain' => 'Probability / inference',
        'topic' => 'calculator/backlog',
        'family' => 'bayesian',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Turn prior, likelihood, and evidence into posterior reasoning and uncertainty updates.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'prior=0.1;sensitivity=0.9;specificity=0.95;positive=true', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'network-cascade-graph-tool',
        'title' => 'Network Dependency and Cascade Risk Tool',
        'domain' => 'Graph systems',
        'topic' => 'calculator/backlog',
        'family' => 'risk_matrix',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze dependency networks, cascades, centrality, bottlenecks, and failure propagation.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'probability=0.25;consequence=80;exposure=0.7;vulnerability=0.6;adaptive_capacity=0.4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'policy-coherence-tradeoff-tool',
        'title' => 'Policy Coherence, Synergy, and Tradeoff Calculator',
        'domain' => 'Governance / policy',
        'topic' => 'calculator/backlog',
        'family' => 'policy_coherence',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Measure policy contradiction, synergy, spillover risk, monitoring quality, and coordination capacity.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'sector_progress=0.72;synergy=0.22;tradeoff=0.18;spillover=0.12;coordination=0.65;monitoring=0.58', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'eigen-stability-calculator',
        'title' => 'Eigenvalue Stability and State Transition Calculator',
        'domain' => 'Linear systems',
        'topic' => 'calculator/backlog',
        'family' => 'linear_algebra',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze whether matrix-driven systems converge, oscillate, diverge, or decouple.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'matrix=[[0.8,0.1],[0.2,0.7]];vector=[1,0]', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'mechanics-energy-momentum-tool',
        'title' => 'Physics Mechanics, Energy, and Momentum Calculator',
        'domain' => 'Physics',
        'topic' => 'calculator/backlog',
        'family' => 'physics_mechanics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compute forces, work, energy, momentum, torque, rotation, and idealized mechanical systems.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass=2;velocity=12;height=5;force=10;distance=3;angle_deg=0', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'psychology-scale-reliability-tool',
        'title' => 'Psychology Scale and Construct Reliability Tool',
        'domain' => 'Psychology / behavioral science',
        'topic' => 'calculator/backlog',
        'family' => 'psychometrics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compute scale scores, Cronbach-style reliability, factor/construct checks, and group comparisons.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'items=4,5,4,3,5;4,4,5,3,4;5,5,4,4,5;3,4,3,3,4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'quantum-nuclear-particle-physics-tool',
        'title' => 'Quantum, Nuclear, and Particle Physics Education Calculator',
        'domain' => 'Advanced physics',
        'topic' => 'calculator/backlog',
        'family' => 'advanced_physics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support safe educational calculations for wave functions, uncertainty, decay, event rates, and particle units.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass_mev_c2=0.511;momentum_mev_c=1.0;half_life_s=3600;time_s=7200;lagrangian_terms=kinetic_minus_potential', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'content-framework-completeness-tool',
        'title' => 'Content Framework Completeness and Evidence Support Calculator',
        'domain' => 'Content frameworks',
        'topic' => 'calculator/backlog',
        'family' => 'content_profile',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Score explanatory completeness, evidence support, balance, audience path, and governance needs.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'purpose=4;evidence=3;structure=4;audience=4;ethics=5;measurement=3', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'rf-antenna-link-budget-tool',
        'title' => 'RF, Antenna, and Link Budget Calculator',
        'domain' => 'RF / communications',
        'topic' => 'calculator/backlog',
        'family' => 'rf_link',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compute wavelength, link budget, free-space path loss, antenna gain, impedance, and noise margin.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'frequency_hz=915e6;distance_km=1;tx_power_dbm=20;tx_gain_dbi=2;rx_gain_dbi=2;losses_db=2', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'risk-resilience-impact-matrix',
        'title' => 'Risk, Resilience, and Impact Matrix',
        'domain' => 'Risk / resilience',
        'topic' => 'calculator/module',
        'family' => 'risk_matrix',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Build risk, exposure, vulnerability, consequence, and resilience scorecards.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'probability=0.25;consequence=80;exposure=0.7;vulnerability=0.6;adaptive_capacity=0.4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'materials-stress-strain-tool',
        'title' => 'Materials, Stress-Strain, and Failure Screening Tool',
        'domain' => 'Materials / mechanical engineering',
        'topic' => 'calculator/backlog',
        'family' => 'materials',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Estimate stress, strain, elastic response, safety factor, fatigue screening, and material comparison.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'load_n=10000;area_m2=0.01;length_m=2;delta_length_m=0.001;yield_strength_pa=250e6;youngs_modulus_pa=200e9', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'ode-phase-stability-workbench',
        'title' => 'ODE, Phase Plane, and Stability Workbench',
        'domain' => 'Differential equations',
        'topic' => 'calculator/module',
        'family' => 'ode',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Convert continuous dynamics equations into trajectories, equilibria, and stability interpretation.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'model=logistic;x0=10;rate=0.25;carrying_capacity=100;time=30;dt=0.1', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'quantum-particle-physics-calculator',
        'title' => 'Quantum and Particle Physics Calculator',
        'domain' => 'Advanced physics',
        'topic' => 'calculator/module',
        'family' => 'advanced_physics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support quantum mechanics, particle physics, scattering, decay, measurement, and uncertainty examples.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass_mev_c2=0.511;momentum_mev_c=1.0;half_life_s=3600;time_s=7200;lagrangian_terms=kinetic_minus_potential', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'network-cascade-dependency-tool',
        'title' => 'Network Dependency and Cascade Tool',
        'domain' => 'Graph systems',
        'topic' => 'calculator/module',
        'family' => 'network',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Map dependency graphs, cascade risks, centrality, and network resilience.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'edges=A,B;B,C;C,D;A,D;D,E;E,B;shock_node=A;attenuation=0.5', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'biology-ecology-growth-tool',
        'title' => 'Biology, Ecology, and Growth Modeling Tool',
        'domain' => 'Biology / ecology',
        'topic' => 'calculator/module',
        'family' => 'ode',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support biological, ecological, evolutionary, and population-dynamics articles.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'model=logistic;x0=10;rate=0.25;carrying_capacity=100;time=30;dt=0.1', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'economics-policy-systems-suite',
        'title' => 'Economics and Policy Systems Suite',
        'domain' => 'Economics / policy',
        'topic' => 'calculator/module',
        'family' => 'economics_policy',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support economics, welfare, policy coherence, development, beyond-GDP, and tradeoff modeling.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'output=0.8;health=0.78;education=0.74;institutions=0.66;ecology=0.52;inequality=0.35;weights=0.25,0.2,0.18,0.17,0.2', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'signal-fourier-spectral-analysis',
        'title' => 'Signal, Fourier, and Spectral Analysis Tool',
        'domain' => 'Scientific computing',
        'topic' => 'calculator/module',
        'family' => 'profile',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze spectral, Fourier, oscillatory, and signal-processing equations across science and engineering.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'clarity=4;evidence=3;assumptions=4;uncertainty=3;interpretation=4', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'stock-flow-accumulation-simulator',
        'title' => 'Stock-Flow and Accumulation Simulator',
        'domain' => 'Systems modeling',
        'topic' => 'calculator/module',
        'family' => 'stock_flow',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Run stock, flow, depletion, exposure, and accumulation models from site equations.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'initial=100;inflows=12,14,13,15,16,15;outflows=8,9,10,11,10,12;steps=6', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'causal-counterfactual-estimator',
        'title' => 'Causal Effect and Counterfactual Estimator',
        'domain' => 'Causal inference',
        'topic' => 'calculator/module',
        'family' => 'causal',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze potential outcomes, counterfactual logic, treatment/control comparisons, and causal claims.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'treated=12,14,16,18,19;control=10,11,13,13,14', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'climate-environmental-systems-index',
        'title' => 'Climate and Environmental Systems Index',
        'domain' => 'Climate / environment',
        'topic' => 'calculator/module',
        'family' => 'weighted_index',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Support environmental monitoring, climate, planetary boundaries, and global-impact index building.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'health=0.82;education=0.76;institutions=0.68;ecology=0.55;resilience=0.72;weights=0.25,0.2,0.2,0.2,0.15', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'story-narrative-meaning-matrix',
        'title' => 'Story, Narrative, Symbolism, and Meaning Matrix',
        'domain' => 'Storytelling / meaning',
        'topic' => 'calculator/backlog',
        'family' => 'meaning_matrix',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Turn narrative, symbolism, mythic structure, and meaning-centered interpretation into structured analysis.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'narrative_structure=4;symbolic_depth=5;ritual_resonance=3;memory=4;ethical_meaning=4;interpretive_openness=5', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'clinical-research-epidemiology-tool',
        'title' => 'Clinical Research and Epidemiology Calculator',
        'domain' => 'Health / medicine',
        'topic' => 'calculator/backlog',
        'family' => 'clinical_epi',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Compute diagnostic metrics, risk ratios, odds ratios, NNT/NNH, trial summaries, and public-health rates.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'a=40;b=60;c=20;d=80;true_positive=90;false_positive=10;false_negative=15;true_negative=85', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'power-grid-energy-systems-tool',
        'title' => 'Power Systems and Grid Reliability Calculator',
        'domain' => 'Power systems',
        'topic' => 'calculator/backlog',
        'family' => 'physics_mechanics',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Model load, capacity, storage, reliability margins, voltage drop, generation mix, and outage risk.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass=2;velocity=12;height=5;force=10;distance=3;angle_deg=0', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'electrical-circuit-tool',
        'title' => 'Electrical Circuit and Power Calculator',
        'domain' => 'Electrical engineering',
        'topic' => 'calculator/backlog',
        'family' => 'electrical_power',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze DC/AC circuits, Ohm’s law, impedance, filters, RC/RL time constants, and power.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'voltage=12;current=2;resistance=6;capacitance_f=1e-6;frequency_hz=1000;load_mw=120;capacity_mw=160', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'social-behavior-network-tool',
        'title' => 'Social Influence and Behavioral Systems Tool',
        'domain' => 'Social psychology',
        'topic' => 'calculator/backlog',
        'family' => 'network',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze social norms, influence pathways, group dynamics, adoption, and behavior-change leverage points.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'edges=A,B;B,C;C,D;A,D;D,E;E,B;shock_node=A;attenuation=0.5', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ],
    [
        'id' => 'lab-assay-dose-response-tool',
        'title' => 'Lab Assay, Dose-Response, and Calibration Tool',
        'domain' => 'Lab science',
        'topic' => 'calculator/backlog',
        'family' => 'lab_assay',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze calibration curves, dilution, dose response, enzyme kinetics, assay quality, and lab reproducibility.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'standards=0,1,2,3,4,5;signals=0.02,0.9,2.1,3.0,4.2,5.1;unknown_signal=2.6', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'rocket-orbital-astrophysics-tool',
        'title' => 'Rocket, Orbital, and Astrophysics Calculator',
        'domain' => 'Aerospace / astrophysics',
        'topic' => 'calculator/backlog',
        'family' => 'relativity_cosmology',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Handle orbital mechanics, delta-v, escape velocity, Keplerian periods, redshift, and simple astrophysics quantities.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'mass_kg=5.972e24;radius_m=6371000;redshift=0.1;h0_km_s_mpc=70;distance_mpc=100', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'structural-beam-column-tool',
        'title' => 'Structural Beam, Column, and Load Path Calculator',
        'domain' => 'Structural engineering',
        'topic' => 'calculator/backlog',
        'family' => 'structural',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Analyze simplified beams, columns, loads, shear/moment, deflection, and buckling risk.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'span_m=6;load_n_per_m=5000;point_load_n=10000;section_modulus_m3=0.0005;allowable_stress_pa=160e6', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'professional_review_required'
    ],
    [
        'id' => 'csv-equation-feature-miner',
        'title' => 'CSV Equation Feature Miner',
        'domain' => 'Developer tooling',
        'topic' => 'calculator/backlog',
        'family' => 'csv_feature_miner',
        'engine' => 'python/numpy + equation-registry feature engine',
        'description' => 'Read the equation registry CSV and suggest new calculators automatically from equation patterns.',
        'inputs' => [
            ['name' => 'inputs', 'label' => 'Inputs / assumptions', 'type' => 'textarea', 'default' => 'min_priority=P0;include_p1=true;feature_limit=20', 'help' => 'Semicolon key=value format. Replace defaults with article-specific data.'],
            ['name' => 'equation', 'label' => 'Equation or formula context', 'type' => 'textarea', 'default' => '', 'help' => 'Optional LaTeX or equation text from the registry.'],
            ['name' => 'notes', 'label' => 'Interpretive notes', 'type' => 'textarea', 'default' => '', 'help' => 'Optional context, units, assumptions, article title, or scenario notes.']
        ],
        'graph_types' => ['feature_curve', 'bar', 'pdf_report'],
        'audience_modes' => ['guided', 'analyst', 'expert'],
        'safety_level' => 'educational'
    ]
];
