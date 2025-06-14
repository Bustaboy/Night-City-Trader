# market/data_fetcher.py
"""
Arasaka Data Fetcher - Jacks market data from exchanges into the Neural-Net
"""
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta

from config.settings import settings
from core.database import db
from utils.logger import logger

class DataFetcher:
    def __init__(self):
        self.exchanges = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize exchanges"""
        if self._initialized:
            return
            
        try:
            # Initialize configured exchanges
            for ex_name in settings.TRADING["exchanges"]:
                if hasattr(ccxt, ex_name):
                    exchange_class = getattr(ccxt, ex_name)
                    
                    # Configure exchange
                    config = {
                        "enableRateLimit": True,
                        "rateLimit": 1200,  # requests per minute
                        "options": {
                            "defaultType": "spot"
                        }
                    }
                    
                    # Add API keys for Binance
                    if ex_name == "binance":
                        config["apiKey"] = settings.BINANCE_API_KEY
                        config["secret"] = settings.BINANCE_API_SECRET
                    
                    # Create exchange instance
                    exchange = exchange_class(config)
                    
                    # Set testnet mode
                    if settings.TESTNET:
                        exchange.set_sandbox_mode(True)
                    
                    self.exchanges[ex_name] = exchange
                    logger.info(f"Initialized {ex_name} exchange")
            
            self._initialized = True
            
            # Preload some historical data
            asyncio.create_task(self.preload_historical_data())
            
        except Exception as e:
            logger.error(f"Exchange initialization flatlined: {e}")
    
    async def preload_historical_data(self):
        """Preload historical data for configured pairs"""
        try:
            logger.info("Starting historical data preload...")
            
            for ex_name, exchange in self.exchanges.items():
                try:
                    await exchange.load_markets()
                    
                    # Get USDT pairs
                    pairs = [
                        symbol for symbol in exchange.markets.keys()
                        if symbol.endswith("/USDT") and exchange.markets[symbol]["active"]
                    ]
                    
                    # Limit to top pairs
                    top_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
                    pairs_to_load = [p for p in top_pairs if p in pairs][:5]
                    
                    for symbol in pairs_to_load:
                        try:
                            # Fetch recent data
                            data = await self.fetch_ohlcv(
                                symbol,
                                settings.TRADING["timeframe"],
                                limit=1000,
                                exchange=ex_name
                            )
                            
                            if data:
                                logger.info(f"Preloaded {len(data)} candles for {ex_name}:{symbol}")
                                
                        except Exception as e:
                            logger.error(f"Failed to preload {symbol}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Market loading failed for {ex_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Historical data preload flatlined: {e}")
    
    async def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None, exchange="binance"):
        """Fetch OHLCV data from exchange or database"""
        await self.initialize()
        
        try:
            if exchange not in self.exchanges:
                logger.warning(f"Exchange {exchange} not configured")
                exchange = "binance"  # Fallback
            
            ex = self.exchanges.get(exchange)
            if not ex:
                logger.error(f"No exchange available")
                return self._get_cached_data(symbol, exchange, limit)
            
            # Load markets if needed
            if not ex.markets:
                await ex.load_markets()
            
            # Check if symbol exists
            if symbol not in ex.markets:
                logger.warning(f"Symbol {symbol} not found on {exchange}")
                return self._get_cached_data(symbol, exchange, limit)
            
            # Fetch from exchange
            ohlcv = await ex.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            
            # Store in database
            if ohlcv:
                db.store_historical_data(f"{exchange}:{symbol}", ohlcv)
                
                # Also store in market_data table for recent access
                for candle in ohlcv[-20:]:  # Last 20 candles
                    db.execute_query(
                        """
                        INSERT OR REPLACE INTO market_data
                        (symbol, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (f"{exchange}:{symbol}", candle[0], candle[1], candle[2], 
                         candle[3], candle[4], candle[5])
                    )
            
            logger.info(f"Fetched {len(ohlcv)} candles for {exchange}:{symbol}")
            return ohlcv
            
        except Exception as e:
            logger.error(f"OHLCV fetch failed: {e}")
            return self._get_cached_data(symbol, exchange, limit)
    
    def _get_cached_data(self, symbol, exchange, limit):
        """Get cached data from database"""
        try:
            # Try historical_data table first
            data = db.fetch_all(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"{exchange}:{symbol}", limit)
            )
            
            if not data:
                # Try market_data table
                data = db.fetch_all(
                    """
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"{exchange}:{symbol}", limit)
                )
            
            if data:
                # Convert to OHLCV format and reverse order
                ohlcv = [[d[0], d[1], d[2], d[3], d[4], d[5]] for d in reversed(data)]
                logger.info(f"Retrieved {len(ohlcv)} cached candles for {exchange}:{symbol}")
                return ohlcv
            else:
                logger.warning(f"No cached data for {exchange}:{symbol}, using simulated")
                return self.simulate_ohlcv(limit)
                
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return self.simulate_ohlcv(limit)
    
    async def fetch_historical_data(self, exchange, symbol, timeframe, years=5):
        """Fetch multiple years of historical data"""
        await self.initialize()
        
        try:
            if exchange not in self.exchanges:
                logger.error(f"Exchange {exchange} not configured")
                return []
            
            ex = self.exchanges[exchange]
            await ex.load_markets()
            
            # Calculate time range
            now = datetime.now()
            since_date = now - timedelta(days=365 * years)
            since = int(since_date.timestamp() * 1000)
            
            all_data = []
            
            # Fetch in chunks
            while since < int(now.timestamp() * 1000):
                try:
                    data = await ex.fetch_ohlcv(
                        symbol,
                        timeframe,
                        since=since,
                        limit=1000
                    )
                    
                    if not data:
                        break
                    
                    all_data.extend(data)
                    
                    # Update since to last candle timestamp
                    since = data[-1][0] + 1
                    
                    # Rate limit protection
                    await asyncio.sleep(ex.rateLimit / 1000)
                    
                except Exception as e:
                    logger.error(f"Historical fetch error: {e}")
                    break
            
            # Store in database
            if all_data:
                db.store_historical_data(f"{exchange}:{symbol}", all_data)
            
            logger.info(f"Fetched {len(all_data)} historical candles for {exchange}:{symbol}")
            return all_data
            
        except Exception as e:
            logger.error(f"Historical data fetch flatlined: {e}")
            return []
    
    async def fetch_order_book(self, symbol, exchange="binance"):
        """Fetch order book data"""
        await self.initialize()
        
        try:
            if exchange not in self.exchanges:
                logger.warning(f"Exchange {exchange} not configured")
                return {"bids": [], "asks": []}
            
            ex = self.exchanges[exchange]
            
            if not ex.markets:
                await ex.load_markets()
            
            # Fetch order book
            book = await ex.fetch_order_book(symbol, limit=10)
            
            logger.info(f"Fetched order book for {exchange}:{symbol}")
            return book
            
        except Exception as e:
            logger.error(f"Order book fetch failed: {e}")
            return {"bids": [], "asks": []}
    
    async def fetch_ticker(self, symbol, exchange="binance"):
        """Fetch ticker data"""
        await self.initialize()
        
        try:
            if exchange not in self.exchanges:
                return None
            
            ex = self.exchanges[exchange]
            
            if not ex.markets:
                await ex.load_markets()
            
            ticker = await ex.fetch_ticker(symbol)
            return ticker
            
        except Exception as e:
            logger.error(f"Ticker fetch failed: {e}")
            return None
    
    def simulate_ohlcv(self, limit):
        """Generate simulated OHLCV data for testing"""
        logger.warning("Generating simulated OHLCV data")
        
        # Generate timestamps
        now = datetime.now()
        timestamps = []
        for i in range(limit):
            ts = now - timedelta(hours=i)
            timestamps.append(int(ts.timestamp() * 1000))
        timestamps.reverse()
        
        # Generate price data
        base_price = 50000  # Starting BTC price
        volatility = 0.02
        trend = 0.0001
        
        data = []
        current_price = base_price
        
        for i, ts in enumerate(timestamps):
            # Random walk with trend
            change = np.random.normal(trend, volatility)
            current_price *= (1 + change)
            
            # Generate OHLC from close
            high = current_price * (1 + abs(np.random.normal(0, volatility/2)))
            low = current_price * (1 - abs(np.random.normal(0, volatility/2)))
            open_price = current_price * (1 + np.random.normal(0, volatility/3))
            
            # Ensure logical order
            high = max(high, open_price, current_price)
            low = min(low, open_price, current_price)
            
            # Volume (decreasing with age)
            volume = np.random.uniform(100, 1000) * (1 - i/limit)
            
            data.append([ts, open_price, high, low, current_price, volume])
        
        return data
    
    def set_sandbox_mode(self, enabled):
        """Toggle sandbox mode for all exchanges"""
        for ex in self.exchanges.values():
            ex.set_sandbox_mode(enabled)
        logger.info(f"Sandbox mode {'enabled' if enabled else 'disabled'} for all exchanges")
    
    async def close(self):
        """Close all exchange connections"""
        for ex_name, ex in self.exchanges.items():
            try:
                await ex.close()
                logger.info(f"Closed {ex_name} connection")
            except Exception as e:
                logger.error(f"Error closing {ex_name}: {e}")

# Create singleton instance
fetcher = DataFetcher()
