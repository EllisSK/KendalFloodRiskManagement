import pandas as pd

from src.estimation.statistical.local import *
from src.estimation.hydrograph import *

def main():
    #data = pd.read_csv("data/anmax_flows.csv")

    #fig = create_jackknife_plot(data, [2, 100])

    #fig.write_image("exports/jack_knife.svg", width=1592, height=984)

    #wrtie_jackknife_report(data, 100, "exports/jack_knife.txt")

    catchment_parameters = parse_feh_xml_to_dataframe("data/FEH_Catchment_Descriptors.xml")

    print(catchment_parameters)


if __name__ == "__main__":
    main()