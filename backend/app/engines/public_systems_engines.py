from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, parse_number_list, parse_rows, result, svg_from_figure, bar_graph


def _safe_series(text, default):
    vals = parse_number_list(text or default)
    return np.array(vals, dtype=float)


def _linear_trend(values):
    y = np.array(values, dtype=float)
    x = np.arange(len(y), dtype=float)
    if len(y) < 2:
        return 0.0, float(y[0]) if len(y) else 0.0, np.zeros_like(y)
    m, b = np.polyfit(x, y, 1)
    return float(m), float(b), m*x + b


def environmental_monitoring_qaqc(inputs):
    """Sensor QA/QC and threshold analytics for environmental monitoring."""
    values = _safe_series(inputs.get('values'), '12,12.4,12.2,19.8,12.1,12.0,11.9,15.5,12.3')
    lower = float(inputs.get('lower_threshold', np.nanmin(values) - 1))
    upper = float(inputs.get('upper_threshold', np.nanmax(values) + 1))
    z_limit = float(inputs.get('z_limit', 3.0))
    labels = [f't{i+1}' for i in range(len(values))]
    mean = float(np.mean(values)); sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    z = (values - mean) / (sd if sd else 1.0)
    threshold_flags = [int(v < lower or v > upper) for v in values]
    z_flags = [int(abs(zz) > z_limit) for zz in z]
    missing_rate = float(np.mean(np.isnan(values))) if len(values) else 0.0
    slope, intercept, trend = _linear_trend(values)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(values, marker='o', label='observed')
    ax.plot(trend, linestyle='--', label='linear trend')
    ax.axhline(lower, linewidth=1, linestyle=':', label='lower threshold')
    ax.axhline(upper, linewidth=1, linestyle=':', label='upper threshold')
    ax.set_title('Environmental monitoring QA/QC time series')
    ax.set_xlabel('Observation'); ax.set_ylabel('Value'); ax.grid(alpha=.25); ax.legend()
    graph = {'title':'Monitoring QA/QC series','type':'time_series','svg':svg_from_figure(fig)}; plt.close(fig)
    warnings = []
    if sum(threshold_flags): warnings.append('One or more readings exceed configured thresholds.')
    if sum(z_flags): warnings.append('One or more readings are statistical outliers under the selected z-score rule.')
    return result('Environmental Monitoring QA/QC Tool', 'Analyzed sensor readings for thresholds, outliers, basic trend, and monitoring quality flags.', {
        'count': int(len(values)), 'mean': mean, 'standard_deviation': sd, 'trend_slope_per_step': slope,
        'threshold_exceedances': int(sum(threshold_flags)), 'zscore_outliers': int(sum(z_flags)), 'missing_rate': missing_rate,
        'lower_threshold': lower, 'upper_threshold': upper
    }, warnings, [graph], ['Parse sensor series', 'Compute trend and dispersion', 'Flag threshold exceedances and z-score outliers', 'Render monitoring graph'], 'python/numpy')


def global_impact_assessment(inputs):
    """Serious multidomain impact scoring across environmental, health, legal, equity, and governance dimensions."""
    kv = parse_kv(inputs.get('scores') or 'climate=4;biodiversity=4;water=3;public_health=4;human_rights=3;economic_disruption=3;governance=4;reversibility=2;uncertainty=4;equity=4')
    weights = parse_kv(inputs.get('weights') or '')
    labels = [k for k,v in kv.items() if isinstance(v,(int,float))]
    vals = np.array([float(kv[k]) for k in labels], dtype=float)
    w = np.array([float(weights.get(k, 1.0)) for k in labels], dtype=float)
    w = w / (w.sum() or 1.0)
    weighted = vals * w
    total = float(weighted.sum())
    graph = bar_graph(labels, vals.tolist(), 'Global impact dimension scores', 'Score')
    rank = sorted(zip(labels, vals.tolist(), w.tolist(), weighted.tolist()), key=lambda x: -x[3])
    warnings = []
    if total >= 3.5: warnings.append('High global-impact profile. Consider full interdisciplinary review, stakeholder analysis, legal/rights screening, and uncertainty assessment.')
    if 'uncertainty' in kv and float(kv['uncertainty']) >= 4: warnings.append('High uncertainty: avoid false precision; use scenario analysis and sensitivity checks.')
    return result('Global Impact Assessment Matrix', 'Computed a weighted global-impact profile across environment, health, rights, economics, governance, equity, reversibility, and uncertainty.', {
        'weighted_score': total, 'ranking': [{'dimension':a,'score':b,'weight':c,'weighted_contribution':d} for a,b,c,d in rank]
    }, warnings, [graph], ['Score impact dimensions', 'Apply weights', 'Rank weighted contributors', 'Flag high-impact/high-uncertainty profiles'], 'python')


