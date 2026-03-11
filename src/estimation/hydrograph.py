import numpy as np
import pandas as pd

from scipy.interpolate import RegularGridInterpolator

def calculate_arf(area, duration):
    ln_A = np.log(area)

    if area <= 20:
        a = 0.40 - 0.0208 * np.log(4.6 - ln_A)
        b = 0.0394 * (area ** 0.354)
    elif area < 100:
        a = 0.40 - 0.00382 * ((4.6 - ln_A) ** 2)
        b = 0.0394 * (area ** 0.354)
    elif area < 500:
        a = 0.40 - 0.00382 * ((4.6 - ln_A) ** 2)
        b = 0.0627 * (area ** 0.254)
    elif area < 1000:
        a = 0.40 - 0.0208 * np.log(ln_A - 4.6)
        b = 0.0627 * (area ** 0.254)
    else:
        a = 0.40 - 0.0208 * np.log(ln_A - 4.6)
        b = 0.1050 * (area ** 0.180)

    arf = 1 - b * (duration ** (-1 * a))
    
    return arf

def parse_feh_xml_to_dataframe(xml_file_path):
    df_desc = pd.read_xml(xml_file_path, xpath=".//CatchmentDescriptors")
    df_catch_ddf = pd.read_xml(xml_file_path, xpath=".//CatchmentAverageDDFValues")
    df_point_ddf = pd.read_xml(xml_file_path, xpath=".//PointDDFValues")
    
    df_combined = pd.concat([df_desc, df_catch_ddf, df_point_ddf], axis=1)

    df_long = df_combined.melt(
        var_name="Catchment Descriptor", 
        value_name="Value"
    )

    return df_long

def interpolate_ddf_2022(xml_file_path, return_period, duration):
    df_parent = pd.read_xml(xml_file_path, xpath=".//CatchmentAverageDDF2022Values")
    rp_str = df_parent["ReturnPeriods"].iloc
    return_periods = np.array([float(x.strip()) for x in str(rp_str).split(",")])
    
    df_depths = pd.read_xml(xml_file_path, xpath=".//CatchmentAverageDDF2022Values/Depths")
    durations = df_depths["duration"].astype(float).values
    
    depth_col = [col for col in df_depths.columns if col != "duration"]
    depths_matrix = np.array([
        [float(x.strip()) for x in str(val).split(",")]
        for val in df_depths[depth_col]
    ])
    
    interpolator = RegularGridInterpolator((durations, return_periods), depths_matrix)
    
    interpolated_value = interpolator((duration, return_period))
    return float(interpolated_value)

def calculate_time_to_peak(propwet, dplbar, urbext1990, dpsbar):
    return 1.56 * (propwet ** -1.09) * (dplbar ** 0.6) * ((1 + urbext1990) ** -3.34) * (dpsbar ** -0.28)

def calculate_duration(Tp, SAAR, Dt):
    target_val = Tp * (1 + SAAR / 1000)
    
    ratio = target_val / Dt
    
    n = np.round((ratio - 1) / 2)
    nearest_odd = 2 * n + 1
    
    return nearest_odd * Dt

def calculate_design_storm_precipitation(propwet, dplbar, urbext1990, dpsbar, saar, Dt, xml_file_path, return_period, area):
    Tp = calculate_time_to_peak(propwet, dplbar, urbext1990, dpsbar)
    
    duration = calculate_duration(Tp, saar, Dt)
    
    rddf = interpolate_ddf_2022(xml_file_path, return_period, duration)

    arf = calculate_arf(area, duration)

    scf = 0.89

    return rddf * arf * scf

def calculate_storm_profile(urbext1990, D, Dt):
    print(urbext1990)
    if urbext1990 < 0.125:
        a = 0.06
        b = 1.026
    else:
        a = 0.1
        b = 0.815

    def intensity_func(t, a, b):
        x = 2 * np.abs(t - 0.5)
        z = x * b
        
        intensity = (b * np.log(a) * np.power(a, z)) / (a - 1)
        return intensity
    
    n_rain_bars = int(D / Dt)

    half_step = (Dt / D) / 2.0
    time_vals = np.linspace(half_step, 1.0 - half_step, n_rain_bars)

    profile = intensity_func(time_vals, a, b)

    profile_sum = sum(profile)

    return profile / profile_sum
    
def calculate_design_storm():
    pass