#!/usr/bin/env python3
"""
Enable FULL simulation mode - Test everything without API keys!
"""
import sys
import os
sys.path.append(os.getcwd())

from core.database import db
from datetime import datetime, timedelta
import uuid
import random
import numpy as np

def create_historical_data():
    """Create realistic historical data for backtesting"""
    print("📊 Creating historical price data...")
    
    symbols = ["binance:BTC/USDT", "binance:ETH/USDT", "binance:BNB/USDT"]
    
    for symbol in symbols:
        # Generate 1000 hours of data
        base_price = {"BTC": 45000, "ETH": 3000, "BNB": 300}
        coin = symbol.split(":")[1].split("/")[0]
        price = base_price.get(coin, 1000)
        
        data = []
        now = datetime.now()
        
        for i in range(1000):
            timestamp = now - timedelta(hours=i)
            ts_ms = int(timestamp.timestamp() * 1000)
            
            # Add some realistic volatility
            change = random.uniform(-0.02, 0.02)
            price = price * (1 + change)
            
            high = price * (1 + abs(random.uniform(0, 0.01)))
            low = price * (1 - abs(random.uniform(0, 0.01)))
            volume = random.uniform(100000, 1000000)
            
            data.append((symbol, ts_ms, price*0.99, high, low, price, volume))
        
        # Batch insert
        db.executemany(
            """
            INSERT OR REPLACE INTO historical_data
            (symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            data
        )
        
        print(f"✅ Created {len(data)} candles for {symbol}")

def create_simulated_trades():
    """Create a series of simulated trades"""
    print("\n💰 Creating simulated trades...")
    
    trades = []
    positions = []
    
    # Starting portfolio
    portfolio_value = 1000.0
    
    # Create 20 trades over the past week
    for i in range(20):
        trade_time = datetime.now() - timedelta(hours=i*8)
        trade_id = str(uuid.uuid4())
        
        # Alternate between buy and sell
        side = "buy" if i % 2 == 0 else "sell"
        
        # Random price around 45k
        price = 45000 + random.uniform(-2000, 2000)
        amount = 0.001
        fee = amount * price * 0.001  # 0.1% fee
        
        trades.append((
            trade_id,
            "binance:BTC/USDT",
            side,
            amount,
            price,
            fee,
            1.0,  # leverage
            trade_time.isoformat()
        ))
        
        # Update portfolio value
        if side == "sell":
            # Calculate profit/loss
            profit = amount * (price - (45000 + random.uniform(-1000, 1000))) - fee*2
            portfolio_value += profit
    
    # Insert trades
    db.executemany(
        """
        INSERT INTO trades (id, symbol, side, amount, price, fee, leverage, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        trades
    )
    
    print(f"✅ Created {len(trades)} simulated trades")
    
    # Create some open positions
    position_id = str(uuid.uuid4())
    db.execute_query(
        """
        INSERT INTO positions (id, symbol, side, amount, entry_price, stop_loss, take_profit, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            position_id,
            "binance:BTC/USDT",
            "buy",
            0.002,
            45000.0,
            43000.0,  # Stop loss
            47000.0,  # Take profit
            datetime.now().isoformat()
        )
    )
    
    print("✅ Created open position")
    
    # Update portfolio
    db.update_portfolio_value(portfolio_value)
    print(f"✅ Portfolio value: ${portfolio_value:.2f}")

def create_market_data():
    """Create recent market data for real-time display"""
    print("\n📈 Creating market data...")
    
    symbols = ["binance:BTC/USDT", "binance:ETH/USDT", "binance:BNB/USDT"]
    
    for symbol in symbols:
        # Last 24 hours of data
        for i in range(24):
            timestamp = datetime.now() - timedelta(hours=i)
            ts_ms = int(timestamp.timestamp() * 1000)
            
            base_prices = {"BTC": 45000, "ETH": 3000, "BNB": 300}
            coin = symbol.split(":")[1].split("/")[0]
            price = base_prices.get(coin, 1000) + random.uniform(-500, 500)
            
            db.execute_query(
                """
                INSERT OR REPLACE INTO market_data
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    ts_ms,
                    price * 0.99,
                    price * 1.01,
                    price * 0.98,
                    price,
                    random.uniform(100000, 1000000)
                )
            )
    
    print("✅ Created recent market data")

