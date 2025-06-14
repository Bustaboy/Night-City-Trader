# trading/analyze_performance.py
from trading.strategies import TradingStrategies
from core.database import db
from utils.logger import logger
import numpy as np
from sklearn.genetic import GA
import asyncio

class PerformanceAnalyzer:
    def __init__(self):
        self.strategies = TradingStrategies()

    async def auto_analyze_performance(self):
        try:
            symbols = db.fetch_all("SELECT DISTINCT symbol FROM historical_data")
            for symbol in [s[0] for s in symbols]:
                data = db.fetch_all("SELECT * FROM historical_data WHERE symbol = ? ORDER BY timestamp", (symbol,))
                df = pd.DataFrame(data, columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
                best_params = self.optimize_strategy(df, symbol)
                self.strategies.update_strategy(symbol, best_params)
                logger.info(f"Optimized {symbol} strategy: {best_params}")
        except Exception as e:
            logger.error(f"Performance analysis flatlined: {e}")

    def optimize_strategy(self, df, symbol):
        # Simplified GA optimization (placeholder)
        def fitness(params):
            signals = self.strategies.get_signal(symbol, df, "1h", "breakout", params)
            df["signal"] = signals
            returns = df["signal"].shift(1) * df["close"].pct_change()
            return -returns.mean() / returns.std() if returns.std() > 0 else 0
        ga = GA(population_size=10, generations=5, fitness_function=fitness, n_genes=2)
        best_params = ga.run()
        return {"atr_period": best_params[0], "breakout_threshold": best_params[1]}

performance_analyzer = PerformanceAnalyzer()
