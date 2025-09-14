import numpy as np
import pandas as pd

# ----------------
#  echo
# ----------------


def continue_echo(dataserie, initial_value=None, skip_values=[None]):
    """
    i.e:  input [0, -1,  0,  0,  0,  1,  0,  0,  0]
         output [0, -1, -1, -1, -1,  1,  1,  1,  1]
    """

    prev = dataserie.iloc[0] if initial_value is None else initial_value
    cur = prev
    arr = []

    verify_isnull = any([pd.isnull(item) for item in skip_values])
    skip_values = list(filter(lambda item: not pd.isnull(item), skip_values))

    for _, value in dataserie.items():
        if (verify_isnull) & pd.isnull(value):
            pass

        elif value is not prev:
            if value not in skip_values:
                prev = value
                cur = value

        arr.append(cur)

    return arr


def revert_echo(dataserie, empty_value=None):
    """
    i.e:  input  [0, -1, -1, -1, -1,  1,  1,  1,  1]
          output [0, -1,  0,  0,  0,  1,  0,  0,  0]
    """
    prev = empty_value
    arr = []
    for x, value in dataserie.items():
        if value == prev:
            arr.append(empty_value)
        else:
            arr.append(value)

        prev = value
    return arr


# ----------------
#  crossover
# ----------------


def crossover(dataserie_a, dataserie_b=None, shift=1, echo=False, nosignal_value=0):
    """whether a variable series crossed over another series"""

    col = "cross"
    df = dataserie_a.to_frame().copy()
    df["a"] = dataserie_a
    df["b"] = df["a"].copy().shift(1) if dataserie_b is None else dataserie_b
    df[col] = np.select(
        [
            np.isnan(df["a"]),
            np.isnan(df["b"]),
            (df["a"] > df["b"]) & (df["a"].shift(shift) < df["b"].shift(shift)),
            (df["a"] < df["b"]) & (df["a"].shift(shift) > df["b"].shift(shift)),
        ],
        [nosignal_value, nosignal_value, 1, -1],
        nosignal_value,
    )

    if echo:
        df[col] = continue_echo(df[col], initial_value=0, skip_values=[nosignal_value])

    return df[col]


# -------------------------
#  cross with 3 dataseries
# -------------------------

crossover3_labels = {3: "bullish", 2: "accumulation", 1: "recovery", -1: "warning", -2: "distribution", -3: "bearish"}


def crossover3(dataserie_a, dataserie_b, dataserie_c, echo=False, nosignal_value=0):
    col = "cross"
    df = dataserie_a.to_frame().copy()
    df["a"] = dataserie_a
    df["b"] = dataserie_b
    df["c"] = dataserie_c

    df[col] = np.select(
        [
            (df["a"] < df["b"]) & (df["a"] > df["c"]) & (df["b"] > df["c"]),
            (df["a"] < df["b"]) & (df["a"] < df["c"]) & (df["b"] > df["c"]),
            (df["a"] < df["b"]) & (df["a"] < df["c"]) & (df["b"] < df["c"]),
            (df["a"] > df["b"]) & (df["a"] < df["c"]) & (df["b"] < df["c"]),
            (df["a"] > df["b"]) & (df["a"] > df["c"]) & (df["b"] < df["c"]),
            (df["a"] > df["b"]) & (df["a"] > df["c"]) & (df["b"] > df["c"]),
        ],
        [-1, -2, -3, 1, 2, 3],
        nosignal_value,
    )

    if not echo:
        df[col] = revert_echo(df[col], empty_value=nosignal_value)

    return df[col]
