"""

PERFORMANCE METRICS


PURPOSE:
    Calculate trading performance metrics for strategy evaluation.

METRICS:
    - Total Return: (Final - Initial) / Initial
    - Sharpe Ratio: Risk-adjusted return
    - Max Drawdown: Largest peak-to-trough decline
    - Win Rate: % of profitable trades
    - Average Trade Return: Mean return per trade
    - Sortino Ratio: Downside risk-adjusted return

"""

import numpy as np
import pandas as pd
from typing import List, Dict


def calculate_total_return(initial_value: float, final_value: float) -> float:
    """
    Calculate total return percentage.

    Args:
        initial_value: Starting portfolio value
        final_value: Ending portfolio value

    Returns:
        Total return as decimal (e.g., 0.15 = 15%)
    """
    return (final_value - initial_value) / initial_value


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.

    Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns

    Args:
        returns: Series of periodic returns
        risk_free_rate: Annual risk-free rate (default: 2%)
        periods_per_year: Trading periods per year (default: 252 for daily)

    Returns:
        Annualized Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0

    # Annualize mean and std
    mean_return = returns.mean() * periods_per_year
    std_return = returns.std() * np.sqrt(periods_per_year)

    # Sharpe ratio
    sharpe = (mean_return - risk_free_rate) / std_return

    return sharpe


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sortino ratio.

    Similar to Sharpe, but only penalizes downside volatility.

    Args:
        returns: Series of periodic returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year

    Returns:
        Annualized Sortino ratio
    """
    if len(returns) == 0:
        return 0

    # Annualize mean
    mean_return = returns.mean() * periods_per_year

    # Downside deviation (only negative returns)
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return np.inf  # No downside risk

    downside_std = downside_returns.std() * np.sqrt(periods_per_year)

    if downside_std == 0:
        return np.inf

    # Sortino ratio
    sortino = (mean_return - risk_free_rate) / downside_std

    return sortino


def calculate_max_drawdown(portfolio_values: pd.Series) -> float:
    """
    Calculate maximum drawdown.

    Max Drawdown = max((Peak - Trough) / Peak) over all peaks

    Args:
        portfolio_values: Series of portfolio values over time

    Returns:
        Maximum drawdown as negative decimal (e.g., -0.25 = -25%)
    """
    if len(portfolio_values) == 0:
        return 0

    # Calculate running maximum
    running_max = portfolio_values.cummax()

    # Calculate drawdown at each point
    drawdown = (portfolio_values - running_max) / running_max

    # Maximum drawdown (most negative)
    max_dd = drawdown.min()

    return max_dd


def calculate_win_rate(trade_returns: List[float]) -> float:
    """
    Calculate win rate (% of profitable trades).

    Args:
        trade_returns: List of returns for each trade

    Returns:
        Win rate as decimal (e.g., 0.58 = 58%)
    """
    if len(trade_returns) == 0:
        return 0

    winning_trades = sum(1 for r in trade_returns if r > 0)
    total_trades = len(trade_returns)

    return winning_trades / total_trades


def calculate_avg_trade_return(trade_returns: List[float]) -> float:
    """
    Calculate average return per trade.

    Args:
        trade_returns: List of returns for each trade

    Returns:
        Average return as decimal
    """
    if len(trade_returns) == 0:
        return 0

    return np.mean(trade_returns)


def calculate_profit_factor(trade_returns: List[float]) -> float:
    """
    Calculate profit factor (gross profits / gross losses).

    Args:
        trade_returns: List of returns for each trade

    Returns:
        Profit factor (>1 is profitable)
    """
    if len(trade_returns) == 0:
        return 0

    gross_profits = sum(r for r in trade_returns if r > 0)
    gross_losses = abs(sum(r for r in trade_returns if r < 0))

    if gross_losses == 0:
        return np.inf if gross_profits > 0 else 0

    return gross_profits / gross_losses


def calculate_calmar_ratio(
    total_return: float,
    max_drawdown: float,
    years: float = 1.0
) -> float:
    """
    Calculate Calmar ratio (annualized return / max drawdown).

    Args:
        total_return: Total return over period
        max_drawdown: Maximum drawdown (negative)
        years: Period length in years

    Returns:
        Calmar ratio
    """
    if max_drawdown >= 0:
        return np.inf if total_return > 0 else 0

    annualized_return = (1 + total_return) ** (1 / years) - 1

    return abs(annualized_return / max_drawdown)


def generate_performance_report(
    portfolio_values: pd.Series,
    trade_returns: List[float],
    initial_capital: float
) -> Dict:
    """
    Generate comprehensive performance report.

    Args:
        portfolio_values: Series of portfolio values over time
        trade_returns: List of returns for each completed trade
        initial_capital: Starting capital

    Returns:
        Dictionary of all performance metrics
    """
    # Calculate returns
    returns = portfolio_values.pct_change().dropna()

    # Calculate metrics
    final_value = portfolio_values.iloc[-1]
    total_return = calculate_total_return(initial_capital, final_value)
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    max_dd = calculate_max_drawdown(portfolio_values)
    win_rate = calculate_win_rate(trade_returns)
    avg_trade = calculate_avg_trade_return(trade_returns)
    profit_factor = calculate_profit_factor(trade_returns)

    # Estimate years (assuming daily data)
    years = len(portfolio_values) / 252
    calmar = calculate_calmar_ratio(total_return, max_dd, years)

    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'avg_trade_return': avg_trade,
        'profit_factor': profit_factor,
        'calmar_ratio': calmar,
        'num_trades': len(trade_returns)
    }


def print_performance_report(metrics: Dict):
    """
    Print formatted performance report.

    Args:
        metrics: Dictionary from generate_performance_report()
    """
    print("\n" + "="*60)
    print("PERFORMANCE REPORT")
    print("="*60)
    print(f"Initial Capital:     ${metrics['initial_capital']:,.2f}")
    print(f"Final Value:         ${metrics['final_value']:,.2f}")
    print(f"Total Return:        {metrics['total_return']:+.2%}")
    print(f"\nRisk-Adjusted Returns:")
    print(f"  Sharpe Ratio:      {metrics['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio:     {metrics['sortino_ratio']:.2f}")
    print(f"  Calmar Ratio:      {metrics['calmar_ratio']:.2f}")
    print(f"\nRisk Metrics:")
    print(f"  Max Drawdown:      {metrics['max_drawdown']:.2%}")
    print(f"\nTrade Statistics:")
    print(f"  Number of Trades:  {metrics['num_trades']}")
    print(f"  Win Rate:          {metrics['win_rate']:.1%}")
    print(f"  Avg Trade Return:  {metrics['avg_trade_return']:+.2%}")
    print(f"  Profit Factor:     {metrics['profit_factor']:.2f}")
    print("="*60)


def main():
    """Test metrics calculation."""
    print("="*60)
    print("PERFORMANCE METRICS - Testing")
    print("="*60)

    # Sample data
    portfolio_values = pd.Series([
        10000, 10200, 10150, 10400, 10300,
        10500, 10450, 10600, 10800, 10900,
        11000, 10850, 11200, 11300, 11500
    ])

    trade_returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, -0.03, 0.06]

    # Generate report
    metrics = generate_performance_report(
        portfolio_values,
        trade_returns,
        initial_capital=10000
    )

    # Print report
    print_performance_report(metrics)

    print("\n[COMPLETE] METRICS TEST COMPLETE")


if __name__ == "__main__":
    main()
