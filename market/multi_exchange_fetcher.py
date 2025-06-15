# market/multi_exchange_fetcher.py
"""
Arasaka Multi-Exchange Data Fetcher - Jacks data from all configured exchanges
"""
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config.exchange_manager import exchange_manager
from core.database import db
from utils.logger import logger

class MultiExchangeFetcher:
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self._initialized = False
        self._exchange_configs = {}
        
    async def initialize(self):
        """Initialize all configured exchanges"""
        if self._initialized:
            return
            
        try:
            # Get all enabled exchange credentials
            credentials = exchange_manager.get_all_credentials()
            
            for cred in credentials:
                if not cred.enabled:
                    continue
                    
                try:
                    # Get exchange class
                    if not hasattr(ccxt, cred.exchange):
                        logger.warning(f"Exchange {cred.exchange} not supported by CCXT")
                        continue
                    
                    exchange_class = getattr(ccxt, cred.exchange)
                    config = exchange_manager.get_exchange_config(cred.exchange)
                    
                    # Build exchange configuration
                    exchange_config = {
                        "apiKey": cred.api_key,
                        "secret": cred.api_secret,
                        "enableRateLimit": True,
                        "rateLimit": config.get("rate_limit", 100)
                    }
                    
                    # Add exchange-specific configurations
                    if cred.exchange == "coinbase":
                        exchange_config["password"] = cred.api_passphrase
                        if cred.testnet:
                            exchange_config["urls"] = {
                                "api": config["testnet_url"]
                            }
                    
                    elif cred.exchange == "bybit":
                        if cred.subaccount:
                            exchange_config["headers"] = {
                                "referer": cred.subaccount
                            }
                        if cred.testnet:
                            exchange_config["urls"] = {
                                "api": config["testnet_url"]
                            }
                    
                    # Create exchange instance
                    exchange = exchange_class(exchange_config)
                    
                    # Set testnet mode for exchanges that support it
                    if cred.testnet and hasattr(exchange, 'set_sandbox_mode'):
                        exchange.set_sandbox_mode(True)
                    
                    self.exchanges[cred.exchange] = exchange
                    self._exchange_configs[cred.exchange] = config
                    
                    logger.info(f"Initialized {cred.exchange} exchange ({'testnet' if cred.testnet else 'live'} mode)")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {cred.exchange}: {e}")
                    continue
            
            self._initialized = True
            
            # Start preloading data
            if self.exchanges:
                asyncio.create_task(self.preload_all_exchanges())
            
        except Exception as e:
            logger.error(f"Multi-exchange initialization failed: {e}")
    
    async def preload_all_exchanges(self):
        """Preload data from all exchanges"""
        try:
            tasks = []
            for exchange_name, exchange in self.exchanges.items():
                tasks.append(self._preload_exchange_data(exchange_name, exchange))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Preload all exchanges failed: {e}")
    
    async def _preload_exchange_data(self, exchange_name: str, exchange: ccxt.Exchange):
        """Preload data for a single exchange"""
        try:
            await exchange.load_markets()
            
            # Get appropriate pairs for each exchange
            pairs = self._get_top_pairs_for_exchange(exchange_name, exchange)
            
            for symbol in pairs[:5]:  # Limit to top 5 pairs
                try:
                    data = await self.fetch_ohlcv(symbol, "1h", limit=100, exchange=exchange_name)
                    if data:
                        logger.info(f"Preloaded {len(data)} candles for {exchange_name}:{symbol}")
                except Exception as e:
                    logger.error(f"Failed to preload {symbol} from {exchange_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Preload failed for {exchange_name}: {e}")
    
    def _get_top_pairs_for_exchange(self, exchange_name: str, exchange: ccxt.Exchange) -> List[str]:
        """Get top trading pairs for specific exchange"""
        all_symbols = list(exchange.markets.keys())
        active_symbols = [s for s in all_symbols if exchange.markets[s]["active"]]
        
        # Exchange-specific top pairs
        exchange_pairs = {
            "coinbase": ["BTC/USD", "ETH/USD", "SOL/USD", "MATIC/USD", "AVAX/USD"],
            "kraken": ["BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD"],
            "bitstamp": ["BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD", "BCH/USD"],
            "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
            "bitvavo": ["BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "DOT-EUR"],
            "binance": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
        }
        
        preferred_pairs = exchange_pairs.get(exchange_name, [])
        return [p for p in preferred_pairs if p in active_symbols]
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100, 
                         since: Optional[int] = None, exchange: Optional[str] = None) -> List:
        """Fetch OHLCV data from specific exchange or best available"""
        await self.initialize()
        
        if exchange and exchange in self.exchanges:
            # Fetch from specific exchange
            return await self._fetch_from_exchange(exchange, symbol, timeframe, limit, since)
        else:
            # Try to fetch from any available exchange
            for ex_name, ex in self.exchanges.items():
                try:
                    data = await self._fetch_from_exchange(ex_name, symbol, timeframe, limit, since)
                    if data:
                        return data
                except:
                    continue
            
            # Fallback to cached or simulated data
            return self._get_cached_data(symbol, exchange or list(self.exchanges.keys())[0] if self.exchanges else "unknown", limit)
    
    async def _fetch_from_exchange(self, exchange_name: str, symbol: str, 
                                   timeframe: str, limit: int, since: Optional[int]) -> List:
        """Fetch OHLCV from specific exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            
            if not exchange.markets:
                await exchange.load_markets()
            
            # Check if symbol exists
            if symbol not in exchange.markets:
                logger.warning(f"Symbol {symbol} not found on {exchange_name}")
                return []
            
            # Fetch data
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
            
            # Store in database
            if ohlcv:
                db.store_historical_data(f"{exchange_name}:{symbol}", ohlcv)
            
            return ohlcv
            
        except Exception as e:
            logger.error(f"OHLCV fetch failed from {exchange_name}: {e}")
            return []
    
    async def fetch_tickers_all_exchanges(self) -> Dict[str, Dict]:
        """Fetch tickers from all exchanges for arbitrage detection"""
        await self.initialize()
        
        all_tickers = {}
        
        async def fetch_exchange_tickers(exchange_name: str, exchange: ccxt.Exchange):
            try:
                tickers = await exchange.fetch_tickers()
                return exchange_name, tickers
            except Exception as e:
                logger.error(f"Failed to fetch tickers from {exchange_name}: {e}")
                return exchange_name, {}
        
        # Fetch tickers from all exchanges in parallel
        tasks = [fetch_exchange_tickers(name, ex) for name, ex in self.exchanges.items()]
        results = await asyncio.gather(*tasks)
        
        for exchange_name, tickers in results:
            all_tickers[exchange_name] = tickers
        
        return all_tickers
    
    async def find_arbitrage_opportunities(self, min_profit_percent: float = 0.5) -> List[Dict]:
        """Find arbitrage opportunities across all exchanges"""
        all_tickers = await self.fetch_tickers_all_exchanges()
        opportunities = []
        
        # Find common symbols across exchanges
        symbol_exchanges = {}
        for exchange, tickers in all_tickers.items():
            for symbol in tickers:
                if symbol not in symbol_exchanges:
                    symbol_exchanges[symbol] = []
                symbol_exchanges[symbol].append(exchange)
        
        # Check for arbitrage opportunities
        for symbol, exchanges in symbol_exchanges.items():
            if len(exchanges) < 2:
                continue
            
            prices = {}
            for exchange in exchanges:
                ticker = all_tickers[exchange].get(symbol)
                if ticker and ticker.get('bid') and ticker.get('ask'):
                    prices[exchange] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'volume': ticker.get('quoteVolume', 0)
                    }
            
            # Find best arbitrage opportunity for this symbol
            for buy_exchange, buy_data in prices.items():
                for sell_exchange, sell_data in prices.items():
                    if buy_exchange == sell_exchange:
                        continue
                    
                    # Calculate profit
                    buy_price = buy_data['ask']
                    sell_price = sell_data['bid']
                    
                    if buy_price > 0 and sell_price > buy_price:
                        # Account for fees
                        buy_fee = self._exchange_configs[buy_exchange].get('fee_taker', 0.001)
                        sell_fee = self._exchange_configs[sell_exchange].get('fee_taker', 0.001)
                        
                        profit_percent = ((sell_price / buy_price) - 1 - buy_fee - sell_fee) * 100
                        
                        if profit_percent >= min_profit_percent:
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': buy_exchange,
                                'sell_exchange': sell_exchange,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'profit_percent': profit_percent,
                                'volume': min(buy_data['volume'], sell_data['volume'])
                            })
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        
        return opportunities
    
    async def execute_arbitrage(self, opportunity: Dict, amount: float) -> Tuple[bool, str]:
        """Execute an arbitrage trade"""
        try:
            symbol = opportunity['symbol']
            buy_exchange = self.exchanges[opportunity['buy_exchange']]
            sell_exchange = self.exchanges[opportunity['sell_exchange']]
            
            # Execute buy order
            buy_order = await buy_exchange.create_market_buy_order(symbol, amount)
            logger.info(f"Arbitrage buy executed on {opportunity['buy_exchange']}: {buy_order['id']}")
            
            # Execute sell order
            sell_order = await sell_exchange.create_market_sell_order(symbol, amount)
            logger.info(f"Arbitrage sell executed on {opportunity['sell_exchange']}: {sell_order['id']}")
            
            # Calculate actual profit
            buy_cost = buy_order['cost'] if 'cost' in buy_order else buy_order['price'] * amount
            sell_revenue = sell_order['cost'] if 'cost' in sell_order else sell_order['price'] * amount
            actual_profit = sell_revenue - buy_cost
            
            return True, f"Arbitrage executed! Profit: ${actual_profit:.2f}"
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            return False, str(e)
    
    async def get_best_exchange_for_pair(self, symbol: str) -> Optional[str]:
        """Find best exchange for a trading pair based on liquidity and fees"""
        best_exchange = None
        best_score = -float('inf')
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                if not exchange.markets:
                    await exchange.load_markets()
                
                if symbol not in exchange.markets:
                    continue
                
                # Get order book depth
                order_book = await exchange.fetch_order_book(symbol, limit=10)
                
                # Calculate liquidity score
                bid_liquidity = sum(bid[1] * bid[0] for bid in order_book['bids'][:5])
                ask_liquidity = sum(ask[1] * ask[0] for ask in order_book['asks'][:5])
                total_liquidity = bid_liquidity + ask_liquidity
                
                # Get spread
                if order_book['bids'] and order_book['asks']:
                    spread = (order_book['asks'][0][0] - order_book['bids'][0][0]) / order_book['bids'][0][0]
                else:
                    spread = float('inf')
                
                # Get fees
                config = self._exchange_configs[exchange_name]
                fee = (config.get('fee_maker', 0.001) + config.get('fee_taker', 0.001)) / 2
                
                # Calculate score (higher is better)
                score = total_liquidity / (1 + spread + fee)
                
                if score > best_score:
                    best_score = score
                    best_exchange = exchange_name
                    
            except Exception as e:
                logger.error(f"Failed to evaluate {exchange_name} for {symbol}: {e}")
                continue
        
        return best_exchange
    
    def _get_cached_data(self, symbol: str, exchange: str, limit: int) -> List:
        """Get cached data from database"""
        try:
            data = db.fetch_all(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%:{symbol}", limit)
            )
            
            if data:
                ohlcv = [[d[0], d[1], d[2], d[3], d[4], d[5]] for d in reversed(data)]
                return ohlcv
            else:
                return self._simulate_ohlcv(limit)
                
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return self._simulate_ohlcv(limit)
    
    def _simulate_ohlcv(self, limit: int) -> List:
        """Generate simulated OHLCV data"""
        logger.warning("Generating simulated OHLCV data")
        
        now = datetime.now()
        timestamps = []
        for i in range(limit):
            ts = now - timedelta(hours=i)
            timestamps.append(int(ts.timestamp() * 1000))
        timestamps.reverse()
        
        base_price = 50000
        volatility = 0.02
        trend = 0.0001
        
        data = []
        current_price = base_price
        
        for i, ts in enumerate(timestamps):
            change = np.random.normal(trend, volatility)
            current_price *= (1 + change)
            
            high = current_price * (1 + abs(np.random.normal(0, volatility/2)))
            low = current_price * (1 - abs(np.random.normal(0, volatility/2)))
            open_price = current_price * (1 + np.random.normal(0, volatility/3))
            
            high = max(high, open_price, current_price)
            low = min(low, open_price, current_price)
            
            volume = np.random.uniform(100, 1000) * (1 - i/limit)
            
            data.append([ts, open_price, high, low, current_price, volume])
        
        return data
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed {exchange_name} connection")
            except Exception as e:
                logger.error(f"Error closing {exchange_name}: {e}")

# Create singleton instance
multi_fetcher = MultiExchangeFetcher()
