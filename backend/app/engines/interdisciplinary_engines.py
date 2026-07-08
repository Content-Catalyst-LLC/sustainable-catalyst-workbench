from __future__ import annotations
import math, re
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, parse_number_list, result, svg_from_figure, bar_graph


def _series_graph(x, y, title, xlabel='x', ylabel='value'):
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.plot(x, y, marker='o')
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.grid(alpha=.25)
    svg = svg_from_figure(fig); plt.close(fig)
    return {'title': title, 'type': 'curve', 'svg': svg}


def physics_calculator(inputs):
    mode = inputs.get('mode') or 'mechanics'
    kv = parse_kv(inputs.get('inputs') or 'mass=2;velocity=12;height=5;force=10;distance=3;angle_deg=0')
    graphs=[]; warnings=[]
    if mode == 'mechanics':
        m=float(kv.get('mass',2)); v=float(kv.get('velocity',12)); r=float(kv.get('radius',3)); g=float(kv.get('gravity',9.80665))
        values={'momentum_kg_m_s':m*v,'kinetic_energy_j':0.5*m*v*v,'weight_n':m*g,'centripetal_force_n':m*v*v/r if r else None}
        graphs.append(bar_graph(['momentum','kinetic energy','weight','centripetal force'], [values['momentum_kg_m_s'], values['kinetic_energy_j'], values['weight_n'], values['centripetal_force_n'] or 0], 'Mechanics summary'))
    elif mode == 'waves':
        f=float(kv.get('frequency_hz',440)); wavelength=float(kv.get('wavelength_m',0.78)); T=1/f if f else None; v=f*wavelength
        values={'wave_speed_m_s':v,'period_s':T,'angular_frequency_rad_s':2*math.pi*f}
        xs=np.linspace(0, 2*wavelength if wavelength else 2, 200); y=np.sin(2*math.pi*xs/(wavelength or 1)); graphs.append(_series_graph(xs,y,'Wave profile proxy','position','amplitude'))
    elif mode == 'electricity':
        voltage=float(kv.get('voltage',12)); resistance=float(kv.get('resistance',6)); current=voltage/resistance if resistance else None
        values={'current_a':current,'power_w':voltage*current if current is not None else None,'resistance_ohm':resistance}
        graphs.append(bar_graph(['voltage','current','power'], [voltage,current or 0, voltage*(current or 0)], 'Electric circuit summary'))
    elif mode == 'fluids':
        rho=float(kv.get('density',1000)); velocity=float(kv.get('velocity',2)); diameter=float(kv.get('diameter',0.05)); mu=float(kv.get('dynamic_viscosity',0.001)); pressure=float(kv.get('pressure',101325)); area=float(kv.get('area',1))
        values={'reynolds_number':rho*velocity*diameter/mu if mu else None,'force_from_pressure_n':pressure*area,'dynamic_pressure_pa':0.5*rho*velocity**2}
        graphs.append(bar_graph(['Re/1000','pressure force/1000','dynamic pressure/1000'], [(values['reynolds_number'] or 0)/1000, values['force_from_pressure_n']/1000, values['dynamic_pressure_pa']/1000], 'Fluid mechanics summary'))
    elif mode == 'thermodynamics':
        m=float(kv.get('mass',1)); c=float(kv.get('specific_heat',4184)); dT=float(kv.get('delta_t',10)); q=m*c*dT
        values={'heat_energy_j':q,'mass_kg':m,'specific_heat_j_kg_k':c,'delta_t_k':dT}
        graphs.append(bar_graph(['mass','specific heat/1000','delta T','heat/10000'], [m,c/1000,dT,q/10000], 'Thermodynamics heat estimate'))
    else:
        F=float(kv.get('force',10)); d=float(kv.get('distance',3)); angle=math.radians(float(kv.get('angle_deg',0))); values={'work_j':F*d*math.cos(angle),'force_n':F,'distance_m':d}
    return result('Physics Calculator', f'Ran physics mode: {mode}.', values, warnings, graphs, ['Parse physical quantities', 'Apply selected introductory-to-applied physics relationship', 'Return units and visual summary'], 'python/numpy')


