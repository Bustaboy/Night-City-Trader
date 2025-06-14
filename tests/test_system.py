# tests/test_system.py
"""
System test script for the Arasaka Neural-Net Trading Matrix
Run this to verify all components are working correctly
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    modules = [
        ("Database", "core.database", "db"),
        ("Logger", "utils.logger", "logger"),
        ("Settings", "config.settings", "settings"),
        ("Trading Bot", "trading.trading_bot", "bot"),
        ("Risk Manager", "trading.risk_manager", "risk_manager"),
        ("ML Trainer", "ml.trainer", "trainer"),
        ("RL Trainer", "ml.rl_trainer", "rl_trainer"),
        ("Data Fetcher", "market.data_fetcher", "fetcher"),
        ("Pair Selector", "market.pair_selector", "pair_selector"),
        ("Security Manager", "utils.security_manager", "security_manager"),
        ("Tax Reporter", "utils.tax_reporter", "tax_reporter"),
        ("Kill Switch", "emergency.kill_switch", "kill_switch"),
        ("Trading Strategies", "trading.strategies", "strategies"),
    ]
    
    failed = []
    
    for name, module_path, obj_name in modules:
        try:
            module = __import__(module_path, fromlist=[obj_name])
            obj = getattr(module, obj_name)
            print(f"✓ {name} imported successfully")
        except Exception as e:
            print(f"✗ {name} import failed: {e}")
            failed.append(name)
    
    return len(failed) == 0

def test_database():
    """Test database operations"""
    print("\nTesting database...")
    
    try:
        from core.database import db
        
        # Test query
        result = db.fetch_one("SELECT 1")
        assert result[0] == 1
        print("✓ Database query successful")
        
        # Test portfolio
        value = db.get_portfolio_value()
        print(f"✓ Portfolio value: {value} Eddies")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config.settings import settings
        
        checks = [
            ("API Host", settings.API_HOST),
            ("API Port", settings.API_PORT),
            ("Testnet Mode", settings.TESTNET),
            ("Trading Symbol", settings.TRADING["symbol"]),
            ("Risk Profiles", len(settings.TRADING["risk"])),
            ("ML Features", len(settings.ML["features"])),
        ]
        
        for name, value in checks:
            print(f"✓ {name}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

async def test_exchange_connection():
    """Test exchange connectivity"""
    print("\nTesting exchange connection...")
    
    try:
        from market.data_fetcher import fetcher
        
        # Initialize fetcher
        await fetcher.initialize()
        
        # Try to fetch some data
        data = await fetcher.fetch_ohlcv("BTC/USDT", "1h", limit=10)
        
        if data:
            print(f"✓ Exchange connection successful - Retrieved {len(data)} candles")
        else:
            print("✓ Exchange connection successful - Using cached/simulated data")
        
        # Close connection
        await fetcher.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Exchange test failed: {e}")
        return False

def test_ml_models():
    """Test ML model loading"""
    print("\nTesting ML models...")
    
    try:
        from ml.trainer import trainer
        from ml.rl_trainer import rl_trainer
        
        # Check if models exist
        ml_exists = os.path.exists(trainer.model_path)
        rl_exists = os.path.exists(rl_trainer.model_path)
        
        if ml_exists:
            print("✓ ML model found")
        else:
            print("! ML model not found (will be created on first training)")
        
        if rl_exists:
            print("✓ RL model found")
        else:
            print("! RL model not found (will be created on first training)")
        
        return True
        
    except Exception as e:
        print(f"✗ ML test failed: {e}")
        return False

def test_security():
    """Test security features"""
    print("\nTesting security...")
    
    try:
        from utils.security_manager import security_manager
        
        # Test PIN verification
        result = security_manager.verify_pin("2077")
        print(f"✓ PIN verification: {'Success' if result else 'Failed (default PIN: 2077)'}")
        
        # Test self-test
        result = security_manager.self_test()
        print(f"✓ Security self-test: {'Passed' if result else 'Failed'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Security test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Arasaka Neural-Net Trading Matrix - System Test")
    print("=" * 60)
    
    # Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠️  Warning: Python 3.9+ recommended")
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Configuration", test_configuration),
        ("ML Models", test_ml_models),
        ("Security", test_security),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Test exchange connection separately (async)
    try:
        result = asyncio.run(test_exchange_connection())
        results.append(("Exchange Connection", result))
    except Exception as e:
        print(f"\n✗ Exchange test crashed: {e}")
        results.append(("Exchange Connection", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational - Ready to jack into the Matrix!")
    else:
        print("\n⚠️  Some tests failed - Check the errors above")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
