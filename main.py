import pandas as pd

import plotly.express as px

from pathlib import Path

from src.estimation.statistical.local import *
from src.estimation.hydrograph import *
from src.estimation.shetran import *

def main():
    data = pd.read_csv("data/anmax_flows.csv")

    #fig = create_jackknife_plot(data, [2, 100])

    #fig.write_image("exports/jack_knife.svg", width=1592, height=984)

    #wrtie_jackknife_report(data, 100, "exports/jack_knife.txt")

    #fig2 = create_dual_jackknife_plot(data, [2, 100], "data/FEH_Catchment_Descriptors.xml", 0.67)

    #fig2.write_image("exports/jack_knife2.svg", width=1592, height=984)

    #calculate_design_storm("data/FEH_Catchment_Descriptors.xml", 100, 0.67)

    #sens_df = perform_sensitivity_analysis("data/FEH_Catchment_Descriptors.xml", 100)

    #fig3 = create_feh_heatmap(sens_df)

    #fig3.write_image("exports/heatmap.svg", width=1592, height=984)

    df = parse_observed_rainfall_data("data/nwe_rainfall.csv")

    print(calculate_rainfall_statistics(df["Rainfall (mm)"]))

    df = parse_synthetic_rainfall_data("data/73012_GEAR.csv")

    print(calculate_rainfall_statistics(df["Rainfall (mm)"]))

    df = parse_shetran_validation_file("data/shetran_validation.csv")
    print(analyse_shetran_performance(df["obs"], df["sim"]))

    sim_data = pd.read_csv("data/sim_anmax_flows.csv")

    #fig4 = create_shetran_jackknife_plot(data, sim_data, [2, 100])
    #fig4.write_image("exports/jack_knife3.svg", width=1592, height=984)

    wrtie_jackknife_report(sim_data, 100, "exports/jack_knife3.txt")

    fig5 = create_sim_obs_plot(df)
    fig5.write_image("exports/peaks.svg", width=1592, height=984)


if __name__ == "__main__":
    main()