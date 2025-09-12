from qfin.backtester.backtester import Backtester


def bt_signal_change(dataset, **karg):
    bt = Backtester(dataset=dataset, **karg)

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

    return bt
