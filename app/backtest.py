# file: app/backtest.py
import pandas as pd
import numpy as np
from app.logger import log_error

def run_trade_backtest(df, initial_capital=100000, slippage_pct=0.001, commission_pct=0.001):
    """
    Event-based backtest (Vectorized preprocessing + Iterative trade log).
    Returns: trades_df, metrics_dict
    """
    try:
        df = df.copy()
        # Strategy Logic:
        # Buy: Close > Middle (from below)
        # Exit: Close < Middle (from above)
        
        # Identify Crossovers
        df['Buy_Signal'] = (df['Close'] > df['Middle']) & (df['Close'].shift(1) <= df['Middle'].shift(1))
        df['Sell_Signal'] = (df['Close'] < df['Middle']) & (df['Close'].shift(1) >= df['Middle'].shift(1))
        
        trades = []
        in_position = False
        entry_price = 0.0
        entry_date = None
        
        # Iterate to pair signals (cannot be fully vectorized easily if we want stateful trade management)
        # Optimization: Only iterate rows where signals exist
        signal_rows = df[(df['Buy_Signal']) | (df['Sell_Signal'])].copy()
        
        for date, row in signal_rows.iterrows():
            if row['Buy_Signal'] and not in_position:
                # Enter
                # Close-to-Close entry
                entry_price = row['Close'] * (1 + slippage_pct + commission_pct)
                entry_date = date
                in_position = True
                
            elif row['Sell_Signal'] and in_position:
                # Exit
                exit_price = row['Close'] * (1 - slippage_pct - commission_pct)
                pnl_pct = (exit_price - entry_price) / entry_price
                
                trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': date,
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'duration_days': (date - entry_date).days,
                    'is_win': pnl_pct > 0
                })
                in_position = False
        
        # Handle open position at end
        if in_position:
            # Mark to market at last close
            last_row = df.iloc[-1]
            exit_price = last_row['Close']
            pnl_pct = (exit_price - entry_price) / entry_price
            trades.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': last_row.name,
                'exit_price': exit_price,
                'pnl_pct': pnl_pct,
                'duration_days': (last_row.name - entry_date).days,
                'is_win': pnl_pct > 0,
                'status': 'Open'
            })

        trades_df = pd.DataFrame(trades)
        
        # Metrics
        if trades_df.empty:
            return pd.DataFrame(), {
                "total_return": 0.0, "cagr": 0.0, "win_rate": 0.0, 
                "trades": 0, "sharpe": 0.0, "max_drawdown": 0.0
            }

        # Calculate Equity Curve for Sharpe/Drawdown
        trades_df['equity_growth'] = 1 + trades_df['pnl_pct']
        total_ret = trades_df['equity_growth'].prod() - 1
        
        # Simple CAGR approximation
        days = (df.index[-1] - df.index[0]).days
        years = max(days / 365.25, 0.5) # avoid div by zero
        cagr = (1 + total_ret) ** (1 / years) - 1
        
        win_rate = len(trades_df[trades_df['is_win']]) / len(trades_df)
        
        # Max Drawdown (Approximate based on trade sequence equity curve)
        cum_equity = trades_df['equity_growth'].cumprod()
        running_max = cum_equity.cummax()
        drawdown = (cum_equity - running_max) / running_max
        max_dd = drawdown.min()
        
        # Sharpe (Using trade returns, assuming risk_free=0)
        avg_ret = trades_df['pnl_pct'].mean()
        std_ret = trades_df['pnl_pct'].std()
        sharpe = (avg_ret / std_ret) * np.sqrt(len(trades_df)) if std_ret != 0 else 0

        metrics = {
            "total_return": round(total_ret * 100, 2),
            "cagr": round(cagr * 100, 2),
            "win_rate": round(win_rate * 100, 2),
            "trades": len(trades_df),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "avg_pnl": round(avg_ret * 100, 2)
        }
        
        return trades_df, metrics

    except Exception as e:
        log_error(e, "Backtest failure")
        return pd.DataFrame(), {}