def climate_change_scenario_tool(inputs):
    mode = inputs.get('mode') or 'warming_pathway'
    kv = parse_kv(inputs.get('inputs') or 'baseline_temp=1.2;annual_change=0.025;years=80;emissions_start=40;annual_reduction=0.02')
    years = int(kv.get('years', 80)); t = np.arange(years + 1)
    if mode == 'carbon_budget':
        annual = float(kv.get('annual_emissions_gtco2', 40)); reduction = float(kv.get('annual_reduction_rate', 0.03)); emissions = annual * (1 - reduction) ** t; cumulative = np.cumsum(emissions); budget=float(kv.get('budget_gtco2', 500)); exceed_idx = np.argmax(cumulative >= budget) if np.any(cumulative >= budget) else None
        values = {'cumulative_emissions_gtco2': float(cumulative[-1]), 'budget_gtco2': budget, 'budget_exceeded_year_index': None if exceed_idx is None else int(exceed_idx)}
        y = cumulative; ylabel='Cumulative GtCO₂'; title='Carbon budget scenario'
    elif mode == 'sea_level_proxy':
        rate=float(kv.get('mm_per_year', 4.0)); acceleration=float(kv.get('acceleration_mm_per_year2', 0.04)); y=rate*t + 0.5*acceleration*t**2; values={'sea_level_change_mm_end':float(y[-1]), 'rate_mm_year':rate, 'acceleration_mm_year2':acceleration}; ylabel='mm'; title='Sea-level proxy scenario'
    else:
        baseline=float(kv.get('baseline_temp',1.2)); annual=float(kv.get('annual_change',0.025)); y=baseline + annual*t; values={'warming_end_c':float(y[-1]), 'baseline_c':baseline, 'annual_change_c':annual}; ylabel='°C above baseline reference'; title='Warming pathway scenario'
    fig, ax = plt.subplots(figsize=(7.5,4.5)); ax.plot(t,y); ax.set_title(title); ax.set_xlabel('Years from start'); ax.set_ylabel(ylabel); ax.grid(alpha=.25); graph={'title':title,'type':'scenario','svg':svg_from_figure(fig)}; plt.close(fig)
    return result('Climate Change Scenario Tool', f'Ran climate scenario mode: {mode}.', values, ['Scenario proxy only; not a climate model. Use for education, sensitivity, and framing.'], [graph], ['Select scenario mode', 'Compute trajectory', 'Render scenario curve', 'Interpret uncertainty and limitations'], 'python + optional Julia')


def earth_science_hazard_analyzer(inputs):
    kv = parse_kv(inputs.get('inputs') or 'probability=0.15;exposure=4;vulnerability=3;capacity=2;warning_time=1')
    p=float(kv.get('probability',0.1)); exposure=float(kv.get('exposure',3)); vulnerability=float(kv.get('vulnerability',3)); capacity=float(kv.get('capacity',2)); warning=float(kv.get('warning_time',1))
    risk = p * exposure * vulnerability * (1 + max(0, 3-capacity)/3) * (1 + max(0, 2-warning)/4)
    labels=['probability','exposure','vulnerability','capacity','warning_time']; vals=[p,exposure,vulnerability,capacity,warning]
    graph=bar_graph(labels, vals, 'Earth-science hazard factors')
    warnings=[]
    if risk > 2: warnings.append('Elevated hazard-risk profile. Add local geospatial exposure data, historical frequency, and mitigation capacity.')
    return result('Earth Science Hazard Analyzer', 'Computed a simple multi-factor hazard risk proxy using probability, exposure, vulnerability, capacity, and warning time.', {'hazard_risk_proxy':float(risk),'inputs':dict(zip(labels,vals))}, warnings, [graph], ['Parse hazard factors', 'Combine probability, exposure, vulnerability, capacity, and warning-time proxy', 'Render factor profile'], 'python')


