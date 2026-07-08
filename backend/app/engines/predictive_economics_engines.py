
from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from .common import parse_kv, parse_number_list, result, svg_from_figure, bar_graph, parse_rows


def _curve(xs, ys, title, xlabel='index', ylabel='value'):
    fig, ax = plt.subplots(figsize=(8.5, 4.9))
    ax.plot(xs, ys, linewidth=2)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.grid(alpha=.28)
    svg = svg_from_figure(fig); plt.close(fig)
    return {'title': title, 'type': 'professional_svg_curve', 'svg': svg, 'export_formats': ['svg','png','pdf_report']}


def _actual_forecast_graph(y, forecast, title='Forecast with historical series'):
    y=np.asarray(y,dtype=float); f=np.asarray(forecast,dtype=float)
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    ax.plot(np.arange(len(y)), y, marker='o', linewidth=2, label='history')
    start=len(y)-1
    ax.plot(np.arange(start, start+len(f)+1), np.r_[y[-1], f], marker='o', linewidth=2, linestyle='--', label='forecast')
    ax.axvline(len(y)-1, linestyle=':', linewidth=1)
    ax.set_title(title); ax.set_xlabel('period'); ax.set_ylabel('value'); ax.legend(); ax.grid(alpha=.28)
    svg=svg_from_figure(fig); plt.close(fig)
    return {'title': title, 'type': 'forecast_svg', 'svg': svg, 'export_formats': ['svg','png','pdf_report']}


def _acf_values(y, max_lag=12):
    y=np.asarray(y,dtype=float)
    if len(y)<3 or np.std(y)==0: return [0.0]*max_lag
    out=[]; yc=y-np.mean(y)
    denom=float(np.dot(yc,yc))
    for lag in range(1,max_lag+1):
        if lag>=len(y): out.append(0.0)
        else: out.append(float(np.dot(yc[:-lag], yc[lag:]) / denom))
    return out


def predictive_analytics_forecasting_tool(inputs):
    y=np.array(parse_number_list(inputs.get('series') or '120,128,133,140,145,151,160,171,178,190,203,215'), dtype=float)
    mode=str(inputs.get('mode') or 'linear_trend')
    horizon=max(1, int(float(inputs.get('horizon') or 6)))
    alpha=float(inputs.get('alpha') or 0.35)
    warnings=['Forecasts are scenario-support tools, not guarantees. Validate with holdout data, domain knowledge, and uncertainty review.']
    graphs=[]
    if len(y)<3:
        y=np.array([1,2,3], dtype=float); warnings.append('Too few observations supplied; used minimal fallback series.')
    x=np.arange(len(y), dtype=float)
    if mode == 'moving_average':
        window=max(2, int(float(inputs.get('window') or min(4, len(y)))))
        level=float(np.mean(y[-window:]))
        forecast=np.ones(horizon)*level
        fitted=np.r_[np.full(window-1, np.nan), [np.mean(y[i-window+1:i+1]) for i in range(window-1,len(y))]]
        method=['Compute trailing moving average', 'Project latest smoothed level', 'Return forecast and holdout-style diagnostics']
    elif mode == 'exponential_smoothing':
        s=float(y[0]); fitted=[]
        for val in y:
            fitted.append(s); s=alpha*float(val)+(1-alpha)*s
        forecast=np.ones(horizon)*s
        fitted=np.array(fitted)
        method=['Iteratively update level with exponential smoothing', 'Forecast future periods from final level']
    else:
        b1,b0=np.polyfit(x, y, 1)
        future=np.arange(len(y), len(y)+horizon, dtype=float)
        forecast=b0+b1*future
        fitted=b0+b1*x
        method=['Fit least-squares linear trend', 'Project horizon periods ahead', 'Report residual and uncertainty proxies']
    resid=y-np.asarray(fitted,dtype=float)
    resid=resid[np.isfinite(resid)]
    rmse=float(np.sqrt(np.mean(resid**2))) if len(resid) else 0.0
    mae=float(np.mean(np.abs(resid))) if len(resid) else 0.0
    mape=float(np.mean(np.abs(resid / np.maximum(np.abs(y[-len(resid):]), 1e-9))) * 100) if len(resid) else 0.0
    lower=forecast-1.96*rmse; upper=forecast+1.96*rmse
    graphs.append(_actual_forecast_graph(y, forecast, 'Predictive analytics forecast'))
    graphs.append(bar_graph([f't+{i+1}' for i in range(horizon)], forecast.tolist(), 'Forecast values', 'forecast'))
    return result('Predictive Analytics Forecasting Tool', f'Generated a {mode} forecast for {horizon} future periods.', {
        'mode': mode, 'horizon': horizon, 'forecast': forecast.tolist(), 'lower_95_proxy': lower.tolist(), 'upper_95_proxy': upper.tolist(),
        'rmse_proxy': rmse, 'mae_proxy': mae, 'mape_percent_proxy': mape
    }, warnings, graphs, method, 'python/numpy', ['Use this for exploratory forecasting and decision support. Add external drivers, validation, and domain-specific causal review before relying on outputs.'])


