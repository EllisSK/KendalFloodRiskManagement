import pandas as pd

from src.estimation.statistical.local import *

def main():
    data = pd.read_csv("data/anmax_flows.csv")

    fig = create_jackknife_plot(data, [2, 100])

    fig.write_image("exports/jack_knife.svg", width=1592, height=984)


if __name__ == "__main__":
    main()