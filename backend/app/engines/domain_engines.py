from __future__ import annotations
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from .common import parse_kv, parse_number_list, parse_rows, result, svg_from_figure, bar_graph


def decision_analysis_tool(inputs):
    rows = []
    for line in str(inputs.get('options', 'Option A,8,6,7\nOption B,6,9,8')).splitlines():
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if len(parts) >= 2:
            rows.append((parts[0], [float(x) for x in parts[1:]]))
    weights = np.array(parse_number_list(inputs.get('weights', '')), dtype=float)
    if not rows: raise ValueError('Enter options as name,score1,score2,...')
    n = len(rows[0][1])
    if weights.size != n: weights = np.repeat(1/n, n)
    weights = weights / weights.sum()
    scores = [(name, float(np.dot(vals, weights))) for name, vals in rows]
    graph = bar_graph([s[0] for s in scores], [s[1] for s in scores], 'Weighted decision scores', 'Score')
    best = max(scores, key=lambda x: x[1])
    return result('Decision Analysis Tool', 'Computed weighted decision scores and identified the highest-scoring option.', {"weights": weights.tolist(), "scores": dict(scores), "best_option": best[0]}, [], [graph], ['Normalize weights', 'Score each option', 'Compare alternatives', 'Flag best-scoring option'], 'python')


def economics_calculator(inputs):
    mode = inputs.get('mode') or 'npv'; kv = parse_kv(inputs.get('inputs') or 'rate=0.08; cashflows=-1000,300,400,500'); graphs=[]; warnings=[]
    if mode == 'elasticity':
        p1,p2,q1,q2 = [float(kv.get(k, 1)) for k in ['p1','p2','q1','q2']]
        e = ((q2-q1)/((q1+q2)/2)) / ((p2-p1)/((p1+p2)/2))
        values = {"arc_elasticity": float(e), "classification": "elastic" if abs(e)>1 else "inelastic"}
    elif mode == 'supply_demand':
        a=float(kv.get('demand_intercept',100)); b=float(kv.get('demand_slope',2)); c=float(kv.get('supply_intercept',20)); d=float(kv.get('supply_slope',1)); q_eq=(a-c)/(b+d); p_eq=a-b*q_eq
        q=np.linspace(0,max(q_eq*2,10),300); fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(q,a-b*q,label='Demand'); ax.plot(q,c+d*q,label='Supply'); ax.scatter([q_eq],[p_eq]); ax.set_title('Supply and demand'); ax.set_xlabel('Quantity'); ax.set_ylabel('Price'); ax.legend(); ax.grid(alpha=.25); graphs.append({"title":"Supply-demand equilibrium","type":"equilibrium","svg":svg_from_figure(fig)}); plt.close(fig); values={"equilibrium_quantity":float(q_eq),"equilibrium_price":float(p_eq)}
    elif mode == 'break_even':
        fixed=float(kv.get('fixed_cost',1000)); price=float(kv.get('price',25)); variable=float(kv.get('variable_cost',10)); values={"contribution_margin":price-variable,"break_even_units":float(fixed/(price-variable))}
    elif mode == 'inequality_gini':
        vals=np.sort(np.array(kv.get('values',[10,20,30,40,100]), dtype=float)); n=len(vals); gini=float((2*np.arange(1,n+1)-n-1).dot(vals)/(n*vals.sum())) if vals.sum() else 0
        lorenz=np.r_[0, np.cumsum(vals)/vals.sum()] if vals.sum() else np.zeros(n+1); fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(np.linspace(0,1,n+1),lorenz,label='Lorenz'); ax.plot([0,1],[0,1],linestyle='--'); ax.set_title('Lorenz curve'); ax.legend(); ax.grid(alpha=.25); graphs.append({"title":"Lorenz curve","type":"lorenz","svg":svg_from_figure(fig)}); plt.close(fig); values={"gini":gini}
    elif mode == 'input_output':
        A=np.array([[0.2,0.1],[0.3,0.2]]); d=np.array(kv.get('demand',[100,80]), dtype=float); x=np.linalg.solve(np.eye(A.shape[0])-A,d); values={"gross_output":x.tolist(),"technology_matrix":A.tolist()}; warnings.append('Demo 2-sector matrix used unless custom matrix support is added.')
    else:
        rate=float(kv.get('rate',0.08)); cashflows=kv.get('cashflows',[-1000,300,400,500]); cashflows=np.array(cashflows,dtype=float); npv=float(sum(cf/((1+rate)**i) for i,cf in enumerate(cashflows))); values={"npv":npv,"rate":rate,"cashflows":cashflows.tolist()}; graphs.append(bar_graph([str(i) for i in range(len(cashflows))], cashflows.tolist(), 'Cash flows', 'Cash flow'))
    return result('Economics Calculator', f'Ran economics mode: {mode}.', values, warnings, graphs, engine='python + optional R/Julia')


