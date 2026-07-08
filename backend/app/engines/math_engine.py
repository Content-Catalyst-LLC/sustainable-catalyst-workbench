from __future__ import annotations
import numpy as np
from scipy import stats, integrate, optimize
from .common import parse_matrix, parse_number_list, parse_kv, parse_rows, result, svg_from_figure, eval_function, bar_graph
import matplotlib.pyplot as plt


def linear_system_solver(inputs):
    A = parse_matrix(inputs.get('A', '[[3,2],[1,2]]'))
    b = np.array(parse_number_list(inputs.get('b', '[5,5]')), dtype=float)
    warnings = []
    values = {"shape": list(A.shape), "rank": int(np.linalg.matrix_rank(A))}
    if A.ndim != 2 or A.shape[0] != b.shape[0]:
        raise ValueError('Matrix A must be 2D and b length must match A rows.')
    if A.shape[0] == A.shape[1]:
        values["determinant"] = float(np.linalg.det(A))
        values["condition_number"] = float(np.linalg.cond(A))
        if values["condition_number"] > 1e8:
            warnings.append('Matrix is ill-conditioned; small input changes can cause large output changes.')
        try:
            x = np.linalg.solve(A, b)
            method = 'solve'
        except np.linalg.LinAlgError:
            x = np.linalg.lstsq(A, b, rcond=None)[0]
            method = 'least_squares_due_to_singularity'
            warnings.append('Matrix was singular or near-singular; returned least-squares solution.')
        try:
            values["eigenvalues"] = [complex(v).real if abs(complex(v).imag) < 1e-10 else str(complex(v)) for v in np.linalg.eigvals(A)]
        except Exception:
            pass
    else:
        x = np.linalg.lstsq(A, b, rcond=None)[0]
        method = 'least_squares_over_or_under_determined'
        warnings.append('A is not square; returned least-squares solution.')
    residual = A @ x - b
    values.update({"solution": x.tolist(), "residual_norm": float(np.linalg.norm(residual)), "method": method})
    graph = bar_graph([f"r{i+1}" for i in range(len(residual))], residual.tolist(), 'Residual by equation', 'Residual')
    return result('Linear System Solver', 'Solved the linear system and checked rank, residual, conditioning, and stability.', values, warnings, [graph], ['Validate dimensions', 'Compute rank/conditioning', 'Solve or least-squares fallback', 'Inspect residual'], 'python/numpy')


def calculus_function_analyzer(inputs):
    expr = inputs.get('expression') or 'x**2 - 4*x + 3'
    x_min = float(inputs.get('x_min', -5)); x_max = float(inputs.get('x_max', 5))
    xs = np.linspace(x_min, x_max, 500)
    ys = eval_function(expr, xs)
    dys = np.gradient(ys, xs)
    area = float(np.trapz(ys, xs))
    idx_min, idx_max = int(np.nanargmin(ys)), int(np.nanargmax(ys))
    fig, ax = plt.subplots(figsize=(7.2, 4.4)); ax.plot(xs, ys, label='f(x)'); ax.plot(xs, dys, label="f'(x)"); ax.axhline(0, linewidth=1); ax.set_title('Function and numerical derivative'); ax.legend(); ax.grid(alpha=.25)
    graph = {"title":"Function and derivative", "type":"line", "svg": svg_from_figure(fig)}; plt.close(fig)
    return result('Calculus Function Analyzer', 'Computed numerical derivative, accumulation, and extrema scan over the selected interval.', {"expression": expr, "area_trapezoid": area, "min_point": [float(xs[idx_min]), float(ys[idx_min])], "max_point": [float(xs[idx_max]), float(ys[idx_max])], "mean_slope": float(np.nanmean(dys))}, [], [graph], ['Evaluate function over interval', 'Estimate derivative with finite differences', 'Integrate numerically', 'Scan extrema'], 'python/numpy')


