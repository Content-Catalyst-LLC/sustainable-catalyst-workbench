<?php
if (!defined('ABSPATH')) { exit; }
return [
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
                'default' => 'Option A,8,6,7
Option B,6,9,8',
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
                'default' => '4,5,4,3
3,4,4,2
5,5,4,4',
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
                'default' => 'IF high_impact THEN human_review
IF human_review THEN audit_log',
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
                'default' => '1,2,3
2,3,4
3,4,6
4,5,8
5,7,10',
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
    ]
];
