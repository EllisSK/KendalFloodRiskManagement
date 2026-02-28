import pandas as pd

from src.estimation.statistical.local import *

def main():
    data = pd.read_csv("data/anmax_flows.csv")

    fig = create_jackknife_plot(data, [2, 100])

    fig.write_image("exports/jack_knife.svg", width=1592, height=984)

    wrtie_jackknife_report(data, 100, "exports/jack_knife.txt")


if __name__ == "__main__":
    main()