def chemistry_calculator(inputs):
    mode=inputs.get('mode') or 'molarity'
    kv=parse_kv(inputs.get('inputs') or 'moles=0.5;volume_l=1.0;mass_g=10;molar_mass_g_mol=58.44')
    graphs=[]; warnings=[]
    if mode == 'molarity':
        n=float(kv.get('moles',0.5)); V=float(kv.get('volume_l',1.0)); values={'molarity_mol_l':n/V if V else None,'moles':n,'volume_l':V}
        graphs.append(bar_graph(['moles','volume L','molarity'], [n,V,values['molarity_mol_l'] or 0], 'Molarity summary'))
    elif mode == 'stoichiometry':
        mass=float(kv.get('mass_g',10)); mm=float(kv.get('molar_mass_g_mol',58.44)); coeff_in=float(kv.get('coefficient_input',1)); coeff_out=float(kv.get('coefficient_output',1)); product_mm=float(kv.get('product_molar_mass_g_mol',18.015)); moles=mass/mm if mm else 0; product_moles=moles*coeff_out/coeff_in if coeff_in else 0
        values={'input_moles':moles,'product_moles_theoretical':product_moles,'product_mass_theoretical_g':product_moles*product_mm}
        graphs.append(bar_graph(['input mol','product mol','product g'], [moles,product_moles,product_moles*product_mm], 'Stoichiometric conversion'))
    elif mode == 'ph':
        h=float(kv.get('h_concentration',1e-7)); oh=float(kv.get('oh_concentration',1e-7)); ph=-math.log10(h) if h>0 else None; poh=-math.log10(oh) if oh>0 else None
        values={'ph':ph,'poh':poh,'classification':'acidic' if ph is not None and ph<7 else ('basic' if ph is not None and ph>7 else 'neutral')}
        graphs.append(bar_graph(['pH','pOH'], [ph or 0,poh or 0], 'Acid/base summary'))
    elif mode == 'ideal_gas':
        P=float(kv.get('pressure_pa',101325)); V=float(kv.get('volume_m3',0.024)); T=float(kv.get('temperature_k',298)); R=float(kv.get('r',8.314)); values={'moles':P*V/(R*T) if R*T else None,'pressure_pa':P,'volume_m3':V,'temperature_k':T}
    elif mode == 'beer_lambert':
        eps=float(kv.get('epsilon',10000)); c=float(kv.get('concentration_m',1e-4)); l=float(kv.get('path_length_cm',1)); values={'absorbance':eps*c*l,'epsilon':eps,'concentration_m':c,'path_length_cm':l}
    else:
        actual=float(kv.get('actual_yield_g',8)); theoretical=float(kv.get('theoretical_yield_g',10)); values={'percent_yield':100*actual/theoretical if theoretical else None}
    return result('Chemistry Calculator', f'Ran chemistry mode: {mode}.', values, warnings, graphs, ['Select chemistry relationship', 'Compute formula quantities with units', 'Return educational caveats'], 'python')


def biology_calculator(inputs):
    mode=inputs.get('mode') or 'population_growth'
    kv=parse_kv(inputs.get('inputs') or 'initial=100;rate=0.25;carrying_capacity=1000;time=30')
    graphs=[]; warnings=[]
    if mode == 'population_growth':
        N0=float(kv.get('initial',100)); r=float(kv.get('rate',0.25)); K=float(kv.get('carrying_capacity',1000)); t_end=int(kv.get('time',30)); t=np.arange(t_end+1); y=K/(1+((K-N0)/N0)*np.exp(-r*t)) if N0>0 else np.zeros_like(t)
        values={'final_population':float(y[-1]),'initial':N0,'rate':r,'carrying_capacity':K}; graphs.append(_series_graph(t,y,'Logistic population growth','time','population'))
    elif mode == 'enzyme_kinetics':
        vmax=float(kv.get('vmax',1.0)); km=float(kv.get('km',0.5)); s=float(kv.get('substrate',0.5)); rate=vmax*s/(km+s) if km+s else None
        xs=np.linspace(0, max(2, s*4), 200); ys=vmax*xs/(km+xs); values={'reaction_rate':rate,'vmax':vmax,'km':km}; graphs.append(_series_graph(xs,ys,'Michaelis-Menten curve','substrate','rate'))
    elif mode == 'hardy_weinberg':
        p=float(kv.get('p',0.6)); q=1-p; values={'p':p,'q':q,'AA':p*p,'Aa':2*p*q,'aa':q*q}; graphs.append(bar_graph(['AA','Aa','aa'], [p*p,2*p*q,q*q], 'Hardy-Weinberg genotype proportions'))
    elif mode == 'biodiversity':
        counts=np.array(parse_number_list(kv.get('counts',[10,20,5,8])) if not isinstance(kv.get('counts'), list) else kv.get('counts'), dtype=float); p=counts/(counts.sum() or 1); shannon=float(-np.sum([pi*math.log(pi) for pi in p if pi>0])); simpson=float(1-np.sum(p*p)); values={'species_count':int(len(counts)),'shannon_index':shannon,'simpson_diversity':simpson}; graphs.append(bar_graph([f's{i+1}' for i in range(len(counts))], counts.tolist(), 'Species abundance'))
    else:
        light=float(kv.get('light',0.8)); co2=float(kv.get('co2',0.7)); water=float(kv.get('water',0.9)); temp=float(kv.get('temperature_factor',0.8)); rate=min(light,co2,water)*temp; values={'photosynthesis_proxy_rate':rate,'limiting_factor':min({'light':light,'co2':co2,'water':water}, key={'light':light,'co2':co2,'water':water}.get)}
    return result('Biology Calculator', f'Ran biology mode: {mode}.', values, warnings, graphs, ['Select biological model', 'Compute ecological/physiological proxy', 'Render relevant curve or summary'], 'python/numpy')