def energy_systems_calculator(inputs):
    mode=inputs.get('mode') or 'electricity_cost_emissions'; kv=parse_kv(inputs.get('inputs') or 'kwh=500;rate=0.16;kgco2_per_kwh=0.4'); graphs=[]
    if mode == 'solar_pv':
        kw=float(kv.get('kw',5)); sun=float(kv.get('sun_hours',4.2)); pr=float(kv.get('performance_ratio',.8)); daily=kw*sun*pr; monthly=np.array([31,28,31,30,31,30,31,31,30,31,30,31])*daily; values={"daily_kwh":daily,"annual_kwh":float(monthly.sum())}; graphs.append(bar_graph(['J','F','M','A','M','J','J','A','S','O','N','D'], monthly.tolist(), 'Estimated monthly solar generation', 'kWh'))
    elif mode == 'battery_autonomy':
        battery=float(kv.get('battery_kwh',13.5)); load=float(kv.get('load_kw',1.2)); dod=float(kv.get('depth_of_discharge',.9)); values={"usable_kwh":battery*dod,"autonomy_hours":battery*dod/load}; graphs.append(bar_graph(['usable kWh','load kW','hours'], [values['usable_kwh'], load, values['autonomy_hours']], 'Battery autonomy'))
    elif mode == 'lcoe':
        capex=float(kv.get('capex',100000)); annual_om=float(kv.get('annual_om',2000)); annual_kwh=float(kv.get('annual_kwh',100000)); rate=float(kv.get('rate',.06)); years=int(kv.get('years',25)); crf=(rate*(1+rate)**years)/((1+rate)**years-1); values={"capital_recovery_factor":crf,"lcoe_per_kwh":(capex*crf+annual_om)/annual_kwh}
    elif mode == 'building_eui':
        area=float(kv.get('area_m2',1000)); annual=float(kv.get('annual_kwh',180000)); values={"eui_kwh_per_m2_year":annual/area,"area_m2":area,"annual_kwh":annual}; graphs.append(bar_graph(['EUI'], [annual/area], 'Building energy use intensity', 'kWh/m²-year'))
    elif mode == 'energy_mix':
        labels=[]; vals=[]
        for k,v in kv.items():
            if isinstance(v,(int,float)): labels.append(k); vals.append(float(v))
        total=sum(vals) or 1; values={"total":total,"shares":{l:vals[i]/total for i,l in enumerate(labels)}}; graphs.append(bar_graph(labels, vals, 'Energy mix scenario', 'Energy'))
    else:
        kwh=float(kv.get('kwh',500)); rate=float(kv.get('rate',.16)); kg=float(kv.get('kgco2_per_kwh',.4)); values={"cost":kwh*rate,"emissions_kgco2":kwh*kg,"kwh":kwh}; graphs.append(bar_graph(['kWh','Cost','kg CO₂'], [kwh,kwh*rate,kwh*kg], 'Energy cost and emissions'))
    return result('Energy Systems Calculator', f'Ran energy mode: {mode}.', values, [], graphs, engine='python + optional Julia/EnergyPlus')


