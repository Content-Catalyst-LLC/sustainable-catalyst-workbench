
from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, result, svg_from_figure, bar_graph

C=299_792_458.0
G=6.67430e-11
SIGMA=5.670374419e-8


def _curve(x,y,title,xlabel='x',ylabel='value'):
    fig, ax=plt.subplots(figsize=(8.5,4.9)); ax.plot(x,y,linewidth=2); ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.grid(alpha=.28)
    svg=svg_from_figure(fig); plt.close(fig)
    return {'title':title,'type':'professional_svg_curve','svg':svg,'export_formats':['svg','png','pdf_report']}


def fpga_digital_systems_tool(inputs):
    mode=str(inputs.get('mode') or 'timing_slack')
    kv=parse_kv(inputs.get('inputs') or 'clock_mhz=100;critical_path_ns=7.5;lut_count=20000;bram_kb=1024;dsp_blocks=80;word_bits=16;pipeline_stages=4')
    warnings=['Educational FPGA/digital-systems estimation only. Validate with vendor synthesis, timing analysis, constraints, CDC tools, and hardware testing.']
    graphs=[]
    if mode=='timing_slack':
        clock=float(kv.get('clock_mhz',100)); path=float(kv.get('critical_path_ns',7.5)); period=1000/clock if clock else 0; slack=period-path; fmax=1000/path if path else None
        values={'clock_period_ns':period,'critical_path_ns':path,'timing_slack_ns':slack,'estimated_fmax_mhz':fmax}
        graphs.append(bar_graph(['period ns','path ns','slack ns'], [period,path,slack], 'FPGA timing summary'))
    elif mode=='fixed_point':
        bits=int(float(kv.get('word_bits',16))); frac=int(float(kv.get('fraction_bits',8))); intbits=bits-frac-1; maxv=(2**intbits)-2**(-frac); minv=-(2**intbits); step=2**(-frac)
        values={'word_bits':bits,'fraction_bits':frac,'min_value':minv,'max_value':maxv,'quantization_step':step,'snr_db_proxy':6.02*bits+1.76}
    elif mode=='pipeline_throughput':
        f=float(kv.get('clock_mhz',100)); stages=int(float(kv.get('pipeline_stages',4))); initiation=float(kv.get('initiation_interval',1)); values={'latency_cycles':stages,'throughput_samples_per_s':f*1e6/max(initiation,1e-9),'initiation_interval':initiation}
    else:
        lut=float(kv.get('lut_count',20000)); bram=float(kv.get('bram_kb',1024)); dsp=float(kv.get('dsp_blocks',80)); risk=0.25*(lut/100000)+0.25*(bram/10000)+0.25*(dsp/1000)+0.25*float(kv.get('cdc_complexity',3))/5
        values={'resource_pressure_proxy':risk,'lut_count':lut,'bram_kb':bram,'dsp_blocks':dsp}; graphs.append(bar_graph(['LUT','BRAM KB','DSP','risk x100'], [lut,bram,dsp,risk*100], 'FPGA resource and CDC pressure'))
    return result('FPGA and Digital Systems Tool', f'Ran FPGA mode: {mode}.', values, warnings, graphs, ['Compute timing/resource/fixed-point estimates', 'Return synthesis-validation caveats'], 'python/numpy')


def power_systems_engineering_tool(inputs):
    mode=str(inputs.get('mode') or 'three_phase_power')
    kv=parse_kv(inputs.get('inputs') or 'voltage_v=480;current_a=100;power_factor=0.85;length_m=100;resistance_ohm_per_km=0.2;reactance_ohm_per_km=0.08')
    warnings=['Educational power-systems estimation only. Not design certification, code compliance, protection-setting, or safety approval.']
    graphs=[]
    if mode=='three_phase_power':
        V=float(kv.get('voltage_v',480)); I=float(kv.get('current_a',100)); pf=float(kv.get('power_factor',0.85)); S=math.sqrt(3)*V*I; P=S*pf; Q=S*math.sqrt(max(0,1-pf*pf)); values={'apparent_power_va':S,'real_power_w':P,'reactive_power_var':Q,'power_factor':pf}; graphs.append(bar_graph(['kVA','kW','kVAr'], [S/1000,P/1000,Q/1000], 'Three-phase power'))
    elif mode=='voltage_drop':
        I=float(kv.get('current_a',100)); L=float(kv.get('length_m',100)); R=float(kv.get('resistance_ohm_per_km',0.2))*L/1000; X=float(kv.get('reactance_ohm_per_km',0.08))*L/1000; pf=float(kv.get('power_factor',0.85)); drop=math.sqrt(3)*I*(R*pf+X*math.sqrt(max(0,1-pf*pf))); values={'voltage_drop_v':drop,'percent_drop_at_voltage':100*drop/max(float(kv.get('voltage_v',480)),1e-9)}
    elif mode=='power_factor_correction':
        P=float(kv.get('real_power_kw',100)); pf1=float(kv.get('pf_initial',0.75)); pf2=float(kv.get('pf_target',0.95)); q1=P*math.tan(math.acos(pf1)); q2=P*math.tan(math.acos(pf2)); values={'capacitor_kvar_required_proxy':q1-q2,'initial_kvar':q1,'target_kvar':q2}
    else:
        V=float(kv.get('voltage_v',480)); Z=float(kv.get('source_impedance_ohm',0.05)); values={'fault_current_a_proxy':V/(math.sqrt(3)*Z) if Z else None,'source_impedance_ohm':Z}
    return result('Power Systems Engineering Tool', f'Ran power-systems mode: {mode}.', values, warnings, graphs, ['Compute electrical power relationship', 'Return code/safety caveats'], 'python/numpy')


