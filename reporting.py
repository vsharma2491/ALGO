import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict

def generate_report(performance_metrics: Dict[str, float], trades: pd.DataFrame, equity_curve: pd.Series) -> None:
    """
    Generates a comprehensive backtest report.

    This function creates a complete report of the backtest results, including
    console output, PnL and drawdown charts, and exports to CSV, Excel, and
    HTML formats.

    Args:
        performance_metrics (Dict[str, float]): A dictionary of performance metrics.
        trades (pd.DataFrame): A DataFrame of all trades.
        equity_curve (pd.Series): The equity curve of the backtest.
    """
    print_metrics(performance_metrics)
    plot_pnl_curve(equity_curve)
    plot_drawdown(equity_curve)

    monthly_returns = equity_curve.resample('ME').ffill().pct_change()

    export_to_csv(trades, performance_metrics, monthly_returns)
    export_to_excel(trades, performance_metrics, monthly_returns)
    export_to_html(trades, performance_metrics, monthly_returns, equity_curve, "results/backtest_results.html")

def print_metrics(metrics: Dict[str, float]) -> None:
    """Prints the performance metrics to the console in a formatted table."""
    print("\n--- Backtest Performance Metrics ---")
    for key, value in metrics.items():
        print(f"{key:<20} {value}")
    print("------------------------------------\n")

def plot_pnl_curve(equity_curve: pd.Series) -> None:
    """Plots and saves the PnL curve chart."""
    plt.figure(figsize=(12, 6))
    equity_curve.plot()
    plt.title("Portfolio Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.savefig("results/pnl_curve.png")
    plt.close()
    print("PnL curve chart saved to results/pnl_curve.png")

def plot_drawdown(equity_curve: pd.Series) -> None:
    """Calculates, plots, and saves the drawdown chart."""
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak

    plt.figure(figsize=(12, 6))
    drawdown.plot(kind='area', color='red', alpha=0.3)
    plt.title("Portfolio Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.grid(True)
    plt.savefig("results/drawdown.png")
    plt.close()
    print("Drawdown chart saved to results/drawdown.png")

def export_to_csv(trades: pd.DataFrame, metrics: Dict[str, float], monthly_returns: pd.Series) -> None:
    """Exports the backtest results to CSV files."""
    trades.to_csv("results/trade_log.csv")
    pd.DataFrame([metrics]).to_csv("results/metrics_summary.csv", index=False)
    monthly_returns.to_csv("results/monthly_returns.csv")
    print("Results exported to CSV files in the 'results' directory.")

def export_to_excel(trades: pd.DataFrame, metrics: Dict[str, float], monthly_returns: pd.Series) -> None:
    """Exports the backtest results to a multi-sheet Excel file."""
    with pd.ExcelWriter("results/backtest_results.xlsx") as writer:
        trades.to_excel(writer, sheet_name="Trade Log")
        pd.DataFrame([metrics]).to_excel(writer, sheet_name="Metrics Summary", index=False)
        monthly_returns.to_excel(writer, sheet_name="Monthly Returns")
    print("Results exported to results/backtest_results.xlsx")

def export_to_html(trades: pd.DataFrame, metrics: Dict[str, float], monthly_returns: pd.Series, equity_curve: pd.Series, file_path: str) -> None:
    """Exports the backtest results to a self-contained HTML file with embedded charts."""
    import base64
    from io import BytesIO

    def fig_to_base64(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    # PnL Curve
    fig_pnl = plt.figure(figsize=(12, 6))
    equity_curve.plot()
    plt.title("Portfolio Equity Curve")
    plt.grid(True)
    pnl_b64 = fig_to_base64(fig_pnl)
    plt.close(fig_pnl)

    # Drawdown Chart
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    fig_dd = plt.figure(figsize=(12, 6))
    drawdown.plot(kind='area', color='red', alpha=0.3)
    plt.title("Portfolio Drawdown")
    plt.grid(True)
    dd_b64 = fig_to_base64(fig_dd)
    plt.close(fig_dd)

    html = f"""
    <html>
    <head>
        <title>Backtest Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 50%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Backtest Results</h1>
        <h2>Performance Metrics</h2>
        {pd.DataFrame([metrics]).to_html(index=False)}
        <h2>Monthly Returns</h2>
        {monthly_returns.to_frame().to_html()}
        <h2>PnL Curve</h2>
        <img src="data:image/png;base64,{pnl_b64}">
        <h2>Drawdown</h2>
        <img src="data:image/png;base64,{dd_b64}">
        <h2>Trade Log</h2>
        {trades.to_html()}
    </body>
    </html>
    """
    with open(file_path, "w") as f:
        f.write(html)
    print(f"HTML report saved to {file_path}")
