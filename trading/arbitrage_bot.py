# trading/arbitrage_bot.py
"""
Arasaka Cross-Exchange Arbitrage Bot - Finds and executes profitable trades across exchanges
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from market.multi_exchange_fetcher import multi_fetcher
from trading.risk_manager import risk_manager
from config.exchange_manager import exchange_manager
from core.database import db
from utils.logger import logger

class ArbitrageBot:
    def __init__(self):
        self.active = False
        self.min_profit_percent = 0.5  # Minimum 0.5% profit after fees
        self.max_position_size = 0.1  # Max 10% of portfolio per trade
        self.execution_delay = 0.1  # Seconds between orders
        self.monitored_pairs = []
        
    async def initialize(self):
        """Initialize arbitrage bot"""
        try:
            # Initialize multi-exchange fetcher
            await multi_fetcher.initialize()
            
            # Get common pairs across exchanges
            self.monitored_pairs = await self._get_common_pairs()
            
            logger.info(f"Arbitrage bot initialized with {len(self.monitored_pairs)} pairs")
            
        except Exception as e:
            logger.error(f"Arbitrage bot initialization failed: {e}")
    
    async def _get_common_pairs(self) -> List[str]:
        """Get trading pairs available on multiple exchanges"""
        exchange_pairs = {}
        
        for exchange_name, exchange in multi_fetcher.exchanges.items():
            try:
                if not exchange.markets:
                    await exchange.load_markets()
                
                # Get active pairs
                pairs = [symbol for symbol, market in exchange.markets.items() 
                        if market['active']]
                exchange_pairs[exchange_name] = set(pairs)
                
            except Exception as e:
                logger.error(f"Failed to get pairs from {exchange_name}: {e}")
        
        # Find pairs available on at least 2 exchanges
        all_pairs = set()
        for pairs in exchange_pairs.values():
            all_pairs.update(pairs)
        
        common_pairs = []
        for pair in all_pairs:
            exchanges_with_pair = sum(1 for pairs in exchange_pairs.values() if pair in pairs)
            if exchanges_with_pair >= 2:
                common_pairs.append(pair)
        
        # Prioritize major pairs
        priority_bases = ['BTC', 'ETH', 'SOL', 'ADA', 'MATIC']
        common_pairs.sort(key=lambda x: next((i for i, base in enumerate(priority_bases) 
                                            if base in x), len(priority_bases)))
        
        return common_pairs[:50]  # Limit to top 50 pairs
    
    async def scan_opportunities(self) -> List[Dict]:
        """Scan for arbitrage opportunities"""
        opportunities = []
        
        try:
            # Get tickers from all exchanges
            all_tickers = await multi_fetcher.fetch_tickers_all_exchanges()
            
            for pair in self.monitored_pairs:
                # Normalize pair format for different exchanges
                pair_variants = self._get_pair_variants(pair)
                
                prices = {}
                for exchange, tickers in all_tickers.items():
                    for variant in pair_variants:
                        if variant in tickers:
                            ticker = tickers[variant]
                            if ticker.get('bid') and ticker.get('ask'):
                                prices[exchange] = {
                                    'pair': variant,
                                    'bid': ticker['bid'],
                                    'ask': ticker['ask'],
                                    'volume': ticker.get('quoteVolume', 0)
                                }
                            break
                
                # Find arbitrage opportunities for this pair
                pair_opportunities = self._find_pair_opportunities(pair, prices)
                opportunities.extend(pair_opportunities)
        
        except Exception as e:
            logger.error(f"Arbitrage scan failed: {e}")
        
        # Sort by profit
        opportunities.sort(key=lambda x: x['net_profit_percent'], reverse=True)
        
        return opportunities
    
    def _get_pair_variants(self, pair: str) -> List[str]:
        """Get different format variants of a trading pair"""
        variants = [pair]
        
        # Handle different formats
        if '/' in pair:
            base, quote = pair.split('/')
            variants.extend([
                f"{base}-{quote}",      # Coinbase format
                f"{base}{quote}",       # Bybit format
                f"{base}_{quote}",      # Some exchanges
                pair.replace('/', '')   # No separator
            ])
        elif '-' in pair:
            base, quote = pair.split('-')
            variants.extend([
                f"{base}/{quote}",
                f"{base}{quote}",
                f"{base}_{quote}"
            ])
        
        # Handle USDT/USD variations
        if 'USDT' in pair:
            for variant in list(variants):
                variants.append(variant.replace('USDT', 'USD'))
        elif 'USD' in pair and 'USDT' not in pair:
            for variant in list(variants):
                variants.append(variant.replace('USD', 'USDT'))
        
        return variants
    
    def _find_pair_opportunities(self, pair: str, prices: Dict) -> List[Dict]:
        """Find arbitrage opportunities for a specific pair"""
        opportunities = []
        
        exchanges = list(prices.keys())
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                buy_data = prices[buy_exchange]
                sell_data = prices[sell_exchange]
                
                # Calculate potential profit
                opportunity = self._calculate_opportunity(
                    pair, buy_exchange, sell_exchange, buy_data, sell_data
                )
                
                if opportunity['net_profit_percent'] >= self.min_profit_percent:
                    opportunities.append(opportunity)
                
                # Check reverse direction
                reverse_opportunity = self._calculate_opportunity(
                    pair, sell_exchange, buy_exchange, sell_data, buy_data
                )
                
                if reverse_opportunity['net_profit_percent'] >= self.min_profit_percent:
                    opportunities.append(reverse_opportunity)
        
        return opportunities
    
    def _calculate_opportunity(self, pair: str, buy_exchange: str, sell_exchange: str,
                              buy_data: Dict, sell_data: Dict) -> Dict:
        """Calculate arbitrage opportunity details"""
        buy_price = buy_data['ask']
        sell_price = sell_data['bid']
        
        # Get exchange fees
        buy_config = exchange_manager.get_exchange_config(buy_exchange)
        sell_config = exchange_manager.get_exchange_config(sell_exchange)
        
        buy_fee = buy_config.get('fee_taker', 0.001)
        sell_fee = sell_config.get('fee_taker', 0.001)
        
        # Calculate profit
        gross_profit_percent = ((sell_price / buy_price) - 1) * 100
        total_fees_percent = (buy_fee + sell_fee) * 100
        net_profit_percent = gross_profit_percent - total_fees_percent
        
        # Estimate max tradeable volume (conservative)
        max_volume = min(buy_data['volume'], sell_data['volume']) * 0.1  # 10% of volume
        
        return {
            'pair': pair,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'gross_profit_percent': gross_profit_percent,
            'total_fees_percent': total_fees_percent,
            'net_profit_percent': net_profit_percent,
            'max_volume': max_volume,
            'timestamp': datetime.now().isoformat()
        }
    
    async def execute_opportunity(self, opportunity: Dict, amount: Optional[float] = None) -> Tuple[bool, str]:
        """Execute an arbitrage opportunity"""
        try:
            # Validate opportunity is still valid
            current_opps = await self.scan_opportunities()
            
            # Find matching opportunity
            current_opp = None
            for opp in current_opps:
                if (opp['pair'] == opportunity['pair'] and
                    opp['buy_exchange'] == opportunity['buy_exchange'] and
                    opp['sell_exchange'] == opportunity['sell_exchange']):
                    current_opp = opp
                    break
            
            if not current_opp:
                return False, "Opportunity no longer available"
            
            if current_opp['net_profit_percent'] < self.min_profit_percent:
                return False, f"Profit too low: {current_opp['net_profit_percent']:.2f}%"
            
            # Calculate position size
            if not amount:
                portfolio_value = db.get_portfolio_value()
                max_position = portfolio_value * self.max_position_size
                amount = min(max_position / current_opp['buy_price'], current_opp['max_volume'])
            
            # Adjust amount for risk
            amount = risk_manager.adjust_position_size(opportunity['pair'], amount)
            
            if amount <= 0:
                return False, "Position size too small after risk adjustment"
            
            # Execute trades
            logger.info(f"Executing arbitrage: Buy {amount} {opportunity['pair']} on {opportunity['buy_exchange']}, "
                       f"sell on {opportunity['sell_exchange']}")
            
            # Get exchanges
            buy_exchange = multi_fetcher.exchanges[opportunity['buy_exchange']]
            sell_exchange = multi_fetcher.exchanges[opportunity['sell_exchange']]
            
            # Execute buy order first
            buy_pair = self._get_exchange_pair_format(opportunity['pair'], opportunity['buy_exchange'])
            buy_order = await buy_exchange.create_market_buy_order(buy_pair, amount)
            
            logger.info(f"Buy order executed: {buy_order['id']}")
            
            # Small delay to ensure order is filled
            await asyncio.sleep(self.execution_delay)
            
            # Execute sell order
            sell_pair = self._get_exchange_pair_format(opportunity['pair'], opportunity['sell_exchange'])
            sell_order = await sell_exchange.create_market_sell_order(sell_pair, amount)
            
            logger.info(f"Sell order executed: {sell_order['id']}")
            
            # Calculate actual profit
            buy_cost = buy_order.get('cost', buy_order.get('price', 0) * amount)
            sell_revenue = sell_order.get('cost', sell_order.get('price', 0) * amount)
            actual_profit = sell_revenue - buy_cost
            
            # Store arbitrage trade
            self._store_arbitrage_trade(opportunity, buy_order, sell_order, actual_profit)
            
            return True, f"Arbitrage executed! Profit: ${actual_profit:.2f} ({actual_profit/buy_cost*100:.2f}%)"
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            return False, str(e)
    
    def _get_exchange_pair_format(self, pair: str, exchange: str) -> str:
        """Convert pair to exchange-specific format"""
        config = exchange_manager.get_exchange_config(exchange)
        format_example = config.get('pairs_format', '')
        
        if '/' in pair:
            base, quote = pair.split('/')
        elif '-' in pair:
            base, quote = pair.split('-')
        else:
            # Try to parse concatenated format
            for i in range(1, len(pair)):
                if pair[i:] in ['USD', 'USDT', 'EUR', 'GBP', 'BTC', 'ETH']:
                    base = pair[:i]
                    quote = pair[i:]
                    break
            else:
                return pair
        
        # Format based on exchange
        if exchange == 'coinbase':
            return f"{base}-{quote}"
        elif exchange == 'bybit':
            return f"{base}{quote}"
        elif exchange == 'bitvavo':
            return f"{base}-{quote}"
        else:
            return f"{base}/{quote}"
    
    def _store_arbitrage_trade(self, opportunity: Dict, buy_order: Dict, sell_order: Dict, profit: float):
        """Store arbitrage trade in database"""
        try:
            # Create arbitrage trades table if needed
            db.execute_query("""
                CREATE TABLE IF NOT EXISTS arbitrage_trades (
                    id TEXT PRIMARY KEY,
                    pair TEXT,
                    buy_exchange TEXT,
                    sell_exchange TEXT,
                    buy_order_id TEXT,
                    sell_order_id TEXT,
                    amount REAL,
                    buy_price REAL,
                    sell_price REAL,
                    profit REAL,
                    profit_percent REAL,
                    timestamp TEXT
                )
            """)
            
            # Store trade
            trade_id = f"arb_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            amount = buy_order.get('amount', 0)
            buy_price = buy_order.get('price', 0)
            sell_price = sell_order.get('price', 0)
            
            db.execute_query("""
                INSERT INTO arbitrage_trades 
                (id, pair, buy_exchange, sell_exchange, buy_order_id, sell_order_id,
                 amount, buy_price, sell_price, profit, profit_percent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_id,
                opportunity['pair'],
                opportunity['buy_exchange'],
                opportunity['sell_exchange'],
                buy_order.get('id', ''),
                sell_order.get('id', ''),
                amount,
                buy_price,
                sell_price,
                profit,
                (profit / (buy_price * amount) * 100) if buy_price > 0 and amount > 0 else 0,
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"Failed to store arbitrage trade: {e}")
    
    async def start_monitoring(self, scan_interval: int = 10):
        """Start continuous arbitrage monitoring"""
        self.active = True
        logger.info("Starting arbitrage monitoring...")
        
        while self.active:
            try:
                # Scan for opportunities
                opportunities = await self.scan_opportunities()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                    
                    # Log top opportunities
                    for opp in opportunities[:5]:
                        logger.info(f"{opp['pair']}: {opp['buy_exchange']} -> {opp['sell_exchange']} "
                                  f"= {opp['net_profit_percent']:.2f}% profit")
                
                # Wait before next scan
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Arbitrage monitoring error: {e}")
                await asyncio.sleep(scan_interval)
    
    def stop_monitoring(self):
        """Stop arbitrage monitoring"""
        self.active = False
        logger.info("Stopping arbitrage monitoring")
    
    async def get_statistics(self) -> Dict:
        """Get arbitrage trading statistics"""
        try:
            # Get total trades
            total_trades = db.fetch_one(
                "SELECT COUNT(*) FROM arbitrage_trades"
            )
            
            # Get profit stats
            profit_stats = db.fetch_one("""
                SELECT 
                    SUM(profit) as total_profit,
                    AVG(profit) as avg_profit,
                    MAX(profit) as best_trade,
                    MIN(profit) as worst_trade,
                    AVG(profit_percent) as avg_profit_percent
                FROM arbitrage_trades
            """)
            
            # Get exchange stats
            exchange_stats = db.fetch_all("""
                SELECT 
                    buy_exchange || ' -> ' || sell_exchange as route,
                    COUNT(*) as trades,
                    SUM(profit) as total_profit
                FROM arbitrage_trades
                GROUP BY buy_exchange, sell_exchange
                ORDER BY total_profit DESC
            """)
            
            return {
                'total_trades': total_trades[0] if total_trades else 0,
                'total_profit': profit_stats[0] if profit_stats else 0,
                'average_profit': profit_stats[1] if profit_stats else 0,
                'best_trade': profit_stats[2] if profit_stats else 0,
                'worst_trade': profit_stats[3] if profit_stats else 0,
                'average_profit_percent': profit_stats[4] if profit_stats else 0,
                'best_routes': [
                    {'route': route, 'trades': trades, 'profit': profit}
                    for route, trades, profit in exchange_stats
                ] if exchange_stats else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get arbitrage statistics: {e}")
            return {}

# Create singleton instance
arbitrage_bot = ArbitrageBot()
