import yfinance as yf


def yahoo(
    ticker,
    start=None,
    end=None,
    interval="1d",
    period="max",
    auto_adjust=False,
    lowercase=True,
    progress=False,
    group_by="ticker",
):
    yf_data = yf.download(
        ticker,
        start=start,
        end=end,
        group_by=group_by,
        auto_adjust=auto_adjust,
        progress=progress,
        interval=interval,
        period=period,  # use "period" instead of start/end
    )

    if lowercase:
        yf_data.drop(["Adj Close"], axis=1, level=1, inplace=True)
        yf_data.rename(columns={ "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)  # fmt: off
        yf_data.rename_axis("date", inplace=True)

    if type(ticker) is str:
        return yf_data[ticker]
    else:
        return yf_data