def mechanical_systems_engineering_tool(inputs):
    mode=str(inputs.get('mode') or 'shaft_torsion')
    kv=parse_kv(inputs.get('inputs') or 'torque_nm=500;radius_m=0.025;polar_j_m4=6.14e-7;length_m=1;shear_modulus_pa=79e9;mass_kg=10;stiffness_n_m=10000')
    warnings=['Educational mechanical engineering estimates only. Professional design requires standards, safety factors, materials data, and review.']
    graphs=[]
    if mode=='shaft_torsion':
        T=float(kv.get('torque_nm',500)); r=float(kv.get('radius_m',0.025)); J=float(kv.get('polar_j_m4',6.14e-7)); L=float(kv.get('length_m',1)); Gm=float(kv.get('shear_modulus_pa',79e9)); tau=T*r/J if J else None; theta=T*L/(J*Gm) if J and Gm else None; values={'max_shear_stress_pa':tau,'angle_of_twist_rad':theta}
    elif mode=='vibration_frequency':
        m=float(kv.get('mass_kg',10)); k=float(kv.get('stiffness_n_m',10000)); wn=math.sqrt(k/m) if m else None; values={'natural_frequency_rad_s':wn,'natural_frequency_hz':wn/(2*math.pi) if wn else None}; t=np.linspace(0,2,250); graphs.append(_curve(t, np.sin((wn or 1)*t), 'Undamped vibration mode proxy', 'time (s)', 'relative displacement'))
    elif mode=='fatigue_proxy':
        alt=float(kv.get('alternating_stress_mpa',120)); mean=float(kv.get('mean_stress_mpa',60)); endurance=float(kv.get('endurance_limit_mpa',240)); ultimate=float(kv.get('ultimate_strength_mpa',500)); util=alt/endurance + mean/ultimate; values={'goodman_utilization_proxy':util,'margin_proxy':1-util}
    else:
        q=float(kv.get('heat_w',100)); L=float(kv.get('length_m',0.05)); k=float(kv.get('conductivity_w_mk',205)); A=float(kv.get('area_m2',0.01)); values={'temperature_difference_k_proxy':q*L/(k*A) if k and A else None}
    return result('Mechanical Systems Engineering Tool', f'Ran mechanical systems mode: {mode}.', values, warnings, graphs, ['Apply mechanical systems formula', 'Return professional-review caveat'], 'python/numpy')


def structural_engineering_tool(inputs):
    mode=str(inputs.get('mode') or 'beam_deflection')
    kv=parse_kv(inputs.get('inputs') or 'span_m=6;uniform_load_kn_m=10;E_pa=200e9;I_m4=8e-6;Fy_mpa=345;area_m2=0.01;K=1')
    warnings=['Educational structural calculations only. Not code compliance, construction approval, life-safety certification, or stamped engineering.']
    graphs=[]
    if mode=='beam_deflection':
        L=float(kv.get('span_m',6)); w=float(kv.get('uniform_load_kn_m',10))*1000; E=float(kv.get('E_pa',200e9)); I=float(kv.get('I_m4',8e-6)); M=w*L**2/8; V=w*L/2; delta=5*w*L**4/(384*E*I) if E and I else None; values={'max_moment_nm':M,'support_shear_n':V,'max_deflection_m':delta,'span_over_deflection':L/delta if delta else None}; xs=np.linspace(0,L,200); graphs.append(_curve(xs, w*xs*(L-xs)/2, 'Simply supported moment diagram proxy','x (m)','M (N m)'))
    elif mode=='column_buckling':
        E=float(kv.get('E_pa',200e9)); I=float(kv.get('I_m4',8e-6)); L=float(kv.get('span_m',6)); K=float(kv.get('K',1)); Pcr=math.pi**2*E*I/(K*L)**2 if K and L else None; values={'euler_buckling_load_n':Pcr,'effective_length_m':K*L}
    elif mode=='load_combination':
        D=float(kv.get('dead_load',100)); Ld=float(kv.get('live_load',75)); W=float(kv.get('wind_load',40)); Eeq=float(kv.get('seismic_load',30)); values={'combo_1_2D_1_6L':1.2*D+1.6*Ld,'combo_1_2D_1_0W_1_0L':1.2*D+W+Ld,'combo_1_2D_1_0E_1_0L':1.2*D+Eeq+Ld}
    else:
        Cs=float(kv.get('seismic_coefficient',0.12)); W=float(kv.get('seismic_weight_kn',5000)); values={'seismic_base_shear_kn_proxy':Cs*W,'seismic_coefficient':Cs}
    return result('Structural Engineering Tool', f'Ran structural mode: {mode}.', values, warnings, graphs, ['Compute structural proxy', 'Return safety/code caveats'], 'python/numpy')