def statistics_analyzer(inputs):
    data = np.array(parse_number_list(inputs.get('data')), dtype=float)
    if data.size < 2: raise ValueError('Enter at least two numeric values.')
    mean = float(np.mean(data)); sd = float(np.std(data, ddof=1)); se = sd / np.sqrt(data.size)
    ci = stats.t.interval(0.95, data.size-1, loc=mean, scale=se) if data.size > 1 else (mean, mean)
    fig, ax = plt.subplots(figsize=(7.2,4.4)); ax.hist(data, bins='auto', edgecolor='black'); ax.axvline(mean, linestyle='--'); ax.set_title('Data distribution'); ax.grid(axis='y', alpha=.25)
    graph = {"title":"Histogram", "type":"histogram", "svg": svg_from_figure(fig)}; plt.close(fig)
    return result('Statistics Analyzer', 'Computed descriptive statistics, interval estimate, and distribution graph.', {"n": int(data.size), "mean": mean, "median": float(np.median(data)), "sample_sd": sd, "min": float(np.min(data)), "max": float(np.max(data)), "ci95_mean": [float(ci[0]), float(ci[1])], "skewness": float(stats.skew(data)), "kurtosis": float(stats.kurtosis(data))}, [], [graph], ['Parse data', 'Compute descriptive statistics', 'Estimate confidence interval', 'Render histogram'], 'python/scipy + optional R')


def regression_analyzer(inputs):
    x = np.array(parse_number_list(inputs.get('x')), dtype=float); y = np.array(parse_number_list(inputs.get('y')), dtype=float)
    if x.size != y.size or x.size < 2: raise ValueError('x and y must have same length and at least two values.')
    fit = stats.linregress(x, y)
    xs = np.linspace(np.min(x), np.max(x), 200); yh = fit.intercept + fit.slope * xs
    residuals = y - (fit.intercept + fit.slope * x)
    fig, ax = plt.subplots(figsize=(7.2,4.4)); ax.scatter(x, y); ax.plot(xs, yh); ax.set_title('Linear regression fit'); ax.grid(alpha=.25)
    graph1 = {"title":"Regression fit", "type":"scatter_fit", "svg": svg_from_figure(fig)}; plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.2,4.4)); ax.axhline(0, linewidth=1); ax.scatter(x, residuals); ax.set_title('Residual plot'); ax.grid(alpha=.25)
    graph2 = {"title":"Residuals", "type":"residuals", "svg": svg_from_figure(fig)}; plt.close(fig)
    return result('Regression Analyzer', 'Fit a linear model and returned coefficient diagnostics and residual graph.', {"slope": float(fit.slope), "intercept": float(fit.intercept), "r_squared": float(fit.rvalue**2), "p_value": float(fit.pvalue), "standard_error": float(fit.stderr)}, [], [graph1, graph2], ['Parse paired data', 'Fit ordinary least squares line', 'Compute diagnostics', 'Graph fit and residuals'], 'python/scipy + optional R')


