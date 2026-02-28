import numpy as np
import plotly.graph_objects as go

from scipy.stats import lmoment
from scipy.stats import genextreme, t
from scipy.optimize import fsolve
from scipy.special import gamma

from tqdm import tqdm

def fit_gev_lmom(sample):
    lmoments = lmoment(sample)

    lambda_1 = lmoments[0][0]
    lambda_2 = lmoments[1][0]
    T_3 = lmoments[2][0]
    T_4 = lmoments[3][0]

    T_2 = lambda_2/lambda_1

    l_loc = lambda_1
    l_cv = T_2
    l_skew = T_3

    def func(k):
        return ((2 * (1 - 3.0**-k)) / (1 - 2.0**-k)) - (3 + l_skew)
    
    shape = fsolve(func, 1)[0]
    gamma_1k = gamma(1 + shape)
    scale = ((l_cv * l_loc) * shape) / (gamma_1k * (1 - 2**-shape))
    loc = l_loc - (scale / shape) * (1 - gamma_1k)

    return shape, loc, scale

def perform_jack_knifing(sample, return_period):
    sample_len = len(sample)
    aep = 1 - (1/return_period)

    shape, loc, scale = fit_gev_lmom(sample)
    flow_aep = genextreme.ppf(aep, shape, loc, scale)

    psudo_vals = []

    for i in range(sample_len):
        sub_sample = sample.drop(sample.index[i])

        shape, loc, scale = fit_gev_lmom(sub_sample)

        sub_flow_aep = genextreme.ppf(aep, shape, loc, scale)

        psudo_val = (flow_aep * sample_len) - ((sample_len - 1) * sub_flow_aep)

        psudo_vals.append(psudo_val)

    std_err = np.std(psudo_vals, ddof=1) / np.sqrt(len(psudo_vals))
    margin_of_err = t.ppf(1 - 0.05/2, df=len(psudo_vals)-1) * std_err
    lower_bound = np.mean(psudo_vals) - margin_of_err
    upper_bound = np.mean(psudo_vals) + margin_of_err

    return float(flow_aep), float(std_err), float(margin_of_err), float(lower_bound), float(upper_bound)

def create_jackknife_plot(sample, return_period_range):
    flows = []
    lower_bounds = []
    upper_bounds = []

    return_periods = np.linspace(return_period_range[0], return_period_range[1], 1000)

    for rp in tqdm(return_periods):
        flow, std_err, moe, lower, upper = perform_jack_knifing(sample, rp)
        flows.append(flow)
        lower_bounds.append(lower)
        upper_bounds.append(upper)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=upper_bounds,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=lower_bounds,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(0, 0, 255, 0.2)",
        name="95% Confidence Interval"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=flows,
        mode="lines",
        line=dict(color="blue", width=2),
        marker=dict(size=6),
        name="GEV Estimate"
    ))

    fig.update_layout(
        title="GEV Frequency Curve with Jackknife Confidence Intervals",
        xaxis_title="Return Period (Years)",
        yaxis_title="Annual Maximum Instantaneous Flow (Cummecs)",
        xaxis_type="log",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey"
        ),
        plot_bgcolor="white",
        hovermode="x unified"
    )

    return fig

def wrtie_jackknife_report(sample, return_period, path):
    shape, loc, scale = fit_gev_lmom(sample)
    flow_aep, std_err, margin_of_err, lower_bound, upper_bound = perform_jack_knifing(sample, return_period)

    with open(path, "w") as f:
        f.write(f"Jack-Knifing Report for {return_period}-year Return Period\n")
        f.write(f"GEV Shape Parameter: {shape}\n")
        f.write(f"GEV Location Parameter: {loc}\n")
        f.write(f"GEV Scale Parameter: {scale}\n")
        f.write(f"Modelled Flow: {flow_aep} cummecs\n")
        f.write(f"Standard Error: {std_err} cummecs\n")
        f.write(f"Margin of Error: {margin_of_err} cummecs\n")
        f.write(f"Lower Bound: {lower_bound} cummecs\n")
        f.write(f"Upper Bound: {upper_bound} cummecs")