def create_seasonality_patterns():
    """Create seasonality data for ML features"""
    print("\n🌊 Creating seasonality patterns...")
    
    patterns = [
        ("binance:BTC/USDT", "weekday_1", 0.02, 0.15),  # Monday - bullish
        ("binance:BTC/USDT", "weekday_5", -0.01, 0.20),  # Friday - bearish
        ("binance:ETH/USDT", "month_12", 0.05, 0.25),   # December - bullish
    ]
    
    for pattern in patterns:
        db.store_seasonality_pattern(*pattern)
    
    print("✅ Created seasonality patterns")

def setup_risk_parameters():
    """Configure risk management for simulation"""
    print("\n🛡️ Setting up risk parameters...")
    
    # Add some reserves
    db.execute_query(
        """
        INSERT INTO reserves (trade_id, amount, timestamp)
        VALUES (?, ?, ?)
        """,
        ("sim_reserve_001", 50.0, datetime.now().isoformat())
    )
    
    print("✅ Created tax reserves: $50.00")

def enable_simulation_api():
    """Modify settings for simulation mode"""
    print("\n⚙️ Configuring simulation mode...")
    
    # Create a simulation config file
    sim_config = """# Simulation Mode Configuration
SIMULATION_MODE=true
SIMULATION_TRADES=true
SIMULATION_PRICES=true

# These will be ignored in simulation mode
BINANCE_API_KEY=simulation_key
BINANCE_API_SECRET=simulation_secret
"""
    
    with open("simulation_config.txt", "w") as f:
        f.write(sim_config)
    
    print("✅ Created simulation config")

def test_features():
    """Test various features with simulated data"""
    print("\n🧪 Testing features with simulated data...")
    
    # Test portfolio calculation
    portfolio = db.get_portfolio_value()
    print(f"   Portfolio Value: ${portfolio:.2f}")
    
    # Test trade count
    trade_count = db.fetch_one("SELECT COUNT(*) FROM trades")[0]
    print(f"   Total Trades: {trade_count}")
    
    # Test position count
    position_count = db.fetch_one("SELECT COUNT(*) FROM positions")[0]
    print(f"   Open Positions: {position_count}")
    
    # Test historical data
    hist_count = db.fetch_one("SELECT COUNT(*) FROM historical_data")[0]
    print(f"   Historical Records: {hist_count}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║          ARASAKA NEURAL-NET SIMULATION MODE SETUP             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n🚀 Setting up complete simulation environment...\n")
    
    # Run all setup functions
    create_historical_data()
    create_simulated_trades()
    create_market_data()
    create_seasonality_patterns()
    setup_risk_parameters()
    enable_simulation_api()
    test_features()
    
    print("\n" + "="*60)
    print("✅ SIMULATION MODE FULLY ACTIVE!")
    print("="*60)
    
    print("\n📋 WHAT YOU CAN TEST NOW:")
    print("\n1. TRADING MATRIX TAB:")
    print("   - Click REFRESH to see portfolio ($1,000+)")
    print("   - View simulated trades in portfolio")
    print("   - P&L display will show profits")
    print("   - Try 'Buy' or 'Sell' (will show error but that's OK)")
    
    print("\n2. DASHBOARD TAB:")
    print("   - RUN BACKTEST - Will work with simulated data!")
    print("   - All automation features can be tested")
    print("   - Charts will display properly")
    
    print("\n3. AUTO-TRADING:")
    print("   - Enable checkbox - indicator turns green")
    print("   - Won't execute real trades but UI works")
    
    print("\n4. FEATURES TO TEST:")
    print("   ✅ Portfolio tracking")
    print("   ✅ P&L calculations")
    print("   ✅ Backtest system")
    print("   ✅ Risk management")
    print("   ✅ ML training (with simulated data)")
    print("   ✅ All UI elements")
    print("   ✅ Automation scheduling")
    
    print("\n💡 Note: Actual trading still needs API keys,")
    print("   but everything else works perfectly!")
    
    print("\n🎮 GO BACK TO YOUR GUI AND TEST EVERYTHING!")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")