def marine_biology_ocean_health_tool(inputs):
    kv = parse_kv(inputs.get('inputs') or 'temperature_anomaly=1.4;ph=8.0;dissolved_oxygen=5.5;nutrients=3.0;plastic_index=2.0;biodiversity=3.5')
    temp=float(kv.get('temperature_anomaly',1.0)); ph=float(kv.get('ph',8.1)); oxygen=float(kv.get('dissolved_oxygen',6.0)); nutrients=float(kv.get('nutrients',2.0)); plastic=float(kv.get('plastic_index',1.0)); biodiversity=float(kv.get('biodiversity',4.0))
    acid_stress=max(0, 8.1-ph)*2.5; oxygen_stress=max(0, 6-oxygen)*0.8; temp_stress=temp; nutrient_stress=nutrients/3; plastic_stress=plastic/3; biodiversity_buffer=biodiversity/5
    stress=temp_stress+acid_stress+oxygen_stress+nutrient_stress+plastic_stress-biodiversity_buffer
    labels=['temperature','acidification','oxygen','nutrients','plastic','biodiversity buffer']; vals=[temp_stress,acid_stress,oxygen_stress,nutrient_stress,plastic_stress,-biodiversity_buffer]
    graph=bar_graph(labels, vals, 'Ocean health stress components')
    return result('Marine Biology and Ocean Health Tool', 'Estimated a transparent ocean-health stress proxy from temperature anomaly, pH, oxygen, nutrients, plastic pressure, and biodiversity buffer.', {'ocean_health_stress_proxy':float(stress),'components':dict(zip(labels,vals))}, ['Educational proxy; calibrate with local marine observations before use.'], [graph], ['Convert indicators into stress components', 'Subtract biodiversity buffer', 'Render stress profile'], 'python')


def astronomy_calculator(inputs):
    mode = inputs.get('mode') or 'orbital_period'
    kv = parse_kv(inputs.get('inputs') or 'central_mass=1.989e30;semi_major_axis=1.496e11;distance_pc=10;apparent_magnitude=5')
    G=6.67430e-11
    graphs=[]
    if mode == 'escape_velocity':
        M=float(kv.get('mass',5.972e24)); r=float(kv.get('radius',6.371e6)); values={'escape_velocity_m_s':float(math.sqrt(2*G*M/r))}
    elif mode == 'luminosity_distance':
        m=float(kv.get('apparent_magnitude',5)); d=float(kv.get('distance_pc',10)); M=m - 5*math.log10(d/10); values={'absolute_magnitude':float(M)}
    elif mode == 'habitable_zone_proxy':
        L=float(kv.get('stellar_luminosity_solar',1)); values={'inner_au':float(math.sqrt(L/1.1)), 'outer_au':float(math.sqrt(L/0.53))}; graphs.append(bar_graph(['inner AU','outer AU'], [values['inner_au'],values['outer_au']], 'Habitable zone proxy'))
    else:
        M=float(kv.get('central_mass',1.989e30)); a=float(kv.get('semi_major_axis',1.496e11)); T=2*math.pi*math.sqrt(a**3/(G*M)); values={'orbital_period_seconds':float(T),'orbital_period_days':float(T/86400),'orbital_period_years':float(T/(86400*365.25))}
    return result('Astronomy Calculator', f'Ran astronomy mode: {mode}.', values, [], graphs, ['Apply selected astronomy relationship', 'Compute interpretable quantities', 'Return units and caveats'], 'python')


def materials_science_calculator(inputs):
    mode=inputs.get('mode') or 'stress_strain'
    kv=parse_kv(inputs.get('inputs') or 'force=1000;area=0.0005;delta_length=0.001;length=1;cycles=100000;stress_amplitude=150e6')
    graphs=[]; warnings=['Educational materials estimate only; verify with material-specific data, standards, and professional review.']
    if mode == 'diffusion':
        D=float(kv.get('diffusivity',1e-10)); t=float(kv.get('time',3600)); values={'diffusion_length_m':float(math.sqrt(2*D*t))}
    elif mode == 'thermal_conduction':
        k=float(kv.get('conductivity',0.8)); A=float(kv.get('area',10)); dT=float(kv.get('delta_t',20)); L=float(kv.get('thickness',0.2)); values={'heat_flow_watts':float(k*A*dT/L)}
    elif mode == 'fatigue_proxy':
        cycles=float(kv.get('cycles',100000)); amp=float(kv.get('stress_amplitude',150e6)); limit=float(kv.get('endurance_limit',120e6)); values={'stress_ratio_to_endurance_limit':float(amp/limit),'cycle_count':cycles};
        if amp > limit: warnings.append('Stress amplitude exceeds endurance-limit proxy; fatigue risk may be high.')
    else:
        F=float(kv.get('force',1000)); A=float(kv.get('area',0.0005)); dl=float(kv.get('delta_length',0.001)); L=float(kv.get('length',1)); stress=F/A; strain=dl/L; values={'stress_pa':stress,'strain':strain,'youngs_modulus_pa':stress/strain if strain else None}; graphs.append(bar_graph(['stress MPa','strain x1000'], [stress/1e6, strain*1000], 'Stress-strain summary'))
    return result('Materials Science Calculator', f'Ran materials mode: {mode}.', values, warnings, graphs, ['Parse material parameters', 'Apply selected engineering/material relationship', 'Render summary where useful'], 'python + optional C++')