def probability_distribution_calculator(inputs):
    dist = (inputs.get('distribution') or 'normal').lower(); params = parse_kv(inputs.get('params') or 'mean=0;sd=1'); value = float(inputs.get('value', 1))
    fig, ax = plt.subplots(figsize=(7.2,4.4)); values = {}
    if dist == 'binomial':
        n = int(params.get('n', 20)); p = float(params.get('p', .5)); xs = np.arange(n+1); ys = stats.binom.pmf(xs, n, p); ax.bar(xs, ys); values = {"pmf_at_value": float(stats.binom.pmf(int(value), n, p)), "cdf_at_value": float(stats.binom.cdf(int(value), n, p)), "mean": n*p, "variance": n*p*(1-p)}
    elif dist == 'poisson':
        lam = float(params.get('lambda', params.get('lam', 3))); xs = np.arange(0, max(12, int(lam*4)+1)); ys = stats.poisson.pmf(xs, lam); ax.bar(xs, ys); values = {"pmf_at_value": float(stats.poisson.pmf(int(value), lam)), "cdf_at_value": float(stats.poisson.cdf(int(value), lam)), "mean": lam, "variance": lam}
    elif dist == 'beta':
        a = float(params.get('alpha', params.get('a', 2))); b = float(params.get('beta', params.get('b', 5))); xs = np.linspace(0,1,400); ys = stats.beta.pdf(xs,a,b); ax.plot(xs, ys); ax.axvline(value, linestyle='--'); values = {"pdf_at_value": float(stats.beta.pdf(value,a,b)), "cdf_at_value": float(stats.beta.cdf(value,a,b)), "mean": a/(a+b), "variance": (a*b)/(((a+b)**2)*(a+b+1))}
    else:
        mean = float(params.get('mean',0)); sd = float(params.get('sd',1)); xs = np.linspace(mean-4*sd, mean+4*sd, 400); ys = stats.norm.pdf(xs, mean, sd); ax.plot(xs, ys); ax.axvline(value, linestyle='--'); values = {"pdf_at_value": float(stats.norm.pdf(value, mean, sd)), "cdf_at_value": float(stats.norm.cdf(value, mean, sd)), "upper_tail": float(1-stats.norm.cdf(value, mean, sd)), "mean": mean, "sd": sd}
    ax.set_title(f'{dist.title()} distribution'); ax.grid(alpha=.25)
    graph = {"title":"Probability distribution", "type":"distribution", "svg": svg_from_figure(fig)}; plt.close(fig)
    return result('Probability Distribution Calculator', 'Computed distribution values and displayed distribution shape.', values, [], [graph], engine='python/scipy')


def differential_equation_simulator(inputs):
    model = inputs.get('model') or 'logistic'; t_end = float(inputs.get('t_end', 30)); t = np.linspace(0, t_end, 600); warnings=[]
    if model == 'exponential_decay':
        y0 = float(inputs.get('initial', 10)); rate = float(inputs.get('rate', .2)); y = y0 * np.exp(-rate * t); values={"model":model,"initial":y0,"rate":rate,"final":float(y[-1])}
        plot_series = [(t,y,'state')]
    elif model == 'harmonic_oscillator':
        y0 = parse_number_list(inputs.get('initial','1,0')); omega = float(inputs.get('rate',1));
        def f(tt, z): return [z[1], -(omega**2)*z[0]]
        sol = integrate.solve_ivp(f, [0,t_end], y0[:2], t_eval=t); values={"model":model,"omega":omega,"final_position":float(sol.y[0,-1]),"final_velocity":float(sol.y[1,-1])}; plot_series=[(t,sol.y[0],'position'),(t,sol.y[1],'velocity')]
    elif model == 'predator_prey':
        y0 = parse_number_list(inputs.get('initial','40,9')); a=.7; b=.02; c=.3; d=.01
        def f(tt,z):
            prey,pred = z; return [a*prey - b*prey*pred, d*prey*pred - c*pred]
        sol = integrate.solve_ivp(f,[0,t_end],y0[:2],t_eval=t); values={"model":model,"final_prey":float(sol.y[0,-1]),"final_predator":float(sol.y[1,-1])}; plot_series=[(t,sol.y[0],'prey'),(t,sol.y[1],'predator')]
    else:
        y0 = float(inputs.get('initial',10)); r = float(inputs.get('rate', .25)); K = float(inputs.get('carrying_capacity', inputs.get('K',100))); y = K/(1+((K-y0)/max(y0,1e-12))*np.exp(-r*t)); values={"model":"logistic","initial":y0,"rate":r,"carrying_capacity":K,"final":float(y[-1])}; plot_series=[(t,y,'state')]
    fig, ax = plt.subplots(figsize=(7.2,4.4))
    for xs, ys, label in plot_series: ax.plot(xs, ys, label=label)
    ax.set_title('Dynamical system trajectory'); ax.set_xlabel('time'); ax.legend(); ax.grid(alpha=.25)
    graph={"title":"System trajectory","type":"trajectory","svg":svg_from_figure(fig)}; plt.close(fig)
    return result('Differential Equation Simulator', 'Simulated a first-order or small dynamical system. Julia bridge is included for future high-end simulations.', values, warnings, [graph], engine='python/scipy + optional Julia')
