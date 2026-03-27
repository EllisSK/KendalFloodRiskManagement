import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .statistical.local import fit_gev_lmom, perform_jack_knifing

from tqdm import tqdm

def parse_observed_rainfall_data(data_path):
    df = pd.read_csv(data_path, skiprows=3)
    
    df.columns = df.columns.astype(str).str.strip()
    
    day_cols = [str(i) for i in range(1, 32)]
    
    actual_day_cols = [col for col in df.columns if col in day_cols]
    
    df_melted = df.melt(
        id_vars=["YEAR", "Month"], 
        value_vars=actual_day_cols, 
        var_name="Day", 
        value_name="Rainfall (mm)"
    )
    
    df_melted["Date"] = pd.to_datetime(
        df_melted["YEAR"].astype(str) + "-" + 
        df_melted["Month"].astype(str) + "-" + 
        df_melted["Day"].astype(str), 
        errors="coerce"
    )
    
    df_clean = df_melted.dropna(subset=["Date"])
    
    final_df = df_clean[["Date", "Rainfall (mm)"]].copy()
    final_df.sort_values("Date", inplace=True)
    final_df.reset_index(drop=True, inplace=True)
    
    return final_df

def parse_synthetic_rainfall_data(data_path):
    df = pd.read_csv(data_path)
    
    df.columns = df.columns.astype(str).str.strip()
    
    df["Rainfall (mm)"] = df.mean(axis=1, numeric_only=True)
    
    final_df = df[["Rainfall (mm)"]].copy()
    final_df.reset_index(drop=True, inplace=True)
    
    return final_df

def parse_shetran_validation_file(data_path):
    start_date_str="06/05/1993"

    df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip().str.lower()
    start_date = pd.to_datetime(start_date_str, dayfirst=True)
    first_serial = df["date"].iloc[0]
    df["date"] = start_date + pd.to_timedelta(df["date"] - first_serial, unit="D")
    return df[["date", "obs", "sim"]]

def calculate_rainfall_statistics(series):    
    is_wet = series > 0
    is_dry = ~is_wet
    
    wet_days_data = series[is_wet]
    
    propwet = len(wet_days_data) / len(series)
    
    rmed = np.median(wet_days_data)
    p99 = np.percentile(wet_days_data, 99)
    sdii = np.mean(wet_days_data)
        
    padded_dry = np.pad(is_dry.astype(int), (1, 1), mode="constant", constant_values=0)
    edges = np.diff(padded_dry)
    
    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0]
    
    max_cdd = np.max(ends - starts)
        
    return propwet, rmed, p99, sdii, max_cdd


def calculate_kge(obs, sim):
    if len(obs) != len(sim):
        raise Exception("Series are not the same length!")

    r = np.corrcoef(sim, obs)[0, 1]
    alpha = np.std(sim) / np.std(obs)
    beta = np.mean(sim) / np.mean(obs)

    print("Bias" + str(float(beta)))

    return 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)

def analyse_shetran_performance(obs, sim):
    #nomral kge
    kge = calculate_kge(obs, sim)

    #kge square
    obs_2 = np.power(obs, 2)
    sim_2 = np.power(sim, 2)

    kge_2 = calculate_kge(obs_2, sim_2)

    return kge, kge_2

def create_shetran_jackknife_plot(obs, sim, return_period_range):
    obs_flows = []
    obs_lower_bounds = []
    obs_upper_bounds = []
    
    sim_flows = []
    sim_lower_bounds = []
    sim_upper_bounds = []

    return_periods = np.linspace(return_period_range[0], return_period_range[1], 1000)

    for rp in tqdm(return_periods):
        obs_flow, obs_std, obs_moe, obs_lower, obs_upper = perform_jack_knifing(obs, rp)
        obs_flows.append(obs_flow)
        obs_lower_bounds.append(obs_lower)
        obs_upper_bounds.append(obs_upper)
        
        sim_flow, sim_std, sim_moe, sim_lower, sim_upper = perform_jack_knifing(sim, rp)
        sim_flows.append(sim_flow)
        sim_lower_bounds.append(sim_lower)
        sim_upper_bounds.append(sim_upper)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=obs_upper_bounds,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=obs_lower_bounds,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(0, 0, 255, 0.2)",
        name="Observed 95% CI"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=obs_flows,
        mode="lines",
        line=dict(color="blue", width=2),
        marker=dict(size=6),
        name="Observed GEV Estimate"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=sim_upper_bounds,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=sim_lower_bounds,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(255, 0, 0, 0.2)",
        name="Simulated 95% CI"
    ))

    fig.add_trace(go.Scatter(
        x=return_periods,
        y=sim_flows,
        mode="lines",
        line=dict(color="red", width=2),
        marker=dict(size=6),
        name="Simulated GEV Estimate"
    ))

    fig.update_layout(
        template="presentation",
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

import plotly.graph_objects as go

def create_sim_obs_plot(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["obs"],
        mode="lines",
        line=dict(color="blue", width=2),
        name="Observed"
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["sim"],
        mode="lines",
        line=dict(color="red", width=2),
        name="Simulated"
    ))

    fig.update_layout(
        template="presentation",
        title="Observed vs Simulated Hydrograph",
        xaxis_title="Date",
        yaxis_title="Flow (Cummecs)",
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