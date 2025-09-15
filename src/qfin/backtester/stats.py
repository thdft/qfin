import datetime as datetime
from typing import cast

import numpy as np
import pandas as pd


def _compute_drawdown_duration_peaks(dd: pd.Series):
    """Compute drawdown duration peaks."""
    iloc = np.unique(np.r_[(dd == 0).values.nonzero()[0], len(dd) - 1])
    iloc = pd.Series(iloc, index=dd.index[iloc])

    # Calculate the duration and peak DD of each drawdown
    df = iloc.to_frame("iloc").assign(prev=iloc.shift())
    df = df[df["iloc"] > df["prev"] + 1].astype(np.int64)

    # If no drawdown since no trade, avoid below for pandas sake and return nan series
    if not len(df):
        return (dd.replace(0, np.nan),) * 2

    df["duration"] = df["iloc"].map(dd.index.__getitem__) - df["prev"].map(dd.index.__getitem__)
    df["peak_dd"] = df.apply(lambda row: dd.iloc[row["prev"] : row["iloc"] + 1].max(), axis=1)

    # Reindex the DataFrame to match the original index
    df = df.reindex(dd.index)

    return df["duration"], df["peak_dd"]


def _geometric_mean(returns: pd.Series) -> float:
    """Compute geometric mean of returns."""
    returns = returns.fillna(0) + 1
    if np.any(returns <= 0):
        return 0
    return np.exp(np.log(returns).sum() / (len(returns) or np.nan)) - 1


def _data_period(index: pd.Series):
    """Return data index period as pd.Timedelta"""
    values = pd.Series(index[-100:])
    return values.diff().dropna().median()


def _round_timedelta(value, period):
    if not isinstance(value, pd.Timedelta):
        return value
    resolution = getattr(period, "resolution_string", None) or period.resolution
    return value.ceil(resolution)


