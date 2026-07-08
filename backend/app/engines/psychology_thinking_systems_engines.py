
from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, result, svg_from_figure, bar_graph


def _radar_bar(labels, values, title):
    return bar_graph(labels, values, title, 'score')


def _parse_scores(inputs, defaults):
    kv=parse_kv(inputs.get('scores') or inputs.get('inputs') or '')
    out=[]
    for k,v in defaults.items():
        try: out.append(float(kv.get(k, v)))
        except Exception: out.append(float(v))
    return list(defaults.keys()), out


def _structured_tool(inputs, title, domain, defaults, summary, warnings=None, interpretation=None):
    labels, vals = _parse_scores(inputs, defaults)
    arr=np.array(vals,dtype=float)
    weights=np.ones(len(arr))/max(len(arr),1)
    overall=float(np.dot(np.clip(arr,0,5), weights)/5*100)
    weakest=labels[int(np.argmin(arr))] if len(arr) else None
    strongest=labels[int(np.argmax(arr))] if len(arr) else None
    graphs=[_radar_bar(labels, vals, title+' profile')]
    return result(title, summary, {
        'overall_score_0_100': overall,
        'strongest_dimension': strongest,
        'weakest_dimension': weakest,
        'dimensions': dict(zip(labels, vals)),
        'recommended_next_review': weakest
    }, warnings or ['Structured screening tool only. Interpret results within context and avoid overclaiming.'], graphs,
    ['Parse user-provided dimension scores', 'Normalize to a 0-100 profile', 'Identify strongest and weakest dimensions', 'Generate export-ready graph'], domain, interpretation or [])

# Psychology cluster

def cognitive_psychology_tool(inputs):
    return _structured_tool(inputs, 'Cognitive Psychology Tool', 'python/numpy', {'attention':3,'working_memory':3,'mental_models':3,'cognitive_load':3,'transfer':3}, 'Mapped cognitive dimensions relevant to learning, reasoning, and decision support.', ['Educational cognitive-psychology screening only, not diagnosis.'])

def developmental_psychology_tool(inputs):
    return _structured_tool(inputs, 'Developmental Psychology Tool', 'python/numpy', {'cognitive_development':3,'social_development':3,'language':3,'emotion_regulation':3,'context_support':3}, 'Mapped developmental dimensions across learning, social context, and adaptation.', ['Educational/developmental framework only, not clinical assessment.'])

def personality_psychology_tool(inputs):
    return _structured_tool(inputs, 'Personality Psychology Tool', 'python/numpy', {'openness':3,'conscientiousness':3,'extraversion':3,'agreeableness':3,'emotional_stability':3}, 'Computed a Big-Five-style personality profile for reflective analysis.', ['Self-report educational profile only, not clinical diagnosis or employment screening.'])

def positive_psychology_tool(inputs):
    return _structured_tool(inputs, 'Positive Psychology Tool', 'python/numpy', {'meaning':3,'engagement':3,'relationships':3,'accomplishment':3,'positive_emotion':3,'strengths_use':3}, 'Mapped wellbeing and strengths dimensions for positive psychology analysis.', ['Educational wellbeing tool only, not mental-health treatment advice.'])

def organizational_psychology_tool(inputs):
    return _structured_tool(inputs, 'Organizational Psychology Tool', 'python/numpy', {'role_clarity':3,'psychological_safety':3,'motivation':3,'coordination':3,'feedback':3,'burnout_risk_inverse':3}, 'Mapped organization-level psychological conditions that affect performance and learning.', ['Organizational diagnostic support only; combine with qualitative evidence and employee safeguards.'])

def institutional_psychology_tool(inputs):
    return _structured_tool(inputs, 'Institutional Psychology Tool', 'python/numpy', {'trust':3,'legitimacy':3,'norm_clarity':3,'accountability':3,'learning_capacity':3,'symbolic_coherence':3}, 'Mapped institutional psychology factors: trust, legitimacy, norms, accountability, learning, and symbolic order.', ['Analytical framework only, not a definitive institutional assessment.'])

def analytical_psychology_symbolism_tool(inputs):
    return _structured_tool(inputs, 'Analytical Psychology, Symbolism, and Depth Mind Tool', 'python/numpy + AI-ready', {'symbol_density':3,'archetypal_pattern':3,'shadow_tension':3,'integration_potential':3,'narrative_depth':3}, 'Structured symbolic and depth-psychology interpretation for myths, images, stories, institutions, and recurring motifs.', ['Interpretive humanities tool only; not clinical Jungian analysis.'])

# Behavioral science cluster

