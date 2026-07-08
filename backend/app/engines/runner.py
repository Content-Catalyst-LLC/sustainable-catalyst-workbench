from __future__ import annotations
from .math_engine import linear_system_solver, calculus_function_analyzer, statistics_analyzer, regression_analyzer, probability_distribution_calculator, differential_equation_simulator
from .domain_engines import decision_analysis_tool, economics_calculator, energy_systems_calculator, psychology_scale_analyzer, scientific_calculator, engineering_calculator, architecture_building_calculator, sustainability_resilience_scorecard, ai_governance_audit, haskell_rule_checker, qualitative_interpretation_matrix
from .pattern_engines import music_frequency_calculator, chord_scale_identifier, color_contrast_calculator, color_harmony_generator, vector_geometry_calculator, embedding_similarity_tool, pca_dimensionality_explorer, fourier_frequency_analysis, ai_classification_metrics, multimodal_pattern_comparison
from .public_systems_engines import environmental_monitoring_qaqc, global_impact_assessment, climate_change_scenario_tool, earth_science_hazard_analyzer, marine_biology_ocean_health_tool, astronomy_calculator, materials_science_calculator, health_medical_public_health_tool, international_law_issue_mapper, legal_traditions_comparator, metaphysics_framework_tool

RUNNERS = {
    'linear-system-solver': linear_system_solver,
    'calculus-function-analyzer': calculus_function_analyzer,
    'statistics-analyzer': statistics_analyzer,
    'regression-analyzer': regression_analyzer,
    'probability-distribution-calculator': probability_distribution_calculator,
    'differential-equation-simulator': differential_equation_simulator,
    'decision-analysis-tool': decision_analysis_tool,
    'economics-calculator': economics_calculator,
    'energy-systems-calculator': energy_systems_calculator,
    'psychology-scale-analyzer': psychology_scale_analyzer,
    'scientific-calculator': scientific_calculator,
    'engineering-calculator': engineering_calculator,
    'architecture-building-calculator': architecture_building_calculator,
    'sustainability-resilience-scorecard': sustainability_resilience_scorecard,
    'ai-governance-audit': ai_governance_audit,
    'haskell-rule-checker': haskell_rule_checker,
    'qualitative-interpretation-matrix': qualitative_interpretation_matrix,
    'music-frequency-calculator': music_frequency_calculator,
    'chord-scale-identifier': chord_scale_identifier,
    'color-contrast-calculator': color_contrast_calculator,
    'color-harmony-generator': color_harmony_generator,
    'vector-geometry-calculator': vector_geometry_calculator,
    'embedding-similarity-tool': embedding_similarity_tool,
    'pca-dimensionality-explorer': pca_dimensionality_explorer,
    'fourier-frequency-analysis-tool': fourier_frequency_analysis,
    'ai-classification-metrics-calculator': ai_classification_metrics,
    'multimodal-pattern-comparison-tool': multimodal_pattern_comparison,
    'environmental-monitoring-qaqc-tool': environmental_monitoring_qaqc,
    'global-impact-assessment-matrix': global_impact_assessment,
    'climate-change-scenario-tool': climate_change_scenario_tool,
    'earth-science-hazard-analyzer': earth_science_hazard_analyzer,
    'marine-biology-ocean-health-tool': marine_biology_ocean_health_tool,
    'astronomy-calculator': astronomy_calculator,
    'materials-science-calculator': materials_science_calculator,
    'health-medical-public-health-tool': health_medical_public_health_tool,
    'international-law-issue-mapper': international_law_issue_mapper,
    'legal-traditions-comparator': legal_traditions_comparator,
    'metaphysics-framework-tool': metaphysics_framework_tool,
}

def run_tool(tool_id: str, inputs: dict, mode: str = 'guided'):
    if tool_id not in RUNNERS:
        raise KeyError(f'Unknown tool: {tool_id}')
    payload = dict(inputs or {})
    payload['_audience_mode'] = mode
    return RUNNERS[tool_id](payload)