def civil_infrastructure_planning_tool(inputs):
    mode=str(inputs.get('mode') or 'stormwater_storage')
    kv=parse_kv(inputs.get('inputs') or 'area_ha=2;rainfall_mm=50;runoff_coefficient=0.7;population=10000;daily_l_per_capita=180;capacity=12000;demand=9000')
    warnings=['Educational civil/infrastructure planning support only. Local design standards, permits, and licensed review are required.']
    graphs=[]
    if mode=='stormwater_storage':
        area=float(kv.get('area_ha',2))*10000; rain=float(kv.get('rainfall_mm',50))/1000; c=float(kv.get('runoff_coefficient',0.7)); values={'runoff_volume_m3':area*rain*c,'area_m2':area,'runoff_coefficient':c}
    elif mode=='water_demand':
        pop=float(kv.get('population',10000)); lpcd=float(kv.get('daily_l_per_capita',180)); values={'daily_demand_m3':pop*lpcd/1000,'annual_demand_m3':pop*lpcd*365/1000}
    elif mode=='capacity_utilization':
        demand=float(kv.get('demand',9000)); cap=float(kv.get('capacity',12000)); values={'utilization':demand/cap if cap else None,'remaining_capacity':cap-demand}
    else:
        condition=float(kv.get('condition_score',3)); criticality=float(kv.get('criticality',4)); exposure=float(kv.get('exposure',3)); risk=condition*criticality*exposure; values={'asset_risk_priority_number':risk,'condition_score':condition,'criticality':criticality,'exposure':exposure}; graphs.append(bar_graph(['condition','criticality','exposure','risk/10'], [condition,criticality,exposure,risk/10], 'Infrastructure risk profile'))
    return result('Civil Infrastructure Planning Tool', f'Ran civil infrastructure mode: {mode}.', values, warnings, graphs, ['Compute planning proxy', 'Flag local-code/professional requirements'], 'python/numpy')


def urban_planning_analytics_tool(inputs):
    mode=str(inputs.get('mode') or 'land_use_mix')
    kv=parse_kv(inputs.get('inputs') or 'population=50000;area_km2=12;jobs=25000;housing_units=22000;income=65000;housing_cost_monthly=1600;residential=0.45;commercial=0.25;industrial=0.1;civic=0.1;open_space=0.1')
    warnings=['Educational urban-planning analytics only. GIS, community engagement, zoning, equity, and local policy review are required.']
    graphs=[]
    if mode=='density_access':
        pop=float(kv.get('population',50000)); area=float(kv.get('area_km2',12)); jobs=float(kv.get('jobs',25000)); values={'population_density_per_km2':pop/area if area else None,'jobs_housing_ratio':jobs/max(float(kv.get('housing_units',22000)),1e-9)}
    elif mode=='housing_affordability':
        inc=float(kv.get('income',65000)); cost=float(kv.get('housing_cost_monthly',1600))*12; values={'housing_cost_burden':cost/inc if inc else None,'affordable_at_30_percent_income_annual':0.3*inc,'annual_housing_cost':cost}
    else:
        shares=np.array([float(kv.get(k,0)) for k in ['residential','commercial','industrial','civic','open_space']],dtype=float); shares=shares/max(np.sum(shares),1e-9); entropy=-float(np.sum([p*math.log(p) for p in shares if p>0]))/math.log(len(shares)); values={'land_use_entropy_0_1':entropy,'normalized_shares':shares.tolist()}; graphs.append(bar_graph(['res','comm','ind','civic','open'], shares.tolist(), 'Land-use mix'))
    return result('Urban Planning Analytics Tool', f'Ran urban planning mode: {mode}.', values, warnings, graphs, ['Compute urban indicator', 'Return equity/community/local planning caveat'], 'python/numpy')