def behavioral_science_psychology_hub_tool(inputs):
    return _structured_tool(inputs, 'Behavioral Science and Psychology Hub Tool', 'python/numpy', {'behavior_definition':3,'context_mapping':3,'measurement':3,'intervention_fit':3,'ethics':3,'evaluation':3}, 'Mapped a behavioral problem from definition through intervention and evaluation.', ['Behavioral intervention planning requires consent, ethics, and local context.'])

def behavioral_economics_tool(inputs):
    return _structured_tool(inputs, 'Behavioral Economics Tool', 'python/numpy', {'loss_aversion':3,'present_bias':3,'status_quo_bias':3,'framing_effect':3,'social_proof':3,'choice_friction':3}, 'Profiled behavioral economics forces shaping decisions under bounded rationality.', ['Analytical support only; avoid manipulative or coercive uses.'])

def behavior_change_habit_tool(inputs):
    return _structured_tool(inputs, 'Behavior Change and Habit Formation Tool', 'python/numpy', {'cue_clarity':3,'routine_feasibility':3,'reward_strength':3,'friction_reduction':3,'identity_alignment':3,'feedback_loop':3}, 'Mapped habit formation conditions across cue, routine, reward, friction, identity, and feedback.', ['Educational behavior-change tool only; avoid medical or mental-health treatment claims.'])

def motivation_reinforcement_learning_tool(inputs):
    return _structured_tool(inputs, 'Motivation, Reinforcement, and Learning Tool', 'python/numpy', {'intrinsic_motivation':3,'extrinsic_support':3,'reinforcement_schedule':3,'competence_feedback':3,'autonomy':3,'mastery_progress':3}, 'Mapped motivation and reinforcement conditions for learning or behavior design.', ['Educational framework only; not clinical or coercive behavior control.'])

def choice_architecture_nudging_tool(inputs):
    return _structured_tool(inputs, 'Choice Architecture and Nudging Tool', 'python/numpy', {'default_design':3,'salience':3,'friction':3,'transparency':3,'user_agency':3,'equity':3}, 'Evaluated choice architecture using effectiveness, agency, transparency, and equity dimensions.', ['Use only for transparent, welfare-enhancing interventions; avoid dark patterns.'])

def social_norms_influence_tool(inputs):
    return _structured_tool(inputs, 'Social Norms and Behavioral Influence Tool', 'python/numpy', {'descriptive_norms':3,'injunctive_norms':3,'reference_group_fit':3,'visibility':3,'trust':3,'backfire_risk_inverse':3}, 'Mapped social norms, reference groups, visibility, trust, and backfire risk.', ['Norm interventions require cultural context and ethical review.'])

def behavioral_public_policy_tool(inputs):
    return _structured_tool(inputs, 'Behavioral Public Policy Tool', 'python/numpy', {'problem_definition':3,'evidence_base':3,'distributional_equity':3,'consent_transparency':3,'administrative_feasibility':3,'evaluation_plan':3}, 'Mapped behavioral public-policy design across evidence, equity, transparency, feasibility, and evaluation.', ['Policy analysis support only, not legal or regulatory advice.'])

def behavioral_research_methods_tool(inputs):
    return _structured_tool(inputs, 'Behavioral Research Methods Tool', 'python/numpy', {'construct_validity':3,'sampling':3,'measurement_reliability':3,'experimental_design':3,'confounding_control':3,'replicability':3}, 'Evaluated behavioral research design quality and threats to inference.', ['Research-methods support only; IRB/ethics review may be required.'])

def ethics_behavioral_intervention_tool(inputs):
    return _structured_tool(inputs, 'Ethics of Behavioral Intervention Tool', 'python/numpy', {'autonomy':3,'beneficence':3,'nonmaleficence':3,'justice':3,'transparency':3,'contestability':3}, 'Mapped ethical safeguards for behavioral intervention design.', ['Ethics support only; does not replace formal review.'])

def moral_psychology_tool(inputs):
    return _structured_tool(inputs, 'Moral Psychology Tool', 'python/numpy', {'harm_care':3,'fairness':3,'loyalty':3,'authority':3,'sanctity':3,'liberty':3,'empathy':3}, 'Mapped moral-psychology dimensions relevant to judgment, conflict, persuasion, and institutions.', ['Interpretive educational tool only; avoid stereotyping or deterministic claims.'])

# Thinking and problem solving cluster

def knowledge_architecture_tool(inputs):
    return _structured_tool(inputs, 'Knowledge Architecture Tool', 'python/numpy', {'taxonomy':3,'navigation':3,'metadata':3,'source_traceability':3,'learning_pathways':3,'governance':3}, 'Evaluated knowledge-system structure, discoverability, traceability, and governance.', ['Information-architecture support only. Validate with real users and content audits.'])

