
from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, parse_number_list, result, svg_from_figure, bar_graph

C = 299_792_458.0
G0 = 9.80665
E_CHARGE = 1.602176634e-19
AMU_MEV = 931.49410242
HBAR_EV_S = 6.582119569e-16
K_B = 1.380649e-23
R_GAS = 8.314462618


def _curve(x, y, title, xlabel='x', ylabel='value'):
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(x, y, linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(alpha=.28)
    svg = svg_from_figure(fig); plt.close(fig)
    return {'title': title, 'type': 'high_resolution_svg_curve', 'svg': svg, 'export_formats': ['svg', 'png', 'pdf_report']}


def _bars(labels, values, title, ylabel='Value'):
    g = bar_graph(labels, values, title, ylabel)
    g['type'] = 'high_resolution_svg_bar'
    g['export_formats'] = ['svg', 'png', 'pdf_report']
    return g


def nuclear_physics_calculator(inputs):
    mode = inputs.get('mode') or 'radioactive_decay'
    kv = parse_kv(inputs.get('inputs') or 'initial_activity_bq=1000;half_life_s=3600;time_s=7200;mass_defect_u=0.01')
    graphs=[]; warnings=['Educational nuclear/radiation physics only. Does not support weapons design, enrichment, reactor operation, or hazardous-material handling.']
    if mode == 'radioactive_decay':
        A0=float(kv.get('initial_activity_bq',1000)); half=float(kv.get('half_life_s',3600)); t=float(kv.get('time_s',7200)); lam=math.log(2)/half if half>0 else 0
        A=A0*math.exp(-lam*t) if lam else A0
        xs=np.linspace(0, max(t, half*5), 240); ys=A0*np.exp(-lam*xs) if lam else np.ones_like(xs)*A0
        values={'decay_constant_s_inv':lam,'remaining_activity_bq':A,'remaining_fraction':A/A0 if A0 else None,'elapsed_half_lives':t/half if half else None}
        graphs.append(_curve(xs, ys, 'Radioactive decay curve', 'time (s)', 'activity (Bq)'))
    elif mode == 'binding_energy':
        mass_defect=float(kv.get('mass_defect_u',0.01)); nucleons=float(kv.get('nucleons',56)); be=mass_defect*AMU_MEV
        values={'binding_energy_mev':be,'binding_energy_per_nucleon_mev':be/nucleons if nucleons else None,'mass_defect_u':mass_defect}
        graphs.append(_bars(['mass defect u','BE MeV','BE/A MeV'], [mass_defect,be,be/nucleons if nucleons else 0], 'Binding energy summary'))
    elif mode == 'radiation_dose_proxy':
        energy_j=float(kv.get('absorbed_energy_j',0.001)); mass_kg=float(kv.get('mass_kg',1)); quality=float(kv.get('radiation_weighting_factor',1)); gy=energy_j/mass_kg if mass_kg else None
        values={'absorbed_dose_gy':gy,'equivalent_dose_sv':gy*quality if gy is not None else None,'radiation_weighting_factor':quality}
        graphs.append(_bars(['absorbed Gy','equiv Sv'], [gy or 0, (gy or 0)*quality], 'Radiation dose educational proxy'))
    else:
        t12=float(kv.get('half_life_s',3600)); lam=math.log(2)/t12 if t12 else 0; tau=1/lam if lam else None
        values={'mean_lifetime_s':tau,'decay_constant_s_inv':lam}
    return result('Nuclear Physics Calculator', f'Ran nuclear physics mode: {mode}.', values, warnings, graphs, ['Apply decay/binding/dose formula', 'Return educational values', 'Block operational nuclear or weapons guidance'], 'python/numpy')


def particle_physics_calculator(inputs):
    mode=inputs.get('mode') or 'relativistic_energy_momentum'
    kv=parse_kv(inputs.get('inputs') or 'mass_mev_c2=0.511;kinetic_energy_mev=1;momentum_mev_c=1;luminosity_cm2_s=1e34;cross_section_pb=1;time_s=3600')
    graphs=[]; warnings=['Educational high-energy/particle physics only. Does not provide detector construction, beamline operation, hazardous radiation procedures, or weapons-related guidance.']
    if mode == 'relativistic_energy_momentum':
        m=float(kv.get('mass_mev_c2',0.511)); p=float(kv.get('momentum_mev_c',1)); total=math.sqrt((p)**2 + m**2); kinetic=total-m; beta=p/total if total else None; gamma=total/m if m else None
        values={'total_energy_mev':total,'kinetic_energy_mev':kinetic,'beta_v_over_c':beta,'gamma':gamma,'rest_energy_mev':m}
        ps=np.linspace(0, max(p*3, 5*m, 1), 240); es=np.sqrt(ps**2+m**2)
        graphs.append(_curve(ps, es, 'Relativistic energy-momentum relation', 'p (MeV/c)', 'E (MeV)'))
    elif mode == 'event_rate':
        L=float(kv.get('luminosity_cm2_s',1e34)); sigma_pb=float(kv.get('cross_section_pb',1)); time=float(kv.get('time_s',3600)); sigma_cm2=sigma_pb*1e-36; rate=L*sigma_cm2
        values={'event_rate_per_s':rate,'expected_events':rate*time,'cross_section_cm2':sigma_cm2,'integrated_luminosity_cm2':L*time}
        graphs.append(_bars(['rate/s','events'], [rate,rate*time], 'Particle event-rate estimate'))
    elif mode == 'uncertainty_resolution':
        sigma=float(kv.get('sigma',0.05)); energy=float(kv.get('energy_mev',100)); fwhm=2.35482*sigma; values={'sigma_resolution':sigma,'fwhm_resolution':fwhm,'relative_resolution':fwhm/energy if energy else None}
        xs=np.linspace(-5*sigma, 5*sigma, 240); ys=np.exp(-0.5*(xs/sigma)**2); graphs.append(_curve(xs, ys, 'Gaussian detector-resolution proxy', 'measurement error', 'relative likelihood'))
    else:
        tau=float(kv.get('lifetime_s',1e-10)); width=HBAR_EV_S/tau if tau else None; values={'decay_width_ev':width,'lifetime_s':tau}
    return result('Particle Physics Calculator', f'Ran particle physics mode: {mode}.', values, warnings, graphs, ['Use relativistic/unit formulas', 'Estimate rates/resolution/lifetime', 'Keep outputs educational and non-operational'], 'python/numpy')


def neurophysics_calculator(inputs):
    mode=inputs.get('mode') or 'membrane_rc'
    kv=parse_kv(inputs.get('inputs') or 'resistance_mohm=100;capacitance_pf=100;temperature_c=37;z=1;outside_mm=145;inside_mm=15')
    graphs=[]; warnings=['Educational neurophysics/biophysics only. Not clinical diagnosis, treatment planning, stimulation prescription, or medical-device guidance.']
    if mode == 'membrane_rc':
        R=float(kv.get('resistance_mohm',100))*1e6; Cc=float(kv.get('capacitance_pf',100))*1e-12; tau=R*Cc; Vinf=float(kv.get('v_inf_mv',-55)); V0=float(kv.get('v0_mv',-70)); t=np.linspace(0,5*tau if tau>0 else .05,240); V=Vinf+(V0-Vinf)*np.exp(-t/tau) if tau else np.ones_like(t)*V0
        values={'time_constant_s':tau,'time_constant_ms':tau*1000,'final_voltage_mv':Vinf}; graphs.append(_curve(t*1000,V,'Membrane RC charging curve','time (ms)','membrane voltage (mV)'))
    elif mode == 'nernst_potential':
        T=float(kv.get('temperature_c',37))+273.15; z=float(kv.get('z',1)); outside=float(kv.get('outside_mm',145)); inside=float(kv.get('inside_mm',15)); E=(R_GAS*T/(z*96485.33212))*math.log(outside/inside) if z and inside>0 and outside>0 else None
        values={'nernst_potential_v':E,'nernst_potential_mv':E*1000 if E is not None else None,'temperature_k':T}
        graphs.append(_bars(['inside mM','outside mM','E mV'], [inside,outside,E*1000 if E is not None else 0], 'Nernst potential summary'))
    elif mode == 'integrate_and_fire':
        tau_ms=float(kv.get('tau_ms',20)); v_rest=float(kv.get('v_rest_mv',-70)); v_thresh=float(kv.get('v_thresh_mv',-55)); current=float(kv.get('input_current_proxy',20)); t=np.linspace(0,100,400); V=v_rest+current*(1-np.exp(-t/tau_ms)); spike_time=float(t[np.argmax(V>=v_thresh)]) if np.any(V>=v_thresh) else None
        values={'threshold_crossing_ms':spike_time,'peak_proxy_mv':float(V[-1]),'threshold_mv':v_thresh}; graphs.append(_curve(t,V,'Integrate-and-fire membrane proxy','time (ms)','voltage proxy (mV)'))
    else:
        distance=float(kv.get('distance_m',1)); velocity=float(kv.get('conduction_velocity_m_s',50)); values={'conduction_delay_s':distance/velocity if velocity else None,'conduction_delay_ms':1000*distance/velocity if velocity else None}
    return result('Neurophysics Calculator', f'Ran neurophysics mode: {mode}.', values, warnings, graphs, ['Apply membrane/electrochemical proxy', 'Return graph and safety caveat'], 'python/numpy')


def rocket_science_calculator(inputs):
    mode=inputs.get('mode') or 'delta_v'
    kv=parse_kv(inputs.get('inputs') or 'isp_s=300;initial_mass_kg=1000;final_mass_kg=500;thrust_n=15000;planet_mass_kg=5.972e24;radius_m=6.371e6')
    graphs=[]; warnings=['Educational aerospace/orbital mechanics only. Not launch approval, weapons guidance, targeting, propulsion fabrication, or safety certification.']
    if mode == 'delta_v':
        isp=float(kv.get('isp_s',300)); m0=float(kv.get('initial_mass_kg',1000)); mf=float(kv.get('final_mass_kg',500)); dv=isp*G0*math.log(m0/mf) if isp>0 and m0>mf>0 else None
        vals=[]; ratios=np.linspace(1.01,max(5,m0/mf if mf else 2),200); dvs=isp*G0*np.log(ratios)
        values={'delta_v_m_s':dv,'mass_ratio':m0/mf if mf else None,'isp_s':isp}; graphs.append(_curve(ratios,dvs,'Tsiolkovsky delta-v by mass ratio','mass ratio m0/mf','delta-v (m/s)'))
    elif mode == 'thrust_to_weight':
        thrust=float(kv.get('thrust_n',15000)); mass=float(kv.get('initial_mass_kg',1000)); g=float(kv.get('gravity',G0)); tw=thrust/(mass*g) if mass*g else None
        values={'thrust_to_weight':tw,'liftoff_possible_idealized':bool(tw and tw>1),'weight_n':mass*g}
        graphs.append(_bars(['thrust','weight','T/W'], [thrust,mass*g,tw or 0], 'Thrust-to-weight summary'))
    elif mode == 'orbital_velocity':
        mu=6.67430e-11*float(kv.get('planet_mass_kg',5.972e24)); r=float(kv.get('radius_m',6.371e6))+float(kv.get('altitude_m',400000)); v=math.sqrt(mu/r) if r>0 else None; period=2*math.pi*math.sqrt(r**3/mu) if mu>0 and r>0 else None
        values={'circular_orbital_velocity_m_s':v,'orbital_period_s':period,'orbital_period_min':period/60 if period else None}
        graphs.append(_bars(['velocity km/s','period min'], [(v or 0)/1000,(period or 0)/60], 'Circular orbit summary'))
    else:
        dv_req=float(kv.get('delta_v_m_s',9400)); isp=float(kv.get('isp_s',300)); ratio=math.exp(dv_req/(isp*G0)) if isp>0 else None; values={'required_mass_ratio':ratio,'delta_v_m_s':dv_req,'isp_s':isp}
    return result('Rocket Science Calculator', f'Ran aerospace/rocket mode: {mode}.', values, warnings, graphs, ['Apply orbital/aerospace relationship', 'Return educational design-space estimate', 'Avoid operational launch or weaponization advice'], 'python/numpy')


def electronics_engineering_calculator(inputs):
    mode=inputs.get('mode') or 'ohms_law_power'
    kv=parse_kv(inputs.get('inputs') or 'voltage=12;resistance=100;capacitance_f=1e-6;frequency_hz=1000;inductance_h=0.01')
    graphs=[]; warnings=['Educational electronics analysis only. Not safety certification, mains wiring guidance, medical-device design, or hazardous construction advice.']
    if mode == 'ohms_law_power':
        V=float(kv.get('voltage',12)); R=float(kv.get('resistance',100)); I=V/R if R else None; P=V*I if I is not None else None
        values={'current_a':I,'power_w':P,'voltage_v':V,'resistance_ohm':R}; graphs.append(_bars(['V','I','P','R/100'], [V,I or 0,P or 0,R/100], 'Ohm/power summary'))
    elif mode == 'rc_filter':
        R=float(kv.get('resistance',1000)); Cc=float(kv.get('capacitance_f',1e-6)); fc=1/(2*math.pi*R*Cc) if R*Cc else None; f=np.logspace(0,6,300); mag=1/np.sqrt(1+(f/(fc or 1))**2)
        values={'cutoff_frequency_hz':fc,'time_constant_s':R*Cc}; graphs.append(_curve(f,20*np.log10(mag),'RC low-pass magnitude response','frequency (Hz)','gain (dB)'))
    elif mode == 'rlc_resonance':
        L=float(kv.get('inductance_h',0.01)); Cc=float(kv.get('capacitance_f',1e-6)); R=float(kv.get('resistance',10)); f0=1/(2*math.pi*math.sqrt(L*Cc)) if L*Cc else None; Q=(1/R)*math.sqrt(L/Cc) if R and Cc else None
        values={'resonant_frequency_hz':f0,'quality_factor_proxy':Q}; graphs.append(_bars(['f0 Hz','Q'], [f0 or 0,Q or 0], 'RLC resonance summary'))
    elif mode == 'op_amp_gain':
        rf=float(kv.get('feedback_resistance',10000)); rin=float(kv.get('input_resistance',1000)); values={'inverting_gain':-rf/rin if rin else None,'non_inverting_gain':1+rf/rin if rin else None}
    else:
        bits=float(kv.get('bits',12)); vref=float(kv.get('vref',3.3)); values={'adc_levels':2**bits,'lsb_volts':vref/(2**bits),'dynamic_range_db':6.02*bits+1.76}
    return result('Electronics Engineering Calculator', f'Ran electronics mode: {mode}.', values, warnings, graphs, ['Compute circuit relationship', 'Return graph where relevant'], 'python/numpy')


def rf_antenna_calculator(inputs):
    mode=inputs.get('mode') or 'wavelength_frequency'
    kv=parse_kv(inputs.get('inputs') or 'frequency_hz=915e6;distance_km=1;tx_power_dbm=20;tx_gain_dbi=2;rx_gain_dbi=2;losses_db=2')
    graphs=[]; warnings=['Educational RF/antenna analysis only. Does not support jamming, interception, unauthorized transmission, or regulatory bypass. Check local RF law and licensing.']
    if mode == 'wavelength_frequency':
        f=float(kv.get('frequency_hz',915e6)); wavelength=C/f if f else None; values={'wavelength_m':wavelength,'quarter_wave_m':wavelength/4 if wavelength else None,'half_wave_m':wavelength/2 if wavelength else None}
        graphs.append(_bars(['lambda','quarter','half'], [wavelength or 0,(wavelength or 0)/4,(wavelength or 0)/2], 'RF wavelength dimensions'))
    elif mode == 'free_space_path_loss':
        f_mhz=float(kv.get('frequency_mhz', float(kv.get('frequency_hz',915e6))/1e6)); d_km=float(kv.get('distance_km',1)); fspl=32.44+20*math.log10(d_km)+20*math.log10(f_mhz) if d_km>0 and f_mhz>0 else None
        values={'fspl_db':fspl,'frequency_mhz':f_mhz,'distance_km':d_km}; ds=np.logspace(-2,2,250); ys=32.44+20*np.log10(ds)+20*np.log10(f_mhz); graphs.append(_curve(ds,ys,'Free-space path loss vs distance','distance (km)','FSPL (dB)'))
    elif mode == 'link_budget':
        p=float(kv.get('tx_power_dbm',20)); gt=float(kv.get('tx_gain_dbi',2)); gr=float(kv.get('rx_gain_dbi',2)); losses=float(kv.get('losses_db',2)); f_mhz=float(kv.get('frequency_mhz', float(kv.get('frequency_hz',915e6))/1e6)); d_km=float(kv.get('distance_km',1)); fspl=32.44+20*math.log10(d_km)+20*math.log10(f_mhz); pr=p+gt+gr-losses-fspl
        values={'received_power_dbm':pr,'fspl_db':fspl,'eirp_dbm':p+gt,'link_terms_db':{'tx_power':p,'tx_gain':gt,'rx_gain':gr,'losses':losses,'fspl':fspl}}; graphs.append(_bars(['Tx','Gt','Gr','loss','FSPL','Pr'], [p,gt,gr,-losses,-fspl,pr], 'RF link budget terms'))
    else:
        gain=float(kv.get('gain_dbi',2.15)); efficiency=float(kv.get('efficiency',0.8)); values={'linear_gain':10**(gain/10),'effective_gain_with_efficiency':10**(gain/10)*efficiency}
    return result('RF and Antenna Calculator', f'Ran RF/antenna mode: {mode}.', values, warnings, graphs, ['Apply RF formula', 'Return educational antenna/link estimate', 'Warn about legal/regulatory constraints'], 'python/numpy')


def full_stack_engineering_tool(inputs):
    mode=inputs.get('mode') or 'fmea_risk'
    kv=parse_kv(inputs.get('inputs') or 'severity=4;occurrence=3;detection=2;load=1000;capacity=2500;mtbf_hours=10000;time_hours=1000')
    graphs=[]; warnings=['Engineering risk tool for analysis and prioritization only. It does not certify designs, structures, circuits, aircraft, vessels, medical devices, or life-safety systems.']
    if mode == 'fmea_risk':
        sev=float(kv.get('severity',4)); occ=float(kv.get('occurrence',3)); det=float(kv.get('detection',2)); rpn=sev*occ*det
        values={'risk_priority_number':rpn,'severity':sev,'occurrence':occ,'detection':det}; graphs.append(_bars(['severity','occurrence','detection','RPN'], [sev,occ,det,rpn], 'FMEA risk profile'))
    elif mode == 'factor_of_safety':
        load=float(kv.get('load',1000)); cap=float(kv.get('capacity',2500)); fos=cap/load if load else None
        values={'factor_of_safety':fos,'capacity':cap,'load':load,'margin':cap-load}; graphs.append(_bars(['load','capacity','margin','FoS'], [load,cap,cap-load,fos or 0], 'Safety margin summary'))
    elif mode == 'reliability':
        mtbf=float(kv.get('mtbf_hours',10000)); t=float(kv.get('time_hours',1000)); R=math.exp(-t/mtbf) if mtbf>0 else None; xs=np.linspace(0,max(t*3,mtbf),240); ys=np.exp(-xs/mtbf) if mtbf>0 else np.zeros_like(xs)
        values={'survival_probability':R,'failure_probability':1-R if R is not None else None,'mtbf_hours':mtbf}; graphs.append(_curve(xs,ys,'Exponential reliability curve','time (hours)','survival probability'))
    else:
        scores={'requirements':float(kv.get('requirements',3)),'verification':float(kv.get('verification',3)),'hazards':float(kv.get('hazards',4)),'interfaces':float(kv.get('interfaces',3)),'maintenance':float(kv.get('maintenance',2)),'governance':float(kv.get('governance',4))}
        values={'systems_engineering_maturity_proxy':float(np.mean(list(scores.values()))),'dimension_scores':scores}; graphs.append(_bars(list(scores.keys()), list(scores.values()), 'Engineering system maturity proxy'))
    return result('Full-Stack Engineering Tool', f'Ran engineering stack mode: {mode}.', values, warnings, graphs, ['Select engineering layer', 'Compute margin/risk/reliability proxy', 'Return professional-review warnings'], 'python/numpy')


def lab_science_calculator(inputs):
    mode=inputs.get('mode') or 'serial_dilution'
    kv=parse_kv(inputs.get('inputs') or 'c1=1.0;v1_ml=1.0;v2_ml=10;od=0.8;dilution_factor=100;colony_count=80;plated_ml=0.1')
    graphs=[]; warnings=['Lab-science educational calculator only. Follow institutional protocols, biosafety rules, clinical-lab standards, and qualified supervision.']
    if mode == 'serial_dilution':
        c1=float(kv.get('c1',1.0)); v1=float(kv.get('v1_ml',1.0)); v2=float(kv.get('v2_ml',10)); c2=c1*v1/v2 if v2 else None
        values={'final_concentration':c2,'dilution_factor':v2/v1 if v1 else None}; graphs.append(_bars(['C1','V1','V2','C2'], [c1,v1,v2,c2 or 0], 'Dilution summary'))
    elif mode == 'cfu_count':
        colonies=float(kv.get('colony_count',80)); df=float(kv.get('dilution_factor',100)); plated=float(kv.get('plated_ml',0.1)); cfu=colonies*df/plated if plated else None
        values={'cfu_per_ml':cfu,'colony_count':colonies,'dilution_factor':df}; graphs.append(_bars(['colonies','dilution','CFU/ml'], [colonies,df,cfu or 0], 'CFU estimate'))
    elif mode == 'qpcr_efficiency':
        slope=float(kv.get('slope',-3.32)); eff=10**(-1/slope)-1 if slope else None
        values={'pcr_efficiency_fraction':eff,'pcr_efficiency_percent':eff*100 if eff is not None else None,'slope':slope}; graphs.append(_bars(['slope abs','eff %'], [abs(slope),eff*100 if eff is not None else 0], 'qPCR efficiency'))
    elif mode == 'dose_response_research':
        ec50=float(kv.get('ec50',1.0)); hill=float(kv.get('hill',1.0)); top=float(kv.get('top',100)); bottom=float(kv.get('bottom',0)); x=np.logspace(-3,3,300); y=bottom+(top-bottom)/(1+(ec50/x)**hill)
        values={'ec50':ec50,'hill_slope':hill,'top':top,'bottom':bottom}; graphs.append(_curve(x,y,'Dose-response research curve','dose','response'))
    else:
        data=parse_number_list(kv.get('replicates',[1.0,1.1,0.95,1.05])); arr=np.array(data,dtype=float); values={'mean':float(np.mean(arr)),'sd':float(np.std(arr,ddof=1)) if len(arr)>1 else 0,'coefficient_of_variation_percent':float(np.std(arr,ddof=1)/np.mean(arr)*100) if len(arr)>1 and np.mean(arr) else None}; graphs.append(_bars([f'r{i+1}' for i in range(len(arr))], arr.tolist(), 'Lab replicate values'))
    return result('Lab Science Calculator', f'Ran lab-science mode: {mode}.', values, warnings, graphs, ['Apply lab math formula', 'Return QA/QC interpretation', 'Warn about biosafety/protocol limits'], 'python/numpy')


def clinical_research_calculator(inputs):
    mode=inputs.get('mode') or 'diagnostic_metrics'
    kv=parse_kv(inputs.get('inputs') or 'tp=80;fp=10;tn=900;fn=20;event_rate_control=0.2;event_rate_treatment=0.12')
    graphs=[]; warnings=['Educational clinical/public-health research analytics only. Not diagnosis, triage, treatment, prescription, or medical advice.']
    if mode == 'diagnostic_metrics':
        tp=float(kv.get('tp',80)); fp=float(kv.get('fp',10)); tn=float(kv.get('tn',900)); fn=float(kv.get('fn',20)); sens=tp/(tp+fn) if tp+fn else None; spec=tn/(tn+fp) if tn+fp else None; ppv=tp/(tp+fp) if tp+fp else None; npv=tn/(tn+fn) if tn+fn else None
        values={'sensitivity':sens,'specificity':spec,'ppv':ppv,'npv':npv,'accuracy':(tp+tn)/(tp+fp+tn+fn) if tp+fp+tn+fn else None}; graphs.append(_bars(['sens','spec','PPV','NPV','acc'], [sens or 0,spec or 0,ppv or 0,npv or 0,values['accuracy'] or 0], 'Diagnostic metrics'))
    elif mode == 'nnt':
        cer=float(kv.get('event_rate_control',0.2)); ter=float(kv.get('event_rate_treatment',0.12)); arr=cer-ter; values={'absolute_risk_reduction':arr,'relative_risk':ter/cer if cer else None,'nnt':1/arr if arr>0 else None}
        graphs.append(_bars(['CER','TER','ARR','NNT/10'], [cer,ter,arr,(values['nnt'] or 0)/10], 'Treatment effect research metrics'))
    elif mode == 'odds_ratio':
        a=float(kv.get('a',40)); b=float(kv.get('b',60)); c=float(kv.get('c',20)); d=float(kv.get('d',80)); values={'odds_ratio':(a*d)/(b*c) if b*c else None,'risk_exposed':a/(a+b) if a+b else None,'risk_unexposed':c/(c+d) if c+d else None}
    else:
        mean1=float(kv.get('mean1',10)); mean2=float(kv.get('mean2',8)); sd1=float(kv.get('sd1',2)); sd2=float(kv.get('sd2',2)); n1=float(kv.get('n1',30)); n2=float(kv.get('n2',30)); pooled=math.sqrt(((n1-1)*sd1**2+(n2-1)*sd2**2)/(n1+n2-2)) if n1+n2>2 else None; d=(mean1-mean2)/pooled if pooled else None; values={'cohens_d':d,'pooled_sd':pooled}
    return result('Clinical Research Calculator', f'Ran clinical research mode: {mode}.', values, warnings, graphs, ['Compute clinical/public-health research metric', 'Return non-diagnostic caveat'], 'python/numpy')