def environmental_science_calculator(inputs):
    mode=inputs.get('mode') or 'water_quality_index'
    kv=parse_kv(inputs.get('inputs') or 'do=7;ph=7.4;turbidity=3;nitrate=2;phosphate=0.1;temperature=18')
    graphs=[]; warnings=[]
    if mode == 'water_quality_index':
        do=float(kv.get('do',7)); ph=float(kv.get('ph',7.4)); turb=float(kv.get('turbidity',3)); nitrate=float(kv.get('nitrate',2)); phosphate=float(kv.get('phosphate',0.1));
        scores={'dissolved_oxygen':min(100,do/9*100),'ph_balance':max(0,100-abs(ph-7.2)*25),'turbidity':max(0,100-turb*8),'nitrate':max(0,100-nitrate*10),'phosphate':max(0,100-phosphate*80)}; values={'water_quality_index_proxy':float(np.mean(list(scores.values()))),'component_scores':scores}; graphs.append(bar_graph(list(scores.keys()), list(scores.values()), 'Water quality proxy components', 'Score'))
    elif mode == 'air_quality_proxy':
        pm25=float(kv.get('pm25',12)); no2=float(kv.get('no2',30)); o3=float(kv.get('o3',70)); scores={'pm25_pressure':pm25/35*100,'no2_pressure':no2/100*100,'ozone_pressure':o3/160*100}; values={'air_quality_pressure_proxy':float(np.mean(list(scores.values()))),'component_pressures':scores}; graphs.append(bar_graph(list(scores.keys()), list(scores.values()), 'Air-quality pressure proxy'))
    elif mode == 'carbon_footprint':
        electricity=float(kv.get('electricity_kwh',500)); gas=float(kv.get('gas_therms',40)); travel=float(kv.get('travel_miles',600)); values={'co2e_kg_proxy':electricity*0.4 + gas*5.3 + travel*0.404}; graphs.append(bar_graph(['electricity','gas','travel'], [electricity*0.4, gas*5.3, travel*0.404], 'Carbon footprint proxy kg CO2e'))
    elif mode == 'habitat_fragmentation':
        patches=float(kv.get('patches',5)); area=float(kv.get('area',100)); edge=float(kv.get('edge_length',50)); values={'patch_density':patches/area if area else None,'edge_to_area_ratio':edge/area if area else None,'fragmentation_pressure_proxy':float((patches/area if area else 0)*50 + (edge/area if area else 0)*10)}
    else:
        pressures=['climate','water','biodiversity','pollution','land_use','equity']; vals=np.array([float(kv.get(p,3)) for p in pressures]); values={'composite_environmental_risk':float(np.mean(vals)),'pressures':dict(zip(pressures, vals.tolist()))}; graphs.append(bar_graph(pressures, vals.tolist(), 'Environmental risk pressure profile'))
    if any(v for v in values.values() if isinstance(v,(int,float)) and v and v>75): warnings.append('High proxy score detected; use professional environmental review and local standards for decisions.')
    return result('Environmental Science Calculator', f'Ran environmental science mode: {mode}.', values, warnings, graphs, ['Parse environmental indicators', 'Normalize or aggregate pressures', 'Return proxy score and caveats'], 'python/numpy')


