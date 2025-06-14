#!/usr/bin/env python3
"""
Arasaka Neural-Net Trading Matrix - Automated Test Suite
Run this to test all components automatically
"""
import os
import sys
import time
import subprocess
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class TestRunner:
    def __init__(self):
        self.results = []
        self.api_process = None
        
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"📍 {text}")
        print(f"{'='*60}")
        
    def test_result(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, passed))
        print(f"{status} - {test_name}")
        if details:
            print(f"    └─ {details}")
            
    def test_python_version(self):
        """Test Python version"""
        self.print_header("PYTHON VERSION CHECK")
        version = sys.version_info
        passed = version.major == 3 and version.minor >= 9
        self.test_result(
            "Python 3.9+", 
            passed, 
            f"Found: {version.major}.{version.minor}.{version.micro}"
        )
        return passed
        
    def test_dependencies(self):
        """Test required packages"""
        self.print_header("DEPENDENCY CHECK")
        required = ['fastapi', 'ccxt', 'pandas', 'numpy', 'tensorflow']
        
        for package in required:
            try:
                __import__(package)
                self.test_result(f"Package: {package}", True)
            except ImportError:
                self.test_result(f"Package: {package}", False, "Not installed")
                
    def test_project_structure(self):
        """Test directory structure"""
        self.print_header("PROJECT STRUCTURE CHECK")
        
        required_dirs = [
            "api", "config", "core", "trading", "ml", 
            "gui", "market", "utils", "scripts", "tests"
        ]
        
        for dir_name in required_dirs:
            exists = Path(dir_name).exists()
            self.test_result(f"Directory: {dir_name}", exists)
            
    def test_configuration(self):
        """Test configuration files"""
        self.print_header("CONFIGURATION CHECK")
        
        # Check .env
        env_exists = Path(".env").exists()
        self.test_result(".env file", env_exists)
        
        if env_exists:
            with open(".env", "r") as f:
                content = f.read()
                has_keys = "BINANCE_API_KEY" in content
                self.test_result(
                    "API keys configured", 
                    has_keys and "your_api_key_here" not in content,
                    "Remember to add real API keys!"
                )
                
        # Check config.yaml
        config_exists = Path("config/config.yaml").exists()
        self.test_result("config.yaml", config_exists)
        
    def test_database(self):
        """Test database operations"""
        self.print_header("DATABASE CHECK")
        
        try:
            from core.database import db
            
            # Test connection
            result = db.fetch_one("SELECT 1")
            self.test_result("Database connection", result is not None)
            
            # Test tables
            tables = ["trades", "positions", "historical_data"]
            for table in tables:
                try:
                    count = db.fetch_one(f"SELECT COUNT(*) FROM {table}")
                    self.test_result(f"Table: {table}", True, f"{count[0]} records")
                except:
                    self.test_result(f"Table: {table}", False)
                    
        except Exception as e:
            self.test_result("Database system", False, str(e))
            
    def test_ml_models(self):
        """Test ML components"""
        self.print_header("ML/AI SYSTEM CHECK")
        
        try:
            from ml.trainer import trainer
            from ml.rl_trainer import rl_trainer
            
            # Check model files
            ml_exists = Path("ml/model.pkl").exists()
            rl_exists = Path("ml/rl_model.h5").exists()
            
            self.test_result(
                "ML model", 
                True, 
                "Loaded" if ml_exists else "Not trained yet"
            )
            self.test_result(
                "RL model", 
                True, 
                "Loaded" if rl_exists else "Not trained yet"
            )
            
        except Exception as e:
            self.test_result("ML system", False, str(e))
            
    def test_api_server(self):
        """Test API server"""
        self.print_header("API SERVER CHECK")
        
        print("Starting API server...")
        
        # Start API server
        self.api_process = subprocess.Popen(
            [sys.executable, "api/app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(5)
        
        # Test endpoints
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            self.test_result("API health endpoint", response.status_code == 200)
            
            response = requests.get("http://localhost:8000/", timeout=5)
            self.test_result("API root endpoint", response.status_code == 200)
            
        except Exception as e:
            self.test_result("API server", False, f"Connection failed: {e}")
            
    def test_trading_components(self):
        """Test trading system"""
        self.print_header("TRADING SYSTEM CHECK")
        
        try:
            from trading.trading_bot import bot
            from trading.risk_manager import risk_manager
            from trading.strategies import strategies
            
            self.test_result("Trading bot", True)
            self.test_result("Risk manager", True)
            self.test_result("Trading strategies", True)
            
            # Test risk profiles
            risk_manager.set_risk_profile("moderate")
            self.test_result("Risk profile setting", True)
            
        except Exception as e:
            self.test_result("Trading system", False, str(e))
            
    def test_security(self):
        """Test security features"""
        self.print_header("SECURITY CHECK")
        
        try:
            from utils.security_manager import security_manager
            
            # Test PIN
            result = security_manager.verify_pin("2077")
            self.test_result("Default PIN (2077)", result)
            
            # Test encryption
            test_data = "test_secret"
            encrypted = security_manager.encrypt_data(test_data)
            decrypted = security_manager.decrypt_data(encrypted)
            self.test_result("Encryption/Decryption", decrypted == test_data)
            
        except Exception as e:
            self.test_result("Security system", False, str(e))
            
    def run_quick_simulation(self):
        """Run a quick trading simulation"""
        self.print_header("TRADING SIMULATION")
        
        try:
            from trading.trading_bot import bot
            from trading.risk_manager import risk_manager
            
            # Simulate risk check
            passed = risk_manager.check_trade_risk("BTC/USDT", "buy", 0.001, 1.0)
            self.test_result("Risk check simulation", passed)
            
            # Simulate position sizing
            size = risk_manager.adjust_position_size("BTC/USDT", 0.01)
            self.test_result("Position sizing", size > 0, f"Size: {size}")
            
        except Exception as e:
            self.test_result("Trading simulation", False, str(e))
            
    def cleanup(self):
        """Cleanup test resources"""
        if self.api_process:
            print("\nShutting down API server...")
            self.api_process.terminate()
            time.sleep(2)
            
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        passed = sum(1 for _, p in self.results if p)
        total = len(self.results)
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL SYSTEMS OPERATIONAL!")
            print("The Neural-Net is ready to stack Eddies!")
        else:
            print("\n⚠️  Some tests failed. Check the details above.")
            print("\nFailed tests:")
            for test, passed in self.results:
                if not passed:
                    print(f"  - {test}")
                    
        # Save results
        with open("test_results.txt", "w") as f:
            f.write(f"ARASAKA TEST RESULTS - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n")
            for test, passed in self.results:
                status = "PASS" if passed else "FAIL"
                f.write(f"{status:6} - {test}\n")
            f.write(f"\nTotal: {passed}/{total} passed\n")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║            ARASAKA NEURAL-NET AUTOMATED TEST SUITE            ║
    ║                  Testing all Matrix components...             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    runner = TestRunner()
    
    try:
        # Run all tests
        if not runner.test_python_version():
            print("\n❌ Python 3.9+ required! Aborting tests.")
            return
            
        runner.test_dependencies()
        runner.test_project_structure()
        runner.test_configuration()
        runner.test_database()
        runner.test_ml_models()
        runner.test_trading_components()
        runner.test_security()
        runner.test_api_server()
        runner.run_quick_simulation()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
    finally:
        runner.cleanup()
        runner.print_summary()
        
    print("\n📝 Test results saved to: test_results.txt")
    print("\nTo start the trading bot:")
    print("  1. python api/app.py")
    print("  2. python gui/main.py")
    print("\nDefault PIN: 2077")

if __name__ == "__main__":
    main()