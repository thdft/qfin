
Quantitative finance research tools in Python

# Install

`uv add git+https://github.com/thdft/qfin`

# How to use 

### Backtest Engine

```python 
import qfin

# date,        close,    signal
# 2023-01-03,  3824.13,   1
# 2023-01-04,  3852.96,   1
# 2023-01-05,  3808.10,   1
# ...    
# 2025-04-03,  5396.52,  -1
# 2025-04-04,  5074.08,  -1
# 2025-04-07,  5062.25,  -1

df = pd.read_csv("./my_table_above.csv", index_col=0, parse_dates=[0], sep=",")

backtest_params = {
    "initial_balance": 10000,
    "default_entry_value": 0.9, # 90%
    "default_entry_value_max": 20000, # but max $20000
}

bt = qfin.Backtester(dataset=df, **backtest_params)

# ---- running strategy ------------
for broker in bt.run():
    current_bar = broker.state.data.iloc[-1]
    previous_bar = broker.state.data.iloc[-2]

    current_signal = current_bar["signal"]
    previous_signal = previous_bar["signal"]
    changed = current_signal != previous_signal

    if changed:
        if current_signal == 1:
            broker.buy()
        elif current_signal == -1:
            broker.sell()
        else:
            broker.close()
```

### Backtest Result

```python
# ---- print statistics ------------
print(bt.stats())

# ---- plot result ------------
bt.plot()
```

## License

This project is licensed under the MIT License.