def psychology_scale_analyzer(inputs):
    mode=inputs.get('mode') or 'scale_reliability'; graphs=[]; warnings=[]
    if mode == 'effect_size':
        a=np.array(parse_number_list(inputs.get('group_a','')), dtype=float); b=np.array(parse_number_list(inputs.get('group_b','')), dtype=float)
        if a.size < 2 or b.size < 2: raise ValueError('Provide group_a and group_b with at least two values each.')
        pooled=np.sqrt(((a.size-1)*a.var(ddof=1)+(b.size-1)*b.var(ddof=1))/(a.size+b.size-2)); d=(a.mean()-b.mean())/pooled; values={"cohens_d":float(d),"mean_a":float(a.mean()),"mean_b":float(b.mean())}; graphs.append(bar_graph(['A mean','B mean'], [a.mean(), b.mean()], 'Group mean comparison'))
    elif mode == 'memory_decay':
        initial=float(inputs.get('initial',100)); rate=float(inputs.get('rate',.12)); t=np.linspace(0,30,300); y=initial*np.exp(-rate*t); values={"initial":initial,"rate":rate,"day_30":float(y[-1])}; fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(t,y); ax.set_title('Memory decay curve'); ax.set_xlabel('time'); ax.set_ylabel('retention'); ax.grid(alpha=.25); graphs.append({"title":"Memory decay","type":"curve","svg":svg_from_figure(fig)}); plt.close(fig)
    elif mode == 'grit_profile':
        data=np.array(parse_number_list(inputs.get('responses','4,5,4,3,5,4,5,4')), dtype=float); values={"mean_grit_score":float(data.mean()),"items":int(data.size),"interpretation":"higher sustained-effort profile" if data.mean()>=4 else "moderate or developing sustained-effort profile"}; graphs.append(bar_graph([f'I{i+1}' for i in range(data.size)], data.tolist(), 'Grit item profile', 'Score'))
    elif mode == 'signal_detection':
        hit=float(inputs.get('hit_rate',.8)); fa=float(inputs.get('false_alarm_rate',.2)); hit=np.clip(hit,.001,.999); fa=np.clip(fa,.001,.999); values={"d_prime":float(stats.norm.ppf(hit)-stats.norm.ppf(fa)),"criterion":float(-0.5*(stats.norm.ppf(hit)+stats.norm.ppf(fa)))}
    else:
        data=parse_rows(inputs.get('responses','4,5,4,3\n3,4,4,2\n5,5,4,4'))
        if data.size == 0: raise ValueError('Enter rows of item responses.')
        total=data.sum(axis=1); k=data.shape[1]; total_var=total.var(ddof=1) if data.shape[0]>1 else 0; item_vars=data.var(axis=0,ddof=1) if data.shape[0]>1 else np.zeros(k); alpha=(k/(k-1))*(1-item_vars.sum()/total_var) if k>1 and total_var>0 else None; values={"respondents":int(data.shape[0]),"items":int(k),"mean_total_score":float(total.mean()),"cronbach_alpha":None if alpha is None else float(alpha),"item_means":data.mean(axis=0).tolist()}; fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.boxplot([data[:,i] for i in range(k)]); ax.set_title('Item response distributions'); ax.set_xlabel('Item'); ax.set_ylabel('Score'); graphs.append({"title":"Scale profile","type":"boxplot","svg":svg_from_figure(fig)}); plt.close(fig)
    return result('Psychology Scale Analyzer', f'Ran psychology mode: {mode}.', values, warnings, graphs, engine='python + optional R')


def scientific_calculator(inputs):
    mode=inputs.get('mode') or 'ideal_gas'; kv=parse_kv(inputs.get('inputs') or 'n=1;R=8.314;T=298;V=0.024'); graphs=[]
    if mode == 'kinetic_energy': values={"kinetic_energy_joules":0.5*float(kv.get('mass',1))*float(kv.get('velocity',1))**2}
    elif mode == 'stress_strain':
        F=float(kv.get('force',1000)); A=float(kv.get('area',.01)); dl=float(kv.get('delta_length',.002)); L=float(kv.get('length',1)); stress=F/A; strain=dl/L; values={"stress_pa":stress,"strain":strain,"youngs_modulus_estimate_pa":stress/strain if strain else None}
    elif mode == 'dilution': values={"required_final_volume":float(kv.get('c1',1))*float(kv.get('v1',1))/float(kv.get('c2',.1))}
    elif mode == 'logistic_population':
        N0=float(kv.get('N0',10)); r=float(kv.get('r',.2)); K=float(kv.get('K',100)); t=np.linspace(0,50,300); y=K/(1+((K-N0)/N0)*np.exp(-r*t)); values={"final_population":float(y[-1])}; fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(t,y); ax.set_title('Logistic population growth'); graphs.append({"title":"Population curve","type":"curve","svg":svg_from_figure(fig)}); plt.close(fig)
    elif mode == 'orbital_period':
        G=6.67430e-11; M=float(kv.get('central_mass',5.972e24)); r=float(kv.get('orbital_radius',6.771e6)); values={"orbital_period_seconds":float(2*np.pi*np.sqrt(r**3/(G*M)))}
    elif mode == 'reynolds_number': values={"reynolds_number":float(kv.get('density',1000))*float(kv.get('velocity',1))*float(kv.get('length',1))/float(kv.get('viscosity',.001))}
    else: values={"pressure_pa":float(kv.get('n',1))*float(kv.get('r',kv.get('R',8.314)))*float(kv.get('t',kv.get('T',298)))/float(kv.get('v',kv.get('V',.024)))}
    return result('Scientific Calculator', f'Ran scientific mode: {mode}.', values, [], graphs, engine='python + optional Julia')


