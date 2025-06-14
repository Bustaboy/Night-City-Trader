# market/pair_selector.py
"""
Arasaka Pair Selector - Finds the most profitable trading pairs in the Net
"""
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import asyncio

from config.settings import settings
from core.database import db
from utils.logger import logger

class PairSelector:
    def __init__(self):
        self.exchanges = {}
        self._initialized = False
        self.ml_trainer = None
        self.rl_trainer = None
        self.fetcher = None
    
    async def initialize(self):
        """Initialize exchanges and dependencies"""
        if self._initialized:
            return
            
        try:
            # Import dependencies
            from ml.trainer import trainer
            from ml.rl_trainer import rl_trainer
            from market.data_fetcher import fetcher
            
            self.ml_trainer = trainer
            self.rl_trainer = rl_trainer
            self.fetcher = fetcher
            
            # Initialize exchanges
            for ex_name in settings.TRADING["exchanges"]:
                if hasattr(ccxt, ex_name):
                    exchange_class = getattr(ccxt, ex_name)
                    
                    config = {
                        "enableRateLimit": True,
                        "rateLimit": 1200
                    }
                    
                    if ex_name == "binance":
                        config["apiKey"] = settings.BINANCE_API_KEY
                        config["secret"] = settings.BINANCE_API_SECRET
                    
                    exchange = exchange_class(config)
                    
                    if settings.TESTNET:
                        exchange.set_sandbox_mode(True)
                    
                    self.exchanges[ex_name] = exchange
            
            self._initialized = True
            logger.info("Pair selector initialized")
            
        except Exception as e:
            logger.error(f"Pair selector initialization flatlined: {e}")
    
    async def select_best_pair(self, timeframe, limit=100):
        """Select the best trading pair based on multiple factors"""
        await self.initialize()
        
        try:
            best_pair = None
            best_score = -float('inf')
            
            for ex_name, exchange in self.exchanges.items():
                try:
                    # Load markets
                    await exchange.load_markets()
                    
                    # Get active USDT pairs
                    pairs = [
                        symbol for symbol in exchange.markets.keys()
                        if symbol.endswith("/USDT") and exchange.markets[symbol]["active"]
                    ]
                    
                    # Limit to top pairs for performance
                    top_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT", 
                                "DOGE/USDT", "XRP/USDT", "DOT/USDT", "MATIC/USDT", "SHIB/USDT"]
                    pairs_to_check = [p for p in top_pairs if p in pairs][:10]
                    
                    for pair in pairs_to_check:
                        try:
                            score = await self._evaluate_pair(ex_name, pair, timeframe, limit)
                            
                            if score > best_score:
                                best_score = score
                                best_pair = f"{ex_name}:{pair}"
                                
                        except Exception as e:
                            logger.error(f"Failed to evaluate {pair}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Market loading failed for {ex_name}: {e}")
                    continue
            
            if best_pair:
                logger.info(f"Selected best pair: {best_pair} (score: {best_score:.4f})")
                return best_pair
            else:
                logger.warning("No suitable pair found, using default")
                return f"binance:{settings.TRADING['symbol']}"
                
        except Exception as e:
            logger.error(f"Pair selection flatlined: {e}")
            return f"binance:{settings.TRADING['symbol']}"
    
    async def _evaluate_pair(self, exchange_name, pair, timeframe, limit):
        """Evaluate a trading pair's potential"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Get ticker data
            ticker = await exchange.fetch_ticker(pair)
            
            # Check basic requirements
            volume = ticker.get("quoteVolume", 0)
            if volume < settings.TRADING["pair_selection"]["min_volume"]:
                return -float('inf')
            
            # Get order book for spread calculation
            book = await exchange.fetch_order_book(pair, limit=5)
            
            if book["bids"] and book["asks"]:
                spread = (book["asks"][0][0] - book["bids"][0][0]) / book["bids"][0][0]
                if spread > settings.TRADING["pair_selection"]["max_spread"]:
                    return -float('inf')
            else:
                spread = 0.001  # Default spread
            
            # Calculate liquidity
            liquidity = 0
            if book["bids"]:
                liquidity += sum(bid[0] * bid[1] for bid in book["bids"][:5])
            if book["asks"]:
                liquidity += sum(ask[0] * ask[1] for ask in book["asks"][:5])
            
            if liquidity < settings.TRADING["pair_selection"]["min_liquidity"]:
                return -float('inf')
            
            # Get historical data for volatility
            data = await self.fetcher.fetch_ohlcv(pair, timeframe, limit=limit, exchange=exchange_name)
            
            if not data or len(data) < 20:
                return -float('inf')
            
            # Calculate volatility
            prices = [candle[4] for candle in data]  # Close prices
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
            
            if volatility < settings.TRADING["pair_selection"]["min_volatility"]:
                return -float('inf')
            
            # Calculate volume spike
            recent_volume = ticker.get("quoteVolume", 0)
            avg_volume = np.mean([candle[5] for candle in data[-24:]])  # Last 24 periods
            volume_spike = (recent_volume / avg_volume - 1) if avg_volume > 0 else 0
            
            # Get ML predictions
            ml_prediction = 0.5
            rl_score = 0.5
            
            if self.ml_trainer and self.rl_trainer and data:
                try:
                    ml_prediction = self.ml_trainer.predict(data[-1])
                    rl_score = self.rl_trainer.predict(data[-1])
                except:
                    pass
            
            # Calculate composite score
            score = (
                (ml_prediction * 0.3) +
                (rl_score * 0.3) +
                (volatility * 100 * 0.2) +
                (volume / 1e9 * 0.1) +
                (1 / (spread + 0.001) * 0.05) +
                (min(volume_spike, 1) * 0.05)
            )
            
            # Boost score for liquidity
            score *= (1 + min(liquidity / 1e6, 1))
            
            logger.info(f"Evaluated {exchange_name}:{pair} - Score: {score:.4f}, Vol: {volatility:.4f}, Volume: ${volume/1e6:.1f}M")
            
            return score
            
        except Exception as e:
            logger.error(f"Pair evaluation failed for {pair}: {e}")
            return -float('inf')
    
    async def auto_rotate_pairs(self):
        """Automatically rotate trading pairs based on performance"""
        await self.initialize()
        
        try:
            profitable_pairs = {}
            
            # Analyze existing trades
            for ex_name in self.exchanges.keys():
                trades = db.fetch_all(
                    """
                    SELECT symbol, 
                           SUM(CASE WHEN side = 'sell' THEN amount * price - fee
                                    WHEN side = 'buy' THEN -(amount * price + fee)
                                    ELSE 0 END) as profit
                    FROM trades 
                    WHERE symbol LIKE ?
                    GROUP BY symbol
                    """,
                    (f"{ex_name}:%",)
                )
                
                portfolio_value = db.get_portfolio_value()
                profit_threshold = 0.01 * portfolio_value  # 1% of portfolio
                
                for symbol, profit in trades:
                    if profit and profit > profit_threshold:
                        profitable_pairs[symbol] = profit
            
            # Evaluate new pairs
            for ex_name, exchange in self.exchanges.items():
                try:
                    await exchange.load_markets()
                    
                    pairs = [
                        symbol for symbol in exchange.markets.keys()
                        if symbol.endswith("/USDT") and exchange.markets[symbol]["active"]
                    ]
                    
                    for pair in pairs[:20]:  # Check top 20 pairs
                        full_symbol = f"{ex_name}:{pair}"
                        
                        if full_symbol not in profitable_pairs:
                            score = await self._evaluate_pair(ex_name, pair, "1h", 100)
                            
                            if score > 0.5:  # Minimum score threshold
                                profitable_pairs[full_symbol] = score * 1000  # Convert to profit estimate
                                
                except Exception as e:
                    logger.error(f"Failed to evaluate new pairs for {ex_name}: {e}")
            
            # Sort by profitability
            sorted_pairs = sorted(profitable_pairs.items(), key=lambda x: x[1], reverse=True)
            top_pairs = [pair for pair, _ in sorted_pairs[:10]]
            
            if not top_pairs:
                top_pairs = [f"binance:{settings.TRADING['symbol']}"]
            
            logger.info(f"Auto-rotated pairs: {top_pairs}")
            return top_pairs
            
        except Exception as e:
            logger.error(f"Pair rotation flatlined: {e}")
            return [f"binance:{settings.TRADING['symbol']}"]
    
    async def detect_arbitrage(self):
        """Detect arbitrage opportunities across exchanges"""
        await self.initialize()
        
        try:
            opportunities = []
            
            # Get common pairs across exchanges
            common_pairs = set()
            
            for exchange in self.exchanges.values():
                try:
                    await exchange.load_markets()
                    pairs = set(
                        symbol for symbol in exchange.markets.keys()
                        if symbol.endswith("/USDT") and exchange.markets[symbol]["active"]
                    )
                    
                    if not common_pairs:
                        common_pairs = pairs
                    else:
                        common_pairs = common_pairs.intersection(pairs)
                        
                except Exception as e:
                    logger.error(f"Failed to load markets: {e}")
            
            # Check top pairs for arbitrage
            pairs_to_check = list(common_pairs)[:20]
            
            for pair in pairs_to_check:
                try:
                    prices = {}
                    
                    # Get prices from all exchanges
                    for ex_name, exchange in self.exchanges.items():
                        try:
                            ticker = await exchange.fetch_ticker(pair)
                            prices[ex_name] = {
                                "bid": ticker.get("bid", 0),
                                "ask": ticker.get("ask", 0)
                            }
                        except:
                            continue
                    
                    # Find arbitrage opportunities
                    for buy_ex, buy_prices in prices.items():
                        for sell_ex, sell_prices in prices.items():
                            if buy_ex != sell_ex and buy_prices["ask"] > 0 and sell_prices["bid"] > 0:
                                # Calculate profit percentage
                                profit_pct = (sell_prices["bid"] / buy_prices["ask"] - 1)
                                
                                # Account for fees
                                total_fees = 2 * settings.TRADING["fees"]["taker"]
                                net_profit = profit_pct - total_fees
                                
                                if net_profit > 0.001:  # 0.1% minimum profit
                                    opportunities.append({
                                        "pair": pair,
                                        "buy_exchange": buy_ex,
                                        "sell_exchange": sell_ex,
                                        "buy_price": buy_prices["ask"],
                                        "sell_price": sell_prices["bid"],
                                        "profit": net_profit
                                    })
                    
                except Exception as e:
                    logger.error(f"Failed to check arbitrage for {pair}: {e}")
            
            # Sort by profit
            opportunities.sort(key=lambda x: x["profit"], reverse=True)
            
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Arbitrage detection flatlined: {e}")
            return []
    
    def set_sandbox_mode(self, enabled):
        """Toggle sandbox mode for all exchanges"""
        for exchange in self.exchanges.values():
            exchange.set_sandbox_mode(enabled)
        logger.info(f"Pair selector sandbox mode {'enabled' if enabled else 'disabled'}")
    
    async def close(self):
        """Close all exchange connections"""
        for ex_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed {ex_name} connection in pair selector")
            except Exception as e:
                logger.error(f"Error closing {ex_name}: {e}")

# Create singleton instance
pair_selector = PairSelector()