def earth_science_calculator(inputs):
    mode=inputs.get('mode') or 'watershed_runoff'
    kv=parse_kv(inputs.get('inputs') or 'rainfall_mm=50;area_km2=10;runoff_coefficient=0.35;slope=8;soil_erodibility=0.3')
    graphs=[]; warnings=[]
    if mode == 'watershed_runoff':
        rain=float(kv.get('rainfall_mm',50)); area=float(kv.get('area_km2',10)); c=float(kv.get('runoff_coefficient',0.35)); volume=rain/1000*area*1e6*c; values={'runoff_volume_m3':volume,'rainfall_mm':rain,'area_km2':area,'runoff_coefficient':c}; graphs.append(bar_graph(['rain mm','area km2','runoff coeff x100','volume/10000'], [rain,area,c*100,volume/10000], 'Watershed runoff proxy'))
    elif mode == 'earthquake_energy':
        M=float(kv.get('magnitude',6.0)); energy=10**(1.5*M+4.8); values={'energy_joules_proxy':energy,'magnitude':M}; warnings.append('Magnitude-energy relation is approximate and not a hazard forecast.')
    elif mode == 'erosion_risk':
        rainfall=float(kv.get('rainfall_factor',3)); slope=float(kv.get('slope',8)); soil=float(kv.get('soil_erodibility',0.3)); cover=float(kv.get('cover_protection',0.6)); risk=rainfall*slope*soil*(1-cover); values={'erosion_risk_proxy':risk,'factors':{'rainfall':rainfall,'slope':slope,'soil_erodibility':soil,'cover_protection':cover}}; graphs.append(bar_graph(['rainfall','slope','soil','lack of cover'], [rainfall,slope,soil,1-cover], 'Erosion-risk factors'))
    elif mode == 'rock_density':
        mass=float(kv.get('mass_kg',2.7)); volume=float(kv.get('volume_m3',0.001)); values={'density_kg_m3':mass/volume if volume else None}
    else:
        precipitation=float(kv.get('precipitation_mm',800)); evap=float(kv.get('evapotranspiration_mm',500)); runoff=float(kv.get('runoff_mm',200)); recharge=precipitation-evap-runoff; values={'water_balance_recharge_mm_proxy':recharge,'precipitation_mm':precipitation,'evapotranspiration_mm':evap,'runoff_mm':runoff}; graphs.append(bar_graph(['precip','ET','runoff','recharge'], [precipitation,evap,runoff,recharge], 'Water-balance proxy'))
    return result('Earth Science Calculator', f'Ran earth science mode: {mode}.', values, warnings, graphs, ['Select earth-system relationship', 'Compute hazard/hydrology/geology proxy', 'Return units and professional caveats'], 'python/numpy')


def content_frameworks_analyzer(inputs):
    text=str(inputs.get('brief') or 'Explain a complex public-interest tool to a mixed audience and connect it to research, ethics, and action.')
    lens=inputs.get('lens') or 'knowledge_architecture'
    dims=['purpose','audience','problem','evidence','structure','voice','action','ethics','measurement']
    t=text.lower(); scores=[]
    for d in dims:
        keywords={
          'purpose':['purpose','goal','why','mission'], 'audience':['audience','reader','public','user'], 'problem':['problem','challenge','risk'], 'evidence':['evidence','data','source','research'], 'structure':['structure','map','framework','sequence'], 'voice':['voice','tone','story','narrative'], 'action':['action','decision','practice','use'], 'ethics':['ethics','responsible','rights','justice'], 'measurement':['measure','metric','evaluate','outcome']
        }[d]
        scores.append(1.0 if any(k in t for k in keywords) else 0.45)
    graph=bar_graph(dims,scores,f'Content framework lens: {lens}','Coverage proxy')
    interp=['Clarify the job of the content before drafting.', 'Separate structure from style: purpose, audience, evidence, sequence, action, and responsibility.', 'Use this as a content-architecture diagnostic, not a substitute for editorial judgment.']
    return result('Content Frameworks Analyzer','Mapped a content brief to strategic and knowledge-architecture dimensions.', {'lens':lens,'coverage':dict(zip(dims,scores))}, [], [graph], ['Tokenize brief', 'Score framework dimensions', 'Return editorial architecture map'], 'python + AI', interp)