def time_series_diagnostics_tool(inputs):
    y=np.array(parse_number_list(inputs.get('series') or '10,11,13,12,15,18,17,21,24,23,26,30'), dtype=float)
    max_lag=max(1, int(float(inputs.get('max_lag') or min(8, len(y)-1)))) if len(y)>1 else 1
    warnings=[]
    if len(y)<5: warnings.append('Short series: diagnostics are unstable.')
    x=np.arange(len(y), dtype=float)
    slope=float(np.polyfit(x,y,1)[0]) if len(y)>1 else 0.0
    acf=_acf_values(y, max_lag)
    dif=np.diff(y) if len(y)>1 else np.array([0])
    rolling_window=max(2, min(5, len(y)))
    roll=np.array([np.mean(y[max(0,i-rolling_window+1):i+1]) for i in range(len(y))])
    z=(y-np.mean(y))/(np.std(y,ddof=1) if len(y)>1 and np.std(y,ddof=1)>0 else 1)
    anomalies=[int(i) for i,v in enumerate(z) if abs(v)>2.5]
    graphs=[_curve(x,y,'Time-series level','period','value'), _curve(x,roll,'Rolling mean','period','mean'), bar_graph([f'lag {i}' for i in range(1,max_lag+1)], acf[:max_lag], 'Autocorrelation profile', 'ACF')]
    return result('Time-Series Diagnostics Tool', 'Computed trend, volatility, autocorrelation, rolling mean, and anomaly diagnostics.', {
        'n': int(len(y)), 'trend_slope_per_period': slope, 'mean': float(np.mean(y)), 'std': float(np.std(y,ddof=1)) if len(y)>1 else 0.0,
        'mean_absolute_change': float(np.mean(np.abs(dif))) if len(dif) else 0.0, 'lag_autocorrelations': acf[:max_lag], 'anomaly_indices_z_gt_2_5': anomalies,
        'stationarity_warning_proxy': bool(abs(slope) > (np.std(dif) if len(dif)>1 else 0.0))
    }, warnings, graphs, ['Fit trend proxy', 'Compute rolling mean and first differences', 'Estimate autocorrelation and anomalies'], 'python/numpy')


def economics_forecasting_scenario_tool(inputs):
    mode=str(inputs.get('mode') or 'macro_scenario')
    kv=parse_kv(inputs.get('inputs') or 'gdp_growth=0.02;inflation=0.03;unemployment=0.05;policy_rate=0.04;demand=1000;price=10;elasticity=-1.2;shock=-0.1;multiplier=1.5')
    graphs=[]; warnings=['Economic forecasts are scenario tools, not investment, legal, tax, or policy advice. Validate assumptions and distributional impacts.']
    if mode == 'macro_scenario':
        years=np.arange(0, 6); base=100*np.cumprod(np.ones_like(years,dtype=float)*(1+float(kv.get('gdp_growth',0.02))))
        inflation=float(kv.get('inflation',0.03)); unemployment=float(kv.get('unemployment',0.05)); policy=float(kv.get('policy_rate',0.04))
        stress=100*(1+0.4*inflation+0.8*unemployment+0.2*policy)
        values={'gdp_index_path':base.tolist(),'macro_stress_proxy':stress,'inflation':inflation,'unemployment':unemployment,'policy_rate':policy}
        graphs.append(_curve(years, base, 'GDP index scenario', 'year', 'index'))
    elif mode == 'demand_forecast':
        q0=float(kv.get('demand',1000)); p0=float(kv.get('price',10)); e=float(kv.get('elasticity',-1.2)); shock=float(kv.get('shock',-0.1)); p1=p0*(1+shock); q1=q0*((p1/p0)**e) if p0>0 and p1>0 else q0
        prices=np.linspace(max(.01,p0*.5), p0*1.5, 120); qs=q0*((prices/p0)**e)
        values={'baseline_quantity':q0,'new_price':p1,'forecast_quantity':q1,'price_elasticity':e,'quantity_change_percent':(q1/q0-1)*100 if q0 else None}
        graphs.append(_curve(prices, qs, 'Demand curve scenario', 'price', 'quantity'))
    elif mode == 'fiscal_multiplier':
        shock=float(kv.get('spending_shock',100)); mult=float(kv.get('multiplier',1.5)); leakage=float(kv.get('leakage_rate',0.2)); impact=shock*mult*(1-leakage)
        values={'spending_shock':shock,'multiplier':mult,'leakage_rate':leakage,'output_impact_proxy':impact}; graphs.append(bar_graph(['shock','gross impact','net impact'], [shock, shock*mult, impact], 'Fiscal multiplier scenario'))
    else:
        benefits=np.array(kv.get('benefits',[300,350,400,450]), dtype=float); costs=np.array(kv.get('costs',[200,225,250,275]), dtype=float); r=float(kv.get('discount_rate',0.05)); t=np.arange(len(benefits)); npv=float(np.sum((benefits-costs)/((1+r)**t)))
        values={'npv':npv,'benefit_cost_ratio':float(np.sum(benefits/((1+r)**t))/max(np.sum(costs/((1+r)**t)),1e-9)),'discount_rate':r}; graphs.append(bar_graph([f'y{i}' for i in range(len(benefits))], (benefits-costs).tolist(), 'Net benefit stream'))
    return result('Economics Forecasting and Scenario Tool', f'Ran economics scenario mode: {mode}.', values, warnings, graphs, ['Parse economic assumptions', 'Run scenario formula', 'Return distributional/professional caveats'], 'python/numpy + optional R')


