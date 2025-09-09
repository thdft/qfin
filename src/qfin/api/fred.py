import pandas as pd


def fred(series):
    """Download series from https://fred.stlouisfed.org
    Version: 1.1
    """
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series
    df = pd.read_csv(
        url,
        index_col=0,
        parse_dates=True,
        header=None,
        skiprows=1,
        names=["Date", series],
        na_values=".",
    )
    return df
