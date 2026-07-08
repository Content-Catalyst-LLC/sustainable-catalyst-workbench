from __future__ import annotations
from .math_engine import linear_system_solver, calculus_function_analyzer, statistics_analyzer, regression_analyzer, probability_distribution_calculator, differential_equation_simulator
from .domain_engines import decision_analysis_tool, economics_calculator, energy_systems_calculator, psychology_scale_analyzer, scientific_calculator, engineering_calculator, architecture_building_calculator, sustainability_resilience_scorecard, ai_governance_audit, haskell_rule_checker, qualitative_interpretation_matrix
from .pattern_engines import music_frequency_calculator, chord_scale_identifier, color_contrast_calculator, color_harmony_generator, vector_geometry_calculator, embedding_similarity_tool, pca_dimensionality_explorer, fourier_frequency_analysis, ai_classification_metrics, multimodal_pattern_comparison
from .advanced_systems_engines import nuclear_physics_calculator, particle_physics_calculator, neurophysics_calculator, rocket_science_calculator, electronics_engineering_calculator, rf_antenna_calculator, full_stack_engineering_tool, lab_science_calculator, clinical_research_calculator
from .public_systems_engines import environmental_monitoring_qaqc, global_impact_assessment, climate_change_scenario_tool, earth_science_hazard_analyzer, marine_biology_ocean_health_tool, astronomy_calculator, materials_science_calculator, health_medical_public_health_tool, international_law_issue_mapper, legal_traditions_comparator, metaphysics_framework_tool
from .interdisciplinary_engines import physics_calculator, chemistry_calculator, biology_calculator, environmental_science_calculator, earth_science_calculator, content_frameworks_analyzer, storytelling_structure_analyzer, social_psychology_analyzer, grit_resilience_analyzer
from .predictive_economics_engines import predictive_analytics_forecasting_tool, time_series_diagnostics_tool, economics_forecasting_scenario_tool, econometrics_policy_model_tool
from .professional_systems_engines import fpga_digital_systems_tool, power_systems_engineering_tool, mechanical_systems_engineering_tool, structural_engineering_tool, civil_infrastructure_planning_tool, urban_planning_analytics_tool, architecture_building_science_tool, astrophysics_research_calculator
from .feature_built_engines import FEATURE_TOOL_IDS, feature_built_tool
from .psychology_thinking_systems_engines import cognitive_psychology_tool, developmental_psychology_tool, personality_psychology_tool, positive_psychology_tool, organizational_psychology_tool, institutional_psychology_tool, analytical_psychology_symbolism_tool, behavioral_science_psychology_hub_tool, behavioral_economics_tool, behavior_change_habit_tool, motivation_reinforcement_learning_tool, choice_architecture_nudging_tool, social_norms_influence_tool, behavioral_public_policy_tool, behavioral_research_methods_tool, ethics_behavioral_intervention_tool, moral_psychology_tool, knowledge_architecture_tool, design_thinking_tool, mathematical_thinking_tool, systems_thinking_tool, algorithms_computational_reasoning_tool, resilience_thinking_tool, futures_thinking_tool, strategic_ideation_tool, beauty_aesthetics_meaning_tool, aesthetics_philosophy_art_tool, mathematics_art_music_pattern_tool, symbolism_style_cultural_meaning_tool, creative_form_composition_interpretation_tool, story_myth_meaning_tool, systems_modeling_tool, predictive_modeling_tool, limits_to_growth_system_dynamics_tool

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
    'physics-calculator': physics_calculator,
    'chemistry-calculator': chemistry_calculator,
    'biology-calculator': biology_calculator,
    'environmental-science-calculator': environmental_science_calculator,
    'earth-science-calculator': earth_science_calculator,
    'content-frameworks-analyzer': content_frameworks_analyzer,
    'storytelling-structure-analyzer': storytelling_structure_analyzer,
    'social-psychology-analyzer': social_psychology_analyzer,
    'grit-resilience-analyzer': grit_resilience_analyzer,
    'nuclear-physics-calculator': nuclear_physics_calculator,
    'particle-physics-calculator': particle_physics_calculator,
    'neurophysics-calculator': neurophysics_calculator,
    'rocket-science-calculator': rocket_science_calculator,
    'electronics-engineering-calculator': electronics_engineering_calculator,
    'rf-antenna-calculator': rf_antenna_calculator,
    'full-stack-engineering-tool': full_stack_engineering_tool,
    'lab-science-calculator': lab_science_calculator,
    'clinical-research-calculator': clinical_research_calculator,

    'predictive-analytics-forecasting-tool': predictive_analytics_forecasting_tool,
    'time-series-diagnostics-tool': time_series_diagnostics_tool,
    'economics-forecasting-scenario-tool': economics_forecasting_scenario_tool,
    'econometrics-policy-model-tool': econometrics_policy_model_tool,
    'fpga-digital-systems-tool': fpga_digital_systems_tool,
    'power-systems-engineering-tool': power_systems_engineering_tool,
    'mechanical-systems-engineering-tool': mechanical_systems_engineering_tool,
    'structural-engineering-tool': structural_engineering_tool,
    'civil-infrastructure-planning-tool': civil_infrastructure_planning_tool,
    'urban-planning-analytics-tool': urban_planning_analytics_tool,
    'architecture-building-science-tool': architecture_building_science_tool,
    'astrophysics-research-calculator': astrophysics_research_calculator,

    'cognitive-psychology-tool': cognitive_psychology_tool,
    'developmental-psychology-tool': developmental_psychology_tool,
    'personality-psychology-tool': personality_psychology_tool,
    'positive-psychology-tool': positive_psychology_tool,
    'organizational-psychology-tool': organizational_psychology_tool,
    'institutional-psychology-tool': institutional_psychology_tool,
    'analytical-psychology-symbolism-tool': analytical_psychology_symbolism_tool,
    'behavioral-science-psychology-hub-tool': behavioral_science_psychology_hub_tool,
    'behavioral-economics-tool': behavioral_economics_tool,
    'behavior-change-habit-tool': behavior_change_habit_tool,
    'motivation-reinforcement-learning-tool': motivation_reinforcement_learning_tool,
    'choice-architecture-nudging-tool': choice_architecture_nudging_tool,
    'social-norms-influence-tool': social_norms_influence_tool,
    'behavioral-public-policy-tool': behavioral_public_policy_tool,
    'behavioral-research-methods-tool': behavioral_research_methods_tool,
    'ethics-behavioral-intervention-tool': ethics_behavioral_intervention_tool,
    'moral-psychology-tool': moral_psychology_tool,
    'knowledge-architecture-tool': knowledge_architecture_tool,
    'design-thinking-tool': design_thinking_tool,
    'mathematical-thinking-tool': mathematical_thinking_tool,
    'systems-thinking-tool': systems_thinking_tool,
    'algorithms-computational-reasoning-tool': algorithms_computational_reasoning_tool,
    'resilience-thinking-tool': resilience_thinking_tool,
    'futures-thinking-tool': futures_thinking_tool,
    'strategic-ideation-tool': strategic_ideation_tool,
    'beauty-aesthetics-meaning-tool': beauty_aesthetics_meaning_tool,
    'aesthetics-philosophy-art-tool': aesthetics_philosophy_art_tool,
    'mathematics-art-music-pattern-tool': mathematics_art_music_pattern_tool,
    'symbolism-style-cultural-meaning-tool': symbolism_style_cultural_meaning_tool,
    'creative-form-composition-interpretation-tool': creative_form_composition_interpretation_tool,
    'story-myth-meaning-tool': story_myth_meaning_tool,
    'systems-modeling-tool': systems_modeling_tool,
    'predictive-modeling-tool': predictive_modeling_tool,
    'limits-to-growth-system-dynamics-tool': limits_to_growth_system_dynamics_tool,
}

RUNNERS.update({fid: (lambda payload, fid=fid: feature_built_tool(fid, payload)) for fid in FEATURE_TOOL_IDS})

def run_tool(tool_id: str, inputs: dict, mode: str = 'guided'):
    if tool_id not in RUNNERS:
        raise KeyError(f'Unknown tool: {tool_id}')
    payload = dict(inputs or {})
    payload['_audience_mode'] = mode
    return RUNNERS[tool_id](payload)