def econometrics_policy_model_tool(inputs):
    mode=str(inputs.get('mode') or 'ols')
    warnings=['Econometric outputs depend on identification assumptions. This is analytical support, not proof of causality or policy advice.']
    graphs=[]
    if mode == 'difference_in_differences':
        kv=parse_kv(inputs.get('inputs') or 'pre_treated=10;post_treated=16;pre_control=9;post_control=11')
        did=(float(kv.get('post_treated',16))-float(kv.get('pre_treated',10)))-(float(kv.get('post_control',11))-float(kv.get('pre_control',9)))
        values={'difference_in_differences_effect':did,'treated_change':float(kv.get('post_treated',16))-float(kv.get('pre_treated',10)),'control_change':float(kv.get('post_control',11))-float(kv.get('pre_control',9))}
        graphs.append(bar_graph(['treated change','control change','DiD'], [values['treated_change'],values['control_change'],did], 'Difference-in-differences decomposition'))
    elif mode == 'elasticity_regression':
        x=np.array(parse_number_list(inputs.get('x') or '10,11,12,13,14,15'), dtype=float); y=np.array(parse_number_list(inputs.get('y') or '100,94,90,82,78,73'), dtype=float)
        lx=np.log(np.maximum(x,1e-9)); ly=np.log(np.maximum(y,1e-9)); beta,alpha=np.polyfit(lx,ly,1); pred=np.exp(alpha+beta*lx); residuals=y-pred
        values={'elasticity_coefficient':float(beta),'intercept_log':float(alpha),'rmse':float(np.sqrt(np.mean(residuals**2)))}
        graphs.append(_actual_forecast_graph(y, pred, 'Elasticity regression fitted values'))
    else:
        rows=parse_rows(inputs.get('data') or '1,2\n2,4\n3,5\n4,7\n5,8')
        if rows.ndim==2 and rows.shape[1]>=2:
            X=rows[:,:-1]; y=rows[:,-1]
            X1=np.c_[np.ones(len(X)), X]
            coef=np.linalg.pinv(X1)@y
            pred=X1@coef; resid=y-pred
            r2=1-float(np.sum(resid**2))/max(float(np.sum((y-np.mean(y))**2)),1e-12)
            values={'coefficients':[float(c) for c in coef], 'r_squared':r2, 'rmse':float(np.sqrt(np.mean(resid**2))), 'n':int(len(y))}
            graphs.append(_actual_forecast_graph(y, pred, 'OLS fitted values'))
        else:
            values={'error':'Provide rows of predictors followed by outcome.'}
    return result('Econometrics and Policy Model Tool', f'Ran econometric mode: {mode}.', values, warnings, graphs, ['Estimate model or policy contrast', 'Report fit/effect proxy', 'Warn on identification and external validity'], 'python/numpy + optional R')
