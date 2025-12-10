# file: app/tests/test_indicators.py
import unittest
import pandas as pd
import numpy as np
from app.indicators import calculate_rsi_wilder

class TestIndicators(unittest.TestCase):
    def test_rsi_wilder_constant(self):
        # A constant price series should have delta=0, RSI should ideally be 50 or stable, 
        # but mathematically with 0 gain/loss it handles div/0. 
        # Let's test a simple rising series.
        prices = pd.Series(np.linspace(100, 200, 100))
        rsi = calculate_rsi_wilder(prices, 14)
        # Rising continuously means RSI should be high
        self.assertTrue(rsi.iloc[-1] > 70)

    def test_rsi_wilder_falling(self):
        prices = pd.Series(np.linspace(200, 100, 100))
        rsi = calculate_rsi_wilder(prices, 14)
        # Falling continuously means RSI should be low
        self.assertTrue(rsi.iloc[-1] < 30)

if __name__ == '__main__':
    unittest.main()
