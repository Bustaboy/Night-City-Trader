# trading/strategies.py
"""
Arasaka Trading Strategies - Multiple strategies for different market conditions
"""
import pandas as pd
import numpy as np
import talib

from config.settings import settings
from utils.logger import logger

class TradingStrategies:
    def __init__(self):
        self.config = settings.TRADING["strategies"]
        self.strategy_params = {}
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        try:
            # Ensure we have enough data
            if len(df) < 50:
                logger.warning("Insufficient data for indicators")
                return df
            
            # ATR (Average True Range)
            if 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                df['atr'] = true_range.rolling(window=14).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['std_20'] = df['close'].rolling(window=20).std()
            df['bollinger_upper'] = df['sma_20'] + (2 * df['std_20'])
            df['bollinger_lower'] = df['sma_20'] - (2 * df['std_20'])
            df['bollinger_width'] = df['bollinger_upper'] - df['bollinger_lower']
            df['bollinger_pct'] = (df['close'] - df['bollinger_lower']) / (df['bollinger_width'] + 1e-10)
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 1e-10)
            
            # Price action
            df['price_change'] = df['close'].pct_change()
            df['high_low_ratio'] = (df['high'] - df['low']) / (df['close'] + 1e-10)
            
            # Support and Resistance
            df['resistance'] = df['high'].rolling(window=20).max()
            df['support'] = df['low'].rolling(window=20).min()
            
            # Fill NaN values
            df = df.fillna(method='ffill').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Indicator calculation failed: {e}")
            return df
    
    def get_signal(self, symbol, data, timeframe, strategy="breakout", custom_params=None):
        """Generate trading signals based on strategy"""
        try:
            # Convert data to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(
                    data,
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
            else:
                df = data.copy()
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Apply strategy
            if strategy == "breakout":
                signals = self._breakout_strategy(df, custom_params)
            elif strategy == "mean_reversion":
                signals = self._mean_reversion_strategy(df, custom_params)
            elif strategy == "momentum":
                signals = self._momentum_strategy(df, custom_params)
            elif strategy == "scalping":
                signals = self._scalping_strategy(df, custom_params)
            elif strategy == "swing":
                signals = self._swing_strategy(df, custom_params)
            elif strategy == "combo":
                signals = self._combo_strategy(df, custom_params)
            else:
                logger.warning(f"Unknown strategy: {strategy}")
                signals = np.zeros(len(df))
            
            logger.info(f"Generated {strategy} signals for {symbol} on {timeframe}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return np.zeros(len(data) if isinstance(data, list) else len(df))
    
    def _breakout_strategy(self, df, params=None):
        """Breakout trading strategy"""
        if params is None:
            params = self.config.get("breakout", {})
        
        atr_period = params.get("atr_period", 14)
        breakout_threshold = params.get("breakout_threshold", 2.0)
        
        signals = np.zeros(len(df))
        
        if 'atr' not in df.columns or df['atr'].isna().all():
            return signals
        
        for i in range(1, len(df)):
            # Long signal - price breaks above resistance
            if (df['close'].iloc[i] > df['resistance'].iloc[i-1] and
                df['volume'].iloc[i] > df['volume_sma'].iloc[i] * 1.5 and
                df['atr'].iloc[i] > 0):
                signals[i] = 1
            
            # Short signal - price breaks below support
            elif (df['close'].iloc[i] < df['support'].iloc[i-1] and
                  df['volume'].iloc[i] > df['volume_sma'].iloc[i] * 1.5 and
                  df['atr'].iloc[i] > 0):
                signals[i] = -1
        
        return signals
    
    def _mean_reversion_strategy(self, df, params=None):
        """Mean reversion strategy using RSI and Bollinger Bands"""
        if params is None:
            params = self.config.get("mean_reversion", {})
        
        rsi_upper = params.get("rsi_upper", 70)
        rsi_lower = params.get("rsi_lower", 30)
        
        signals = np.zeros(len(df))
        
        for i in range(1, len(df)):
            # Long signal - oversold conditions
            if (df['rsi'].iloc[i] < rsi_lower and
                df['close'].iloc[i] < df['bollinger_lower'].iloc[i] and
                df['volume_ratio'].iloc[i] > 0.8):
                signals[i] = 1
            
            # Short signal - overbought conditions
            elif (df['rsi'].iloc[i] > rsi_upper and
                  df['close'].iloc[i] > df['bollinger_upper'].iloc[i] and
                  df['volume_ratio'].iloc[i] > 0.8):
                signals[i] = -1
        
        return signals
    
    def _momentum_strategy(self, df, params=None):
        """Momentum strategy using MACD and moving averages"""
        signals = np.zeros(len(df))
        
        for i in range(1, len(df)):
            # Long signal - bullish momentum
            if (df['macd'].iloc[i] > df['macd_signal'].iloc[i] and
                df['macd'].iloc[i-1] <= df['macd_signal'].iloc[i-1] and
                df['close'].iloc[i] > df['sma_20'].iloc[i] and
                df['sma_20'].iloc[i] > df['sma_50'].iloc[i]):
                signals[i] = 1
            
            # Short signal - bearish momentum
            elif (df['macd'].iloc[i] < df['macd_signal'].iloc[i] and
                  df['macd'].iloc[i-1] >= df['macd_signal'].iloc[i-1] and
                  df['close'].iloc[i] < df['sma_20'].iloc[i] and
                  df['sma_20'].iloc[i] < df['sma_50'].iloc[i]):
                signals[i] = -1
        
        return signals
    
    def _scalping_strategy(self, df, params=None):
        """High-frequency scalping strategy"""
        signals = np.zeros(len(df))
        
        for i in range(2, len(df)):
            # Quick reversal patterns
            if (df['close'].iloc[i] > df['close'].iloc[i-1] and
                df['close'].iloc[i-1] < df['close'].iloc[i-2] and
                df['volume'].iloc[i] > df['volume_sma'].iloc[i] and
                df['rsi'].iloc[i] < 60):
                signals[i] = 1
            
            elif (df['close'].iloc[i] < df['close'].iloc[i-1] and
                  df['close'].iloc[i-1] > df['close'].iloc[i-2] and
                  df['volume'].iloc[i] > df['volume_sma'].iloc[i] and
                  df['rsi'].iloc[i] > 40):
                signals[i] = -1
        
        return signals
    
    def _swing_strategy(self, df, params=None):
        """Swing trading strategy for longer timeframes"""
        signals = np.zeros(len(df))
        
        for i in range(1, len(df)):
            # Strong trend following
            if (df['sma_20'].iloc[i] > df['sma_50'].iloc[i] and
                df['rsi'].iloc[i] > 50 and df['rsi'].iloc[i] < 70 and
                df['macd_histogram'].iloc[i] > 0 and
                df['atr'].iloc[i] > df['atr'].iloc[i-1]):
                signals[i] = 1
            
            elif (df['sma_20'].iloc[i] < df['sma_50'].iloc[i] and
                  df['rsi'].iloc[i] < 50 and df['rsi'].iloc[i] > 30 and
                  df['macd_histogram'].iloc[i] < 0 and
                  df['atr'].iloc[i] > df['atr'].iloc[i-1]):
                signals[i] = -1
        
        return signals
    
    def _combo_strategy(self, df, params=None):
        """Combination of multiple strategies"""
        # Get signals from each strategy
        breakout_signals = self._breakout_strategy(df)
        mean_rev_signals = self._mean_reversion_strategy(df)
        momentum_signals = self._momentum_strategy(df)
        
        # Combine signals with weights
        signals = np.zeros(len(df))
        
        for i in range(len(df)):
            combined = (
                breakout_signals[i] * 0.4 +
                mean_rev_signals[i] * 0.3 +
                momentum_signals[i] * 0.3
            )
            
            # Generate signal if strong consensus
            if combined >= 0.6:
                signals[i] = 1
            elif combined <= -0.6:
                signals[i] = -1
        
        return signals
    
    def update_strategy(self, symbol, params):
        """Update strategy parameters for a symbol"""
        self.strategy_params[symbol] = params
        logger.info(f"Updated strategy parameters for {symbol}")
    
    def backtest_metrics(self, signals, prices):
        """Calculate backtest performance metrics"""
        try:
            if len(signals) != len(prices):
                raise ValueError("Signals and prices length mismatch")
            
            # Calculate returns
            returns = []
            position = 0
            
            for i in range(1, len(signals)):
                if signals[i-1] != 0:
                    position = signals[i-1]
                
                if position != 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1] * position
                    returns.append(ret)
                else:
                    returns.append(0)
            
            if not returns:
                return {
                    "total_return": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "win_rate": 0
                }
            
            # Calculate metrics
            returns = np.array(returns)
            total_return = np.sum(returns)
            
            if np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            # Calculate drawdown
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # Win rate
            winning_trades = np.sum(returns > 0)
            total_trades = np.sum(returns != 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate
            }
            
        except Exception as e:
            logger.error(f"Backtest metrics calculation failed: {e}")
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0
            }

# Create singleton instance
strategies = TradingStrategies()