def engineering_calculator(inputs):
    mode=inputs.get('mode') or 'beam_uniform_load'; kv=parse_kv(inputs.get('inputs') or 'span=6;load=10;E=200e9;I=8e-6'); graphs=[]; warnings=['Educational estimate only. Do not use for final design, permitting, or safety-critical decisions.']
    if mode == 'beam_uniform_load':
        L=float(kv.get('span',6)); w=float(kv.get('load',10))*1000; E=float(kv.get('e',kv.get('E',200e9))); I=float(kv.get('i',kv.get('I',8e-6))); x=np.linspace(0,L,300); V=w*(L/2-x); M=w*x*(L-x)/2; delta_max=5*w*L**4/(384*E*I); values={"max_moment_Nm":float(w*L**2/8),"max_shear_N":float(w*L/2),"max_deflection_m":float(delta_max)}; fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(x,V,label='Shear'); ax.plot(x,M,label='Moment'); ax.set_title('Beam shear and moment'); ax.legend(); ax.grid(alpha=.25); graphs.append({"title":"Shear and moment","type":"engineering","svg":svg_from_figure(fig)}); plt.close(fig)
    elif mode == 'column_buckling':
        E=float(kv.get('E',200e9)); I=float(kv.get('I',8e-6)); L=float(kv.get('length',3)); K=float(kv.get('k_factor',1)); values={"euler_critical_load_N":float(np.pi**2*E*I/(K*L)**2)}
    elif mode == 'factor_of_safety': values={"factor_of_safety":float(kv.get('capacity',100))/float(kv.get('demand',50))}
    elif mode == 'voltage_drop': values={"voltage_drop":2*float(kv.get('current',20))*float(kv.get('length',30))*float(kv.get('resistance_per_m',.005))}
    elif mode == 'heat_transfer': values={"heat_transfer_watts":float(kv.get('u_value',.3))*float(kv.get('area',50))*float(kv.get('delta_t',20))}
    else: values={"reynolds_number":float(kv.get('density',1000))*float(kv.get('velocity',1))*float(kv.get('diameter',.1))/float(kv.get('viscosity',.001))}
    return result('Engineering Calculator', f'Ran engineering mode: {mode}.', values, warnings, graphs, engine='python + optional C++')


