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
