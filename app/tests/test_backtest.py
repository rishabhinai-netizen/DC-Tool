# file: app/tests/test_backtest.py
import unittest
import pandas as pd
import numpy as np
from app.backtest import run_trade_backtest

class TestBacktest(unittest.TestCase):
    def setUp(self):
        # Create a mock dataframe
        dates = pd.date_range(start='2023-01-01', periods=50)
        self.df = pd.DataFrame({
            'Close': [100]*50,
            'Middle': [100]*50,
            'High': [105]*50,
            'Low': [95]*50
        }, index=dates)

    def test_no_trades_flat(self):
        # Flat market, no crossovers
        trades, metrics = run_trade_backtest(self.df)
        self.assertTrue(trades.empty)
        self.assertEqual(metrics['trades'], 0)

    def test_simple_trade(self):
        # Create a crossover
        # Day 10: Close=110, Middle=100 (Buy)
        # Day 20: Close=90, Middle=100 (Sell)
        self.df.loc[self.df.index[10], 'Close'] = 110
        self.df.loc[self.df.index[20], 'Close'] = 90
        
        trades, metrics = run_trade_backtest(self.df)
        
        # Depending on how exact signals align with shift, 
        # index 10 Close > Mid (Buy Signal).
        # index 20 Close < Mid (Sell Signal).
        # Backtest iterates.
        
        self.assertGreater(metrics['trades'], 0)

if __name__ == '__main__':
    unittest.main()