def health_medical_public_health_tool(inputs):
    mode = inputs.get('mode') or 'public_health_risk'
    kv = parse_kv(inputs.get('inputs') or 'population=100000;cases=250;exposed=1000;unexposed=2000;cases_exposed=120;cases_unexposed=80;sensitivity=0.9;specificity=0.95;prevalence=0.02')
    warnings=['Educational public-health analytics only; not medical advice, diagnosis, treatment, or clinical triage.']
    graphs=[]
    if mode == 'screening_test':
        sens=float(kv.get('sensitivity',0.9)); spec=float(kv.get('specificity',0.95)); prev=float(kv.get('prevalence',0.02)); ppv=sens*prev/(sens*prev+(1-spec)*(1-prev)); npv=spec*(1-prev)/((1-sens)*prev+spec*(1-prev)); values={'positive_predictive_value':float(ppv),'negative_predictive_value':float(npv)}; graphs.append(bar_graph(['PPV','NPV'], [ppv,npv], 'Screening-test predictive values'))
    elif mode == 'relative_risk':
        ce=float(kv.get('cases_exposed',120)); e=float(kv.get('exposed',1000)); cu=float(kv.get('cases_unexposed',80)); u=float(kv.get('unexposed',2000)); rr=(ce/e)/(cu/u); values={'risk_exposed':ce/e,'risk_unexposed':cu/u,'relative_risk':float(rr)}; graphs.append(bar_graph(['exposed risk','unexposed risk'], [ce/e,cu/u], 'Relative risk comparison'))
    elif mode == 'sir_proxy':
        pop=float(kv.get('population',10000)); I0=float(kv.get('infectious',10)); beta=float(kv.get('beta',0.25)); gamma=float(kv.get('gamma',0.1)); days=int(kv.get('days',120)); S=pop-I0; I=I0; R=0; Ss=[]; Is=[]; Rs=[]
        for _ in range(days):
            Ss.append(S); Is.append(I); Rs.append(R); new=beta*S*I/pop; rec=gamma*I; S-=new; I+=new-rec; R+=rec
        fig,ax=plt.subplots(figsize=(7.5,4.5)); ax.plot(Is,label='infectious'); ax.plot(Rs,label='recovered'); ax.set_title('SIR proxy trajectory'); ax.legend(); ax.grid(alpha=.25); graphs.append({'title':'SIR proxy','type':'epidemic','svg':svg_from_figure(fig)}); plt.close(fig); values={'peak_infectious':float(max(Is)), 'final_recovered':float(Rs[-1])}
    else:
        population=float(kv.get('population',100000)); cases=float(kv.get('cases',250)); values={'incidence_per_100k':float(cases/population*100000), 'case_count':cases, 'population':population}; graphs.append(bar_graph(['cases','population/1000'], [cases,population/1000], 'Public-health incidence context'))
    return result('Health and Medical/Public Health Analytics Tool', f'Ran public-health mode: {mode}.', values, warnings, graphs, ['Select public-health model', 'Compute interpretable measure', 'Graph risk/trajectory when applicable', 'Return clinical-safety disclaimer'], 'python + optional R')


