class Params:
    def __init__(self, dataset, initial_balance, commission):
        self.dataset = dataset
        self.initial_balance = initial_balance
        self.commission = commission
        self.close_column = "close"


class Broker:
    def __init__(self, params):
        self.params = params
        self.data = []
        self.current_bar = 0
        self.is_last_bar = False
        self.last_price = False
        self.total_bar = len(params.dataset)
        self._nbars = 10

    def set_next_bar(self, index):
        self.current_bar = index
        _start = index - self._nbars if index - self._nbars > 0 else 0
        _end = index + 1
        self.data = self.params.dataset.iloc[_start:_end]
        self.is_last_bar = index + 1 == self.total_bar
        self.last_price = self.data.iloc[-1][self.params.close_column]
        self.refresh_values()

    def refresh_values(self):
        pass

    def buy(self):
        print("buy", self.last_price)
        pass

    def sell(self):
        print("sell", self.last_price)
        pass

    def close(self):
        print("close", self.last_price)
        pass


class Backtester:
    def __init__(
        self,
        dataset,
        initial_balance=10000,
        commission=0.01,
        ohlc_columns=["open", "high", "low", "close"],
    ):
        self.params = Params(dataset.copy(), initial_balance, commission)

    def run(self):
        self.broker = Broker(self.params)
        total = len(self.params.dataset)
        current = 1

        while current < total:
            self.broker.set_next_bar(current)
            yield self.broker
            current += 1
