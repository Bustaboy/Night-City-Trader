# config/exchange_manager.py
"""
Arasaka Exchange Manager - Handles multiple exchange configurations
Stores encrypted API credentials in database, not .env file
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet

from core.database import db
from utils.logger import logger

@dataclass
class ExchangeCredentials:
    """Exchange credential structure"""
    exchange: str
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None  # For Coinbase
    subaccount: Optional[str] = None      # For Bybit
    enabled: bool = True
    testnet: bool = True

class ExchangeManager:
    """Manages multiple exchange configurations"""
    
    # Exchange configuration requirements
    EXCHANGE_CONFIG = {
        "coinbase": {
            "requires_passphrase": True,
            "testnet_url": "https://api-public.sandbox.exchange.coinbase.com",
            "rate_limit": 100,
            "fee_maker": 0.005,
            "fee_taker": 0.005,
            "pairs_format": "BTC-USD",
            "supports_leverage": False
        },
        "kraken": {
            "requires_passphrase": False,
            "testnet_url": None,  # No testnet
            "rate_limit": 60,
            "fee_maker": 0.0016,
            "fee_taker": 0.0026,
            "pairs_format": "BTC/USD",
            "supports_leverage": True
        },
        "bitstamp": {
            "requires_passphrase": False,
            "testnet_url": None,
            "rate_limit": 600,
            "fee_maker": 0.005,
            "fee_taker": 0.005,
            "pairs_format": "BTC/USD",
            "supports_leverage": False
        },
        "bybit": {
            "requires_passphrase": False,
            "testnet_url": "https://api-testnet.bybit.com",
            "rate_limit": 50,
            "fee_maker": 0.001,
            "fee_taker": 0.001,
            "pairs_format": "BTCUSDT",
            "supports_leverage": True
        },
        "bitvavo": {
            "requires_passphrase": False,
            "testnet_url": None,
            "rate_limit": 100,
            "fee_maker": 0.002,
            "fee_taker": 0.0025,
            "pairs_format": "BTC-EUR",
            "supports_leverage": False
        },
        "binance": {
            "requires_passphrase": False,
            "testnet_url": "https://testnet.binance.vision",
            "rate_limit": 1200,
            "fee_maker": 0.001,
            "fee_taker": 0.001,
            "pairs_format": "BTC/USDT",
            "supports_leverage": True
        }
    }
    
    def __init__(self):
        self._init_database()
        self._encryption_key = self._get_or_create_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _init_database(self):
        """Initialize exchange credentials table"""
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS exchange_credentials (
                exchange TEXT PRIMARY KEY,
                encrypted_data TEXT,
                enabled INTEGER DEFAULT 1,
                testnet INTEGER DEFAULT 1,
                last_updated TEXT
            )
        """)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        try:
            # Try to get from database
            result = db.fetch_one("SELECT value FROM system_config WHERE key = 'encryption_key'")
            if result:
                return result[0].encode()
            
            # Create new key
            key = Fernet.generate_key()
            
            # Create system_config table if needed
            db.execute_query("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Store key
            db.execute_query(
                "INSERT INTO system_config (key, value) VALUES (?, ?)",
                ("encryption_key", key.decode())
            )
            
            return key
            
        except Exception as e:
            logger.error(f"Encryption key error: {e}")
            return Fernet.generate_key()
    
    def save_credentials(self, creds: ExchangeCredentials) -> bool:
        """Save encrypted exchange credentials"""
        try:
            # Prepare credential data
            cred_data = {
                "api_key": creds.api_key,
                "api_secret": creds.api_secret,
                "api_passphrase": creds.api_passphrase,
                "subaccount": creds.subaccount
            }
            
            # Encrypt
            encrypted = self._cipher.encrypt(json.dumps(cred_data).encode())
            
            # Save to database
            db.execute_query("""
                INSERT OR REPLACE INTO exchange_credentials 
                (exchange, encrypted_data, enabled, testnet, last_updated)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (
                creds.exchange,
                encrypted.decode(),
                1 if creds.enabled else 0,
                1 if creds.testnet else 0
            ))
            
            logger.info(f"Saved credentials for {creds.exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    def get_credentials(self, exchange: str) -> Optional[ExchangeCredentials]:
        """Get decrypted exchange credentials"""
        try:
            result = db.fetch_one("""
                SELECT encrypted_data, enabled, testnet 
                FROM exchange_credentials 
                WHERE exchange = ?
            """, (exchange,))
            
            if not result:
                return None
            
            # Decrypt
            decrypted = self._cipher.decrypt(result[0].encode())
            cred_data = json.loads(decrypted.decode())
            
            return ExchangeCredentials(
                exchange=exchange,
                api_key=cred_data["api_key"],
                api_secret=cred_data["api_secret"],
                api_passphrase=cred_data.get("api_passphrase"),
                subaccount=cred_data.get("subaccount"),
                enabled=bool(result[1]),
                testnet=bool(result[2])
            )
            
        except Exception as e:
            logger.error(f"Failed to get credentials for {exchange}: {e}")
            return None
    
    def get_all_credentials(self) -> List[ExchangeCredentials]:
        """Get all exchange credentials"""
        try:
            results = db.fetch_all("""
                SELECT exchange, encrypted_data, enabled, testnet 
                FROM exchange_credentials
                WHERE enabled = 1
            """)
            
            credentials = []
            for exchange, encrypted_data, enabled, testnet in results:
                try:
                    decrypted = self._cipher.decrypt(encrypted_data.encode())
                    cred_data = json.loads(decrypted.decode())
                    
                    credentials.append(ExchangeCredentials(
                        exchange=exchange,
                        api_key=cred_data["api_key"],
                        api_secret=cred_data["api_secret"],
                        api_passphrase=cred_data.get("api_passphrase"),
                        subaccount=cred_data.get("subaccount"),
                        enabled=bool(enabled),
                        testnet=bool(testnet)
                    ))
                except Exception as e:
                    logger.error(f"Failed to decrypt credentials for {exchange}: {e}")
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get all credentials: {e}")
            return []
    
    def delete_credentials(self, exchange: str) -> bool:
        """Delete exchange credentials"""
        try:
            db.execute_query(
                "DELETE FROM exchange_credentials WHERE exchange = ?",
                (exchange,)
            )
            logger.info(f"Deleted credentials for {exchange}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
    
    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges"""
        try:
            results = db.fetch_all("""
                SELECT exchange FROM exchange_credentials WHERE enabled = 1
            """)
            return [r[0] for r in results]
        except:
            return []
    
    def get_exchange_config(self, exchange: str) -> Dict:
        """Get exchange configuration"""
        return self.EXCHANGE_CONFIG.get(exchange, {})
    
    def is_testnet_mode(self, exchange: str) -> bool:
        """Check if exchange is in testnet mode"""
        try:
            result = db.fetch_one(
                "SELECT testnet FROM exchange_credentials WHERE exchange = ?",
                (exchange,)
            )
            return bool(result[0]) if result else True
        except:
            return True

# Create singleton instance
exchange_manager = ExchangeManager()
