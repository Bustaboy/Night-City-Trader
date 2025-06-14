# emergency/kill_switch.py
"""
Militech Kill Switch - Emergency stop for all trading operations
"""
import asyncio
import os
from datetime import datetime

from utils.logger import logger
from core.database import db

class KillSwitch:
    def __init__(self):
        self.activated = False
        self.activation_time = None
    
    async def activate(self):
        """Activate emergency kill switch"""
        try:
            logger.critical("KILL SWITCH ACTIVATED - Shutting down all systems!")
            self.activated = True
            self.activation_time = datetime.now()
            
            # Import components
            from trading.trading_bot import bot
            from market.data_fetcher import fetcher
            from market.pair_selector import pair_selector
            
            # Close all positions
            logger.info("Closing all open positions...")
            positions = db.fetch_all("SELECT * FROM positions WHERE side = 'buy'")
            
            for position in positions:
                try:
                    symbol = position[1].split(":")[1] if ":" in position[1] else position[1]
                    amount = position[3]
                    
                    # Execute market sell
                    await bot.exchange.create_market_order(symbol, "sell", amount)
                    logger.info(f"Emergency sold {amount} {symbol}")
                except Exception as e:
                    logger.error(f"Failed to close position: {e}")
            
            # Cancel all pending orders
            logger.info("Cancelling all pending orders...")
            try:
                for symbol in ["BTC/USDT", "ETH/USDT", "BNB/USDT"]:
                    open_orders = await bot.exchange.fetch_open_orders(symbol)
                    for order in open_orders:
                        await bot.exchange.cancel_order(order["id"], symbol)
                        logger.info(f"Cancelled order {order['id']}")
            except Exception as e:
                logger.error(f"Failed to cancel orders: {e}")
            
            # Shutdown all connections
            logger.info("Shutting down all connections...")
            
            try:
                await bot.close()
            except:
                pass
                
            try:
                await fetcher.close()
            except:
                pass
                
            try:
                await pair_selector.close()
            except:
                pass
            
            # Create emergency report
            self._create_emergency_report()
            
            # Create lock file
            with open("EMERGENCY_STOP_ACTIVE", "w") as f:
                f.write(f"Kill switch activated at {self.activation_time.isoformat()}\n")
                f.write("Remove this file to restart the system\n")
            
            logger.critical("KILL SWITCH COMPLETE - All trading stopped!")
            logger.critical("System locked - Remove EMERGENCY_STOP_ACTIVE file to restart")
            
            return True
            
        except Exception as e:
            logger.error(f"Kill switch error: {e}")
            # Still try to create lock file
            try:
                with open("EMERGENCY_STOP_ACTIVE", "w") as f:
                    f.write(f"Kill switch error at {datetime.now().isoformat()}\n")
            except:
                pass
            raise
    
    def _create_emergency_report(self):
        """Create emergency shutdown report"""
        try:
            report_file = f"emergency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_file, "w") as f:
                f.write("ARASAKA NEURAL-NET TRADING MATRIX\n")
                f.write("EMERGENCY SHUTDOWN REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Activation Time: {self.activation_time}\n\n")
                
                # Portfolio status
                portfolio_value = db.get_portfolio_value()
                f.write(f"Portfolio Value: {portfolio_value:.2f} Eddies\n\n")
                
                # Recent trades
                f.write("RECENT TRADES (Last 10):\n")
                trades = db.fetch_all(
                    "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10"
                )
                for trade in trades:
                    f.write(f"  {trade}\n")
                
                # Open positions at shutdown
                f.write("\nOPEN POSITIONS AT SHUTDOWN:\n")
                positions = db.fetch_all("SELECT * FROM positions")
                for position in positions:
                    f.write(f"  {position}\n")
                
                # Reserves
                f.write("\nTAX RESERVES:\n")
                reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
                reserve_amount = reserves[0] if reserves and reserves[0] else 0
                f.write(f"  Total: {reserve_amount:.2f} Eddies\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("System locked - Manual intervention required\n")
            
            logger.info(f"Emergency report created: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to create emergency report: {e}")
    
    def check_status(self):
        """Check if kill switch is active"""
        if os.path.exists("EMERGENCY_STOP_ACTIVE"):
            return True
        return self.activated
    
    def reset(self):
        """Reset kill switch (requires manual file removal)"""
        if os.path.exists("EMERGENCY_STOP_ACTIVE"):
            logger.warning("Cannot reset - Remove EMERGENCY_STOP_ACTIVE file manually")
            return False
        
        self.activated = False
        self.activation_time = None
        logger.info("Kill switch reset")
        return True

# Create singleton instance
kill_switch = KillSwitch()