def design_thinking_tool(inputs):
    return _structured_tool(inputs, 'Design Thinking Tool', 'python/numpy', {'empathy':3,'problem_framing':3,'ideation':3,'prototyping':3,'testing':3,'iteration':3}, 'Mapped a design-thinking workflow from human context through iteration.', ['Design support only; avoid replacing stakeholder research.'])

def mathematical_thinking_tool(inputs):
    return _structured_tool(inputs, 'Mathematical Thinking Tool', 'python/numpy', {'abstraction':3,'formalization':3,'proof_logic':3,'model_fit':3,'edge_cases':3,'interpretation':3}, 'Evaluated mathematical reasoning across abstraction, formalization, proof, model fit, edge cases, and interpretation.', ['Educational reasoning support only.'])

def systems_thinking_tool(inputs):
    return _structured_tool(inputs, 'Systems Thinking Tool', 'python/numpy', {'boundaries':3,'stocks_flows':3,'feedback_loops':3,'delays':3,'leverage_points':3,'emergence':3,'unintended_consequences':3}, 'Mapped systems-thinking dimensions: boundaries, stocks, flows, feedback, delays, leverage, emergence, and unintended consequences.', ['Systems maps are simplifications; validate with stakeholders and data.'])

def algorithms_computational_reasoning_tool(inputs):
    return _structured_tool(inputs, 'Algorithms and Computational Reasoning Tool', 'python/numpy', {'problem_formalization':3,'data_structures':3,'complexity':3,'correctness':3,'testing':3,'accountability':3}, 'Evaluated computational reasoning across formalization, structures, complexity, correctness, testing, and accountability.', ['Educational computational-reasoning support only.'])

def resilience_thinking_tool(inputs):
    return _structured_tool(inputs, 'Resilience Thinking Tool', 'python/numpy', {'exposure':3,'sensitivity_inverse':3,'adaptive_capacity':3,'redundancy':3,'learning':3,'recovery':3,'transformability':3}, 'Mapped resilience across exposure, sensitivity, capacity, redundancy, learning, recovery, and transformability.', ['Resilience analysis requires local evidence and stakeholder review.'])

def futures_thinking_tool(inputs):
    return _structured_tool(inputs, 'Futures Thinking Tool', 'python/numpy', {'drivers':3,'uncertainties':3,'scenarios':3,'early_signals':3,'robust_options':3,'adaptation_pathways':3}, 'Mapped futures-thinking quality across drivers, uncertainties, scenarios, signals, options, and pathways.', ['Scenario planning support only, not prediction.'])

def strategic_ideation_tool(inputs):
    return _structured_tool(inputs, 'Strategic Ideation Tool', 'python/numpy', {'problem_clarity':3,'option_diversity':3,'constraint_awareness':3,'differentiation':3,'feasibility':3,'learning_value':3}, 'Evaluated strategic ideas across clarity, diversity, constraints, differentiation, feasibility, and learning value.', ['Strategic support only; validate with evidence and execution constraints.'])

# Meaning cluster

def beauty_aesthetics_meaning_tool(inputs):
    return _structured_tool(inputs, 'Beauty, Aesthetics, and Meaning Tool', 'python/numpy + AI-ready', {'form':3,'pattern':3,'harmony':3,'symbolic_depth':3,'emotional_resonance':3,'transcendence':3}, 'Mapped aesthetic and meaning dimensions across form, pattern, symbol, resonance, and transcendence.', ['Interpretive tool only; not a definitive theory of beauty.'])

def aesthetics_philosophy_art_tool(inputs):
    return _structured_tool(inputs, 'Aesthetics and Philosophy of Art Tool', 'python/numpy + AI-ready', {'representation':3,'expression':3,'formalist_structure':3,'interpretive_openness':3,'historical_context':3,'judgment':3}, 'Mapped a work or aesthetic claim through major philosophy-of-art dimensions.', ['Interpretive humanities support only.'])

def mathematics_art_music_pattern_tool(inputs):
    return _structured_tool(inputs, 'Mathematics, Art, Music, and Pattern Tool', 'python/numpy', {'symmetry':3,'ratio':3,'recursion':3,'rhythm':3,'variation':3,'emergent_pattern':3}, 'Mapped mathematical pattern relationships across visual, musical, and symbolic form.', ['Exploratory pattern-analysis support only.'])

def symbolism_style_cultural_meaning_tool(inputs):
    return _structured_tool(inputs, 'Symbolism, Style, and Cultural Meaning Tool', 'python/numpy + AI-ready', {'symbol_density':3,'style_coherence':3,'cultural_context':3,'ritual_association':3,'memory':3,'ambiguity':3}, 'Mapped symbolic, stylistic, and cultural meaning dimensions.', ['Interpretive support only; cultural analysis requires care and context.'])