def architecture_building_science_tool(inputs):
    mode=str(inputs.get('mode') or 'hvac_load_proxy')
    kv=parse_kv(inputs.get('inputs') or 'area_m2=1000;u_value=0.35;delta_t_k=20;window_area_m2=150;shgc=0.35;solar_w_m2=500;occupants=120;floor_area_m2=1000')
    warnings=['Educational architecture/building-science estimates only. Not code compliance, egress approval, energy-model certification, or professional design.']
    graphs=[]
    if mode=='hvac_load_proxy':
        A=float(kv.get('area_m2',1000)); U=float(kv.get('u_value',0.35)); dt=float(kv.get('delta_t_k',20)); win=float(kv.get('window_area_m2',150)); shgc=float(kv.get('shgc',0.35)); solar=float(kv.get('solar_w_m2',500)); conduction=A*U*dt; solar_gain=win*shgc*solar; values={'conduction_load_w':conduction,'solar_gain_w':solar_gain,'total_load_w_proxy':conduction+solar_gain}; graphs.append(bar_graph(['conduction','solar','total'], [conduction,solar_gain,conduction+solar_gain], 'Building load proxy'))
    elif mode=='egress_occupancy':
        occ=float(kv.get('occupants',120)); width=float(kv.get('exit_width_m',2.4)); values={'occupants':occ,'exit_width_per_person_m_proxy':width/max(occ,1e-9),'persons_per_meter_proxy':occ/max(width,1e-9)}
    elif mode=='daylight_proxy':
        win=float(kv.get('window_area_m2',150)); floor=float(kv.get('floor_area_m2',1000)); trans=float(kv.get('visible_transmittance',0.6)); values={'window_to_floor_ratio':win/floor if floor else None,'daylight_availability_proxy':win*trans/max(floor,1e-9)}
    else:
        materials=float(kv.get('materials_kgco2e',400000)); area=float(kv.get('floor_area_m2',1000)); values={'embodied_carbon_kgco2e_m2':materials/max(area,1e-9),'total_embodied_carbon_kgco2e':materials}
    return result('Architecture and Building Science Tool', f'Ran building science mode: {mode}.', values, warnings, graphs, ['Compute building-science proxy', 'Return local-code/professional caveat'], 'python/numpy')


def astrophysics_research_calculator(inputs):
    mode=str(inputs.get('mode') or 'blackbody')
    kv=parse_kv(inputs.get('inputs') or 'temperature_k=5778;radius_m=6.957e8;wavelength_nm=500;redshift=0.05;period_days=365.25;semi_major_axis_au=1')
    warnings=['Educational astrophysics/space-science calculator only. Ephemerides, mission planning, and observatory calibration require specialized validated tools.']
    graphs=[]
    if mode=='blackbody':
        T=float(kv.get('temperature_k',5778)); lam=np.linspace(100e-9,3000e-9,400); h=6.62607015e-34; k=1.380649e-23; c=299792458.0; B=(2*h*c**2)/(lam**5)/(np.exp(h*c/(lam*k*T))-1); values={'wien_peak_nm':2.897771955e-3/T*1e9,'temperature_k':T}; graphs.append(_curve(lam*1e9, B/np.max(B), 'Normalized blackbody spectrum','wavelength (nm)','relative radiance'))
    elif mode=='luminosity':
        R=float(kv.get('radius_m',6.957e8)); T=float(kv.get('temperature_k',5778)); values={'luminosity_w':4*math.pi*R**2*SIGMA*T**4,'solar_luminosity_ratio':4*math.pi*R**2*SIGMA*T**4/3.828e26}
    elif mode=='redshift_hubble':
        z=float(kv.get('redshift',0.05)); H0=float(kv.get('h0_km_s_mpc',70)); values={'recession_velocity_km_s_low_z':299792.458*z,'distance_mpc_low_z':299792.458*z/H0 if H0 else None}
    else:
        a=float(kv.get('semi_major_axis_au',1)); M=float(kv.get('central_mass_solar',1)); P_year=math.sqrt(a**3/M) if M else None; values={'orbital_period_years_kepler':P_year,'orbital_period_days':P_year*365.25 if P_year else None}
    return result('Astrophysics Research Calculator', f'Ran astrophysics mode: {mode}.', values, warnings, graphs, ['Apply astrophysical relationship', 'Return educational/research caveat'], 'python/numpy')