def architecture_building_calculator(inputs):
    mode=inputs.get('mode') or 'space_program'; kv=parse_kv(inputs.get('inputs') or 'area_m2=1000;annual_kwh=180000'); graphs=[]; warnings=['Educational planning estimate only. Confirm with licensed architects, engineers, code officials, and local regulations.']
    if mode == 'occupancy_load': values={"estimated_occupants":float(kv.get('area_m2',1000))/float(kv.get('area_per_person',10))}
    elif mode == 'building_eui': values={"eui_kwh_per_m2_year":float(kv.get('annual_kwh',180000))/float(kv.get('area_m2',1000))}; graphs.append(bar_graph(['EUI'], [values['eui_kwh_per_m2_year']], 'Building EUI', 'kWh/m²-year'))
    elif mode == 'embodied_carbon':
        labels=[]; vals=[]
        for k,v in kv.items():
            if k.endswith('_kgco2e') and isinstance(v,(float,int)): labels.append(k.replace('_kgco2e','')); vals.append(float(v))
        if not vals: labels=['structure','envelope','interior']; vals=[50000,20000,10000]
        values={"total_embodied_carbon_kgco2e":sum(vals),"components":dict(zip(labels,vals))}; graphs.append(bar_graph(labels, vals, 'Embodied carbon by component', 'kgCO₂e'))
    elif mode == 'solar_shading': values={"simple_shade_depth_m":float(kv.get('window_height',1.5))/max(np.tan(np.deg2rad(float(kv.get('solar_altitude_deg',60)))),1e-9)}
    elif mode == 'adjacency_matrix': values={"note":"Use a matrix of program spaces and desired adjacency weights. Detailed matrix parser can be expanded in the next release."}
    else:
        total=float(kv.get('total_area',1000)); net=float(kv.get('net_program_area',700)); values={"gross_area_m2":total,"net_program_area_m2":net,"efficiency_ratio":net/total}
        graphs.append(bar_graph(['Net program','Support/circulation'], [net,total-net], 'Space program allocation', 'm²'))
    return result('Architecture & Building Calculator', f'Ran architecture mode: {mode}.', values, warnings, graphs, engine='python + optional EnergyPlus/IfcOpenShell')


def sustainability_resilience_scorecard(inputs):
    kv=parse_kv(inputs.get('scores') or 'exposure=4;sensitivity=3;adaptive_capacity=2;governance=3;equity=2;recovery=4')
    labels=list(kv.keys()); vals=[float(v) for v in kv.values() if isinstance(v,(float,int))]
    if not vals: raise ValueError('Enter named numeric scores.')
    # Low exposure/sensitivity and high adaptive capacity/governance/equity/recovery are better.
    score=float(np.mean(vals)); graph=bar_graph(labels, vals, 'Resilience factor profile', 'Score')
    return result('Sustainability & Resilience Scorecard', 'Computed a structured resilience profile. Interpret with local context and evidence.', {"average_score":score,"factors":dict(zip(labels, vals))}, [], [graph], engine='python')


def ai_governance_audit(inputs):
    kv=parse_kv(inputs.get('scores') or 'data_quality=3;transparency=2;human_oversight=4;contestability=2;impact=4')
    labels=list(kv.keys()); vals=[float(v) for v in kv.values() if isinstance(v,(float,int))]
    risk=float(np.mean(vals)); warnings=[]
    if risk >= 3.5: warnings.append('High governance risk profile. Strengthen documentation, oversight, testing, contestability, and accountability before deployment.')
    graph=bar_graph(labels, vals, 'AI governance risk factors', 'Risk score')
    return result('AI Governance Audit', 'Audited AI system risk factors across documentation, oversight, data quality, impact, and contestability.', {"average_risk_score":risk,"factors":dict(zip(labels, vals))}, warnings, [graph], engine='python + optional Haskell')


def haskell_rule_checker(inputs):
    rules=str(inputs.get('rules') or '').splitlines(); warnings=[]; facts=[]
    for r in rules:
        rr=r.strip().lower()
        if rr.startswith('if') and 'then' in rr: facts.append(rr)
        if 'not ' in rr and rr.replace('not ','') in '\n'.join(rules).lower(): warnings.append('Potential contradiction detected: positive and negative form appear together.')
    return result('Haskell Rule Checker', 'Parsed simple IF/THEN rules and checked for obvious contradictions. Optional Haskell bridge can enforce richer typed rule logic.', {"rules_seen":len(rules),"conditional_rules":len(facts),"contradictions_found":len(warnings)}, warnings, [], engine='python + optional Haskell')


def qualitative_interpretation_matrix(inputs):
    text=str(inputs.get('text') or ''); lens=inputs.get('lens') or 'systems'
    values={"lens":lens,"length":len(text),"suggested_dimensions":["context","actors","symbols","tensions","assumptions","consequences","limits"]}
    interpretation=[f"Use the {lens} lens to separate description from interpretation.", "Identify what evidence supports each claim.", "Keep uncertainty visible; qualitative tools structure judgment rather than replacing it."]
    return result('Qualitative Interpretation Matrix', 'Created a structured interpretive matrix for qualitative reasoning.', values, [], [], engine='python + AI', interpretation=interpretation)