def creative_form_composition_interpretation_tool(inputs):
    return _structured_tool(inputs, 'Creative Form, Composition, and Interpretation Tool', 'python/numpy + AI-ready', {'structure':3,'tension':3,'contrast':3,'unity':3,'movement':3,'interpretive_depth':3}, 'Evaluated creative form through composition, contrast, unity, movement, and interpretive depth.', ['Creative interpretation support only.'])

def story_myth_meaning_tool(inputs):
    return _structured_tool(inputs, 'Story, Myth, and Meaning Tool', 'python/numpy + AI-ready', {'mythic_structure':3,'ritual_depth':3,'archetypal_motif':3,'memory':3,'suffering_hope':3,'sacred_order':3}, 'Mapped story and myth as elemental meaning-making structures.', ['Interpretive humanities tool only.'])

# Systems modeling and limits to growth

def systems_modeling_tool(inputs):
    return _structured_tool(inputs, 'Systems Modeling Tool', 'python/numpy', {'boundary_definition':3,'variable_quality':3,'causal_structure':3,'feedback_representation':3,'data_calibration':3,'validation':3,'scenario_design':3}, 'Evaluated systems-modeling readiness across boundaries, variables, causal structure, feedback, calibration, validation, and scenarios.', ['Modeling support only; outputs depend on assumptions and validation.'])

def predictive_modeling_tool(inputs):
    return _structured_tool(inputs, 'Predictive Modeling Tool', 'python/numpy', {'target_definition':3,'feature_quality':3,'training_data':3,'validation_design':3,'calibration':3,'uncertainty':3,'deployment_monitoring':3}, 'Mapped predictive-modeling readiness from target definition through monitoring.', ['Predictive models require validation, bias review, monitoring, and domain oversight.'])

def limits_to_growth_system_dynamics_tool(inputs):
    kv=parse_kv(inputs.get('inputs') or 'population=1.0;capital=1.0;resources=1.0;pollution=0.05;birth_rate=0.025;death_rate=0.01;investment_rate=0.04;depletion_rate=0.015;pollution_rate=0.02;years=80')
    years=int(float(kv.get('years',80)))
    P=float(kv.get('population',1.0)); K=float(kv.get('capital',1.0)); R=float(kv.get('resources',1.0)); X=float(kv.get('pollution',0.05))
    br=float(kv.get('birth_rate',0.025)); dr=float(kv.get('death_rate',0.01)); inv=float(kv.get('investment_rate',0.04)); dep=float(kv.get('depletion_rate',0.015)); pol=float(kv.get('pollution_rate',0.02))
    ps=[]; ks=[]; rs=[]; xs=[]
    for _ in range(max(years,1)):
        resource_stress=max(0,1-R)
        pollution_stress=X
        death=dr*(1+1.5*resource_stress+pollution_stress)
        P=max(0, P + P*(br-death))
        K=max(0, K + inv*K*R - 0.025*K - 0.01*X*K)
        R=max(0, R - dep*K*P)
        X=max(0, X + pol*K*P - 0.015*X)
        ps.append(P); ks.append(K); rs.append(R); xs.append(X)
    fig, ax=plt.subplots(figsize=(8.8,5.0))
    t=np.arange(len(ps)); ax.plot(t, ps, label='population'); ax.plot(t, ks, label='capital'); ax.plot(t, rs, label='resources'); ax.plot(t, xs, label='pollution')
    ax.set_title('Limits to Growth style system dynamics proxy'); ax.set_xlabel('year'); ax.set_ylabel('relative index'); ax.legend(); ax.grid(alpha=.28)
    svg=svg_from_figure(fig); plt.close(fig)
    collapse_year=None
    for i,(p,r,x) in enumerate(zip(ps,rs,xs)):
        if p < 0.7*ps[0] or r < 0.2 or x > 2.5:
            collapse_year=i; break
    warnings=['Simplified educational system-dynamics proxy inspired by limits-to-growth reasoning. Not a calibrated World3 model or forecast.']
    return result('Limits to Growth System Dynamics Tool', 'Simulated a simplified stocks-flows-feedback scenario linking population, capital, resources, and pollution.', {'final_population_index':ps[-1], 'final_capital_index':ks[-1], 'final_resource_index':rs[-1], 'final_pollution_index':xs[-1], 'stress_threshold_year_proxy':collapse_year}, warnings, [{'title':'Limits to Growth proxy trajectory','type':'system_dynamics_svg','svg':svg,'export_formats':['svg','png','pdf_report']}], ['Initialize stock variables', 'Iterate yearly feedback equations', 'Track resource depletion and pollution stress', 'Graph multi-stock trajectories'], 'python/numpy', ['Use to teach feedback, overshoot, delay, depletion, pollution, and scenario sensitivity.'])
