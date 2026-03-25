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

    df_long = df_long.set_index("Catchment Descriptor")

    return df_long

def interpolate_ddf_2022(xml_file_path, return_period, duration):
    df_parent = pd.read_xml(xml_file_path, xpath=".//CatchmentAverageDDF2022Values")
    rp_str = df_parent["ReturnPeriods"].iloc[0]
    return_periods = np.array([float(x.strip()) for x in str(rp_str).split(",")])
    
    df_depths = pd.read_xml(xml_file_path, xpath=".//CatchmentAverageDDF2022Values/Depths")
    durations = df_depths["duration"].astype(float).values
    
    depth_col = [col for col in df_depths.columns if col != "duration"][0]
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

def calculate_storm_profile(D, Dt):
    
    hardcoded_values = [
        0.189619671,
        0.20077609,
        0.212579979,
        0.225068136,
        0.238279372,
        0.252254619,
        0.267037033,
        0.282672106,
        0.299207781,
        0.316694568,
        0.335185672,
        0.354737113,
        0.375407862,
        0.397259969,
        0.420358703,
        0.444772687,
        0.470574035,
        0.497838496,
        0.526645586,
        0.557078727,
        0.589225372,
        0.623177133,
        0.659029883,
        0.696883858,
        0.736843729,
        0.779018648,
        0.823522254,
        0.870472642,
        0.919992252,
        0.972207692,
        1.027249439,
        1.085251402,
        1.146350297,
        1.21068476,
        1.278394113,
        1.349616649,
        1.424487248,
        1.503134017,
        1.58567353,
        1.672203919,
        1.762794646,
        1.857470845,
        1.956188414,
        2.058792283,
        2.164941684,
        2.273963814,
        2.384529085,
        2.493780946,
        2.59409202,
        2.635979223,
        2.635979223,
        2.59409202,
        2.493780946,
        2.384529085,
        2.273963814,
        2.164941684,
        2.058792283,
        1.956188414,
        1.857470845,
        1.762794646,
        1.672203919,
        1.58567353,
        1.503134017,
        1.424487248,
        1.349616649,
        1.278394113,
        1.21068476,
        1.146350297,
        1.085251402,
        1.027249439,
        0.972207692,
        0.919992252,
        0.870472642,
        0.823522254,
        0.779018648,
        0.736843729,
        0.696883858,
        0.659029883,
        0.623177133,
        0.589225372,
        0.557078727,
        0.526645586,
        0.497838496,
        0.470574035,
        0.444772687,
        0.420358703,
        0.397259969,
        0.375407862,
        0.354737113,
        0.335185672,
        0.316694568,
        0.299207781,
        0.282672106,
        0.267037033,
        0.252254619,
        0.238279372,
        0.225068136,
        0.212579979,
        0.20077609,
        0.189619671
    ]

  
    n_rain_bars = int(D / Dt)

    original_spacing = np.linspace(0, 1, len(hardcoded_values))
    
    target_spacing = np.linspace(0, 1, n_rain_bars)
    
    #Slightly more accurate than provided excel worksheet as values are linearly interoplated rather than rounded to nearest percentile
    resampled_profile = np.interp(target_spacing, original_spacing, hardcoded_values)

    normalised_profile = resampled_profile / np.sum(resampled_profile)
    
    return normalised_profile

    
def calculate_design_storm(xml_file_path):
    Dt = 1

    df = parse_feh_xml_to_dataframe(xml_file_path)

    Tp = calculate_time_to_peak(df["Value"]["propwet"], df["Value"]["dplbar"], df["Value"]["urbext1990"], df["Value"]["dpsbar"])

    D = calculate_duration(Tp, df["Value"]["saar"], Dt)

    profile = calculate_storm_profile(D, Dt)

    rddf = interpolate_ddf_2022(xml_file_path, 100, D)

    arf = calculate_arf(df["Value"]["area"], D)

    scf = 0.89

    return profile * arf * scf * rddf