def storytelling_structure_analyzer(inputs):
    story=str(inputs.get('story') or 'A researcher builds a public-interest tool, faces uncertainty, tests it with users, and turns it into shared infrastructure.')
    mode=inputs.get('mode') or 'narrative_arc'
    dims=['setting','character','desire','conflict','stakes','turning_point','resolution','meaning','memory']
    t=story.lower(); cues={
      'setting':['where','world','context','place'], 'character':['person','researcher','community','team'], 'desire':['wants','goal','seeks','builds'], 'conflict':['faces','risk','problem','uncertainty','barrier'], 'stakes':['stakes','cost','harm','loss','future'], 'turning_point':['then','but','shift','discovers','tests'], 'resolution':['resolves','becomes','turns','delivers'], 'meaning':['meaning','why','lesson','symbol'], 'memory':['remember','legacy','shared','public']}
    scores=[1.0 if any(k in t for k in cues[d]) else 0.4 for d in dims]
    graph=bar_graph(dims,scores,'Story structure diagnostic','Presence proxy')
    interp=['Look for movement: situation, desire, friction, choice, consequence, and meaning.', 'For Sustainable Catalyst, storytelling should clarify systems and responsibility rather than become decoration.']
    return result('Storytelling Structure Analyzer', f'Analyzed story through mode: {mode}.', {'mode':mode,'structure_scores':dict(zip(dims,scores))}, [], [graph], ['Scan narrative text', 'Map story elements', 'Return structure and meaning cues'], 'python + qualitative framework', interp)


def social_psychology_analyzer(inputs):
    scenario=str(inputs.get('scenario') or 'A group is deciding whether to adopt a new tool while norms, trust, authority, incentives, and uncertainty shape behavior.')
    lens=inputs.get('lens') or 'group_dynamics'
    dims=['norms','identity','authority','trust','conformity','polarization','attribution','persuasion','cooperation','diffusion']
    keywords={d:[d] for d in dims}; keywords.update({'authority':['authority','leader','expert'], 'trust':['trust','credibility','confidence'], 'cooperation':['cooperate','shared','collective'], 'diffusion':['spread','adopt','diffusion'], 'conformity':['conform','norm','pressure']})
    t=scenario.lower(); scores=[1.0 if any(k in t for k in keywords[d]) else 0.5 for d in dims]
    graph=bar_graph(dims,scores,f'Social psychology lens: {lens}','Relevance proxy')
    interp=['Use this to identify social mechanisms, not to manipulate users.', 'Check norms, identity, trust, incentives, group pressure, and institutional context before proposing interventions.']
    return result('Social Psychology Analyzer','Mapped a scenario to social-psychology mechanisms relevant to behavior, trust, groups, and adoption.', {'lens':lens,'mechanism_scores':dict(zip(dims,scores))}, [], [graph], ['Scan scenario', 'Score social mechanisms', 'Return non-manipulative intervention cautions'], 'python + qualitative framework', interp)


def grit_resilience_analyzer(inputs):
    values=np.array(parse_number_list(inputs.get('responses') or '4,5,4,3,5,4,4,5'), dtype=float)
    context=str(inputs.get('context') or 'Long-term learning, career transition, creative work, and sustained project execution.')
    mean=float(np.mean(values)) if len(values) else 0.0; sd=float(np.std(values,ddof=1)) if len(values)>1 else 0.0
    dimensions=['perseverance','consistency','recovery','deliberate_practice','purpose_alignment']
    # heuristic profile: mean anchors perseverance/purpose, SD reduces consistency
    scores=[mean/5, max(0,1-sd/2), min(1,mean/5+0.05), min(1,(mean/5)*0.9), 0.8 if any(k in context.lower() for k in ['long-term','purpose','project','career','learning']) else 0.55]
    graph=bar_graph(dimensions, scores, 'Grit and resilience profile', '0-1 proxy')
    warnings=['Not a psychological diagnosis or validated clinical assessment. Use as reflective/educational support only.']
    interp=['Grit should be paired with judgment: persistence is valuable when goals, feedback, and health are sustainable.', 'Separate perseverance from rigidity; build recovery loops and periodic re-evaluation into long projects.']
    return result('Grit and Resilience Analyzer','Computed a reflective grit/resilience profile from self-ratings and context.', {'mean_response':mean,'response_sd':sd,'profile':dict(zip(dimensions,scores))}, warnings, [graph], ['Parse item responses', 'Estimate profile dimensions', 'Return reflective interpretation and caveats'], 'python + optional R', interp)