def international_law_issue_mapper(inputs):
    text=str(inputs.get('case') or 'A cross-border environmental harm affects coastal communities and critical habitats.').lower()
    lenses=['jurisdiction','state responsibility','treaty obligations','customary international law','human rights','international humanitarian law','environmental harm','remedies','evidence','forum']
    hits={lens: any(word in text for word in lens.split()) for lens in lenses}
    # broaden matching
    extra={'human rights':['rights','dignity','health','community'], 'environmental harm':['climate','pollution','ecosystem','biodiversity','water','coastal'], 'state responsibility':['attribution','breach','due diligence'], 'treaty obligations':['treaty','convention','protocol','agreement'], 'forum':['court','tribunal','committee','arbitration']}
    for k, words in extra.items(): hits[k]=hits.get(k,False) or any(w in text for w in words)
    scores=[1 if hits[l] else 0 for l in lenses]
    graph=bar_graph(lenses, scores, 'International law issue map', 'Flag')
    interpretation=['Educational issue spotting only, not legal advice.', 'Identify applicable instruments, jurisdiction, standing, evidence, attribution, breach, causation, remedies, and forum.', 'For environmental or rights impacts, include affected communities, due diligence, prevention, cooperation, and reparation questions.']
    return result('International Law Issue Mapper', 'Mapped a case description to major international-law issue areas.', {'flagged_issues':[l for l in lenses if hits[l]], 'issue_flags':hits}, ['Not legal advice. Use qualified counsel for real matters.'], [graph], ['Tokenize case description', 'Match against legal issue categories', 'Return structured issue map'], 'python + AI', interpretation)


def legal_traditions_comparator(inputs):
    traditions = [x.strip().lower() for x in str(inputs.get('traditions') or 'common law, civil law, islamic law').split(',') if x.strip()]
    dimensions=['sources of authority','role of precedent','codification','judicial reasoning','legal pluralism','religion/custom','institutional setting']
    profiles={}
    for t in traditions:
        profiles[t]={d:0.5 for d in dimensions}
        if 'common' in t: profiles[t].update({'role of precedent':1,'codification':0.35,'judicial reasoning':0.9})
        if 'civil' in t: profiles[t].update({'codification':1,'role of precedent':0.45,'judicial reasoning':0.65})
        if 'islamic' in t or 'religious' in t: profiles[t].update({'religion/custom':1,'sources of authority':0.9,'legal pluralism':0.75})
        if 'custom' in t or 'indigenous' in t: profiles[t].update({'religion/custom':0.8,'legal pluralism':1,'institutional setting':0.7})
        if 'socialist' in t: profiles[t].update({'codification':0.85,'institutional setting':0.9,'sources of authority':0.75})
    labels=list(profiles.keys()); vals=[np.mean(list(p.values())) for p in profiles.values()]
    graph=bar_graph(labels, vals, 'Comparative legal-tradition profile proxy')
    return result('Legal Traditions Comparator', 'Built an educational comparison matrix across major legal-tradition dimensions.', {'dimensions':dimensions,'profiles':profiles}, ['Comparative heuristic only; traditions are internally diverse and historically layered.'], [graph], ['Select traditions', 'Apply comparative dimensions', 'Return structured matrix and caveat diversity'], 'python + qualitative framework')


def metaphysics_framework_tool(inputs):
    question = str(inputs.get('question') or 'What changes while something remains the same?')
    lens = inputs.get('lens') or 'ontology'
    frameworks = {
        'ontology':['entities','properties','relations','categories','dependence','emergence'],
        'causation':['cause','condition','mechanism','counterfactual','agency','constraint'],
        'time':['persistence','change','sequence','duration','becoming','memory'],
        'identity':['selfhood','continuity','difference','boundary','recognition','personhood'],
        'mind_matter':['consciousness','embodiment','physicalism','experience','representation','agency'],
        'freedom':['choice','constraint','responsibility','determinism','possibility','action']
    }
    dims=frameworks.get(lens, frameworks['ontology'])
    text=question.lower(); scores=[1 if d.replace('_',' ') in text or d.split()[0] in text else 0.4 for d in dims]
    graph=bar_graph(dims, scores, f'Metaphysical lens: {lens}', 'Relevance proxy')
    interpretation=[f'Lens: {lens}. Use this as a question-structuring tool, not a truth calculator.', 'Separate what exists, how it changes, what depends on what, and which assumptions define the frame.', 'Compare at least two positions before concluding: realist, relational, process, phenomenological, materialist, or pluralist interpretations.']
    return result('Metaphysics Framework Tool', 'Generated a structured metaphysical analysis scaffold for ontology, causation, time, identity, mind/matter, or freedom.', {'question':question,'lens':lens,'dimensions':dims,'dimension_scores':dict(zip(dims,scores))}, [], [graph], ['Select lens', 'Map question to conceptual dimensions', 'Return interpretive scaffold'], 'python + AI', interpretation)