def stats(history, trades, risk_free_rate=5):
    """Compute the statistics."""
    indexs = history.index
    balance = history["balance"]
    equity = history["equity"]
    trades_df = trades

    s = pd.Series(dtype=object)
    s.loc["Start"] = indexs[0]
    s.loc["End"] = indexs[-1]
    s.loc["Duration"] = s.End - s.Start

    have_position = np.repeat(0, len(indexs))

    for t in trades_df.itertuples(index=False):
        have_position[t.entry_bar : t.exit_bar + 1] = 1

    s.loc["Exposure Time [%]"] = have_position.mean() * 100  # In "n bars" time, not index time
    s.loc["Equity Start"] = equity.iloc[0]
    s.loc["Equity Peak"] = equity.max()
    s.loc["Equity Final"] = equity.iloc[-1]
    s.loc["Equity Return [%]"] = (equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0] * 100
    s.loc["Balance Start"] = balance.iloc[0]
    s.loc["Balance Peak"] = balance.max()
    s.loc["Balance Final"] = balance.iloc[-1]
    s.loc["Balance Return [%]"] = (balance.iloc[-1] - balance.iloc[0]) / balance.iloc[0] * 100
    s.loc["Gross Return [%]"] = round(trades["return_pct"].sum() * 100, 2)  # it is 'balance return' but without the commissions
    s.loc["Total Commissions"] = history.iloc[-1]["commission"]

    dd = 1 - equity / np.maximum.accumulate(equity)
    dd_dur, dd_peaks = _compute_drawdown_duration_peaks(pd.Series(dd, index=indexs))

    is_datetime_index = isinstance(indexs, pd.DatetimeIndex)
    gmean_day_return: float = 0
    day_returns = np.array(np.nan)
    annual_trading_days = np.nan
    is_datetime_index = isinstance(indexs, pd.DatetimeIndex)
    if is_datetime_index:
        freq_days = cast(pd.Timedelta, _data_period(indexs)).days
        have_weekends = indexs.dayofweek.to_series().between(5, 6).mean() > 2 / 7 * 0.6
        annual_trading_days = (
            52
            if freq_days == 7
            else 12
            if freq_days == 31
            else 1
            if freq_days == 365
            else (365 if have_weekends else 252)
        )
        freq = {7: "W", 31: "ME", 365: "YE"}.get(freq_days, "D")
        day_returns = equity.resample(freq).last().dropna().pct_change()
        gmean_day_return = _geometric_mean(day_returns)

    # Annualized return and risk metrics are computed based on the (mostly correct)
    # assumption that the returns are compounded. See: https://dx.doi.org/10.2139/ssrn.3054517
    # Our annualized return matches `empyrical.annual_return(day_returns)` whereas
    # our risk doesn't; they use the simpler approach below.
    annualized_return = (1 + gmean_day_return) ** annual_trading_days - 1
    s.loc["Return (Ann.) [%]"] = annualized_return * 100
    s.loc["Volatility (Ann.) [%]"] = (
        np.sqrt(
            (day_returns.var(ddof=int(bool(day_returns.shape))) + (1 + gmean_day_return) ** 2) ** annual_trading_days
            - (1 + gmean_day_return) ** (2 * annual_trading_days)
        )
        * 100
    )

    if is_datetime_index:
        time_in_years = (s.loc["Duration"].days + s.loc["Duration"].seconds / 86400) / annual_trading_days
        s.loc["CAGR [%]"] = (
            ((s.loc["Equity Final"] / equity.iloc[0]) ** (1 / time_in_years) - 1) * 100 if time_in_years else np.nan
        )

    # risk_free_rate = 5  # (It seems reasonable to consider that, 5% in a year)
    # Our Sharpe mismatches `empyrical.sharpe_ratio()` because they use arithmetic mean return
    # and simple standard deviation

    s.loc["Sharpe Ratio"] = (s.loc["Return (Ann.) [%]"] - risk_free_rate * 100) / (
        s.loc["Volatility (Ann.) [%]"] or np.nan
    )  # noqa: E501
    # Our Sortino mismatches `empyrical.sortino_ratio()` because they use arithmetic mean return
    with np.errstate(divide="ignore"):
        s.loc["Sortino Ratio"] = (annualized_return - risk_free_rate) / (
            np.sqrt(np.mean(day_returns.clip(-np.inf, 0) ** 2)) * np.sqrt(annual_trading_days)
        )  # noqa: E501

    def __round_timedelta(value):
        return _round_timedelta(value, period=_data_period(indexs))

    max_dd = -np.nan_to_num(dd.max())
    s.loc["Calmar Ratio"] = annualized_return / (-max_dd or np.nan)
    s.loc["Max. Drawdown [%]"] = max_dd * 100
    s.loc["Avg. Drawdown [%]"] = -dd_peaks.mean() * 100
    s.loc["Max. Drawdown Duration"] = __round_timedelta(dd_dur.max())
    s.loc["Avg. Drawdown Duration"] = __round_timedelta(dd_dur.mean())
    s.loc["Total Trades"] = n_trades = len(trades_df)
    pl = trades_df["pnl"]
    win_rate = np.nan if not n_trades else (pl > 0).mean()
    s.loc["Win Rate [%]"] = win_rate * 100
    returns = trades_df["return_pct"]
    s.loc["Best Trade [%]"] = returns.max() * 100
    s.loc["Worst Trade [%]"] = returns.min() * 100
    mean_return = _geometric_mean(returns)
    s.loc["Avg. Trade [%]"] = mean_return * 100
    trades_df["duration"] = trades_df["exit_time"] - trades_df["entry_time"]
    durations = trades_df["duration"]
    s.loc["Max. Trade Duration"] = __round_timedelta(durations.max())
    s.loc["Avg. Trade Duration"] = __round_timedelta(durations.mean())
    s.loc["Profit Factor"] = returns[returns > 0].sum() / (abs(returns[returns < 0].sum()) or np.nan)
    s.loc["Expectancy [%]"] = returns.mean() * 100
    s.loc["SQN"] = np.sqrt(n_trades) * pl.mean() / (pl.std() or np.nan)
    s.loc["Kelly Criterion"] = win_rate - (1 - win_rate) / (pl[pl > 0].mean() / -pl[pl < 0].mean())

    s.loc["Candles"] = len(history)
    s.loc["Long Trades"] = len(trades_df[trades_df["is_long"]])
    s.loc["Short Trades"] = len(trades_df[~trades_df["is_long"]])
    s.loc["Exposure Trades [%]"] = round((s.loc["Long Trades"] + s.loc["Short Trades"]) / len(history), 2)

    return s
