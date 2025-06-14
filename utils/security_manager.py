# utils/security_manager.py
"""
Militech Security Protocols - Protects the Trading Matrix from intrusions
"""
import os
import json
import time
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime

from core.database import db
from utils.logger import logger

class SecurityManager:
    def __init__(self):
        # Generate or load encryption key
        self.key_file = "config/security.key"
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        
        # Security settings
        self.config_file = "config/defi_config.json"
        self.pin_hash = None
        self.last_tamper_check = 0
        self.last_db_hash = None
        self.failed_attempts = 0
        self.lockout_time = 0
    
    def _load_or_generate_key(self):
        """Load existing key or generate new one"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, "rb") as f:
                    return f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                with open(self.key_file, "wb") as f:
                    f.write(key)
                return key
        except Exception as e:
            logger.error(f"Security key error: {e}")
            return Fernet.generate_key()
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self.cipher.encrypt(data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ""
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            return self.cipher.decrypt(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def secure_config(self, rpc_url, pancake_address, abi, private_key):
        """Securely store DeFi configuration"""
        try:
            config = {
                "rpc_url": self.encrypt_data(rpc_url) if rpc_url else "",
                "pancake_swap_address": self.encrypt_data(pancake_address) if pancake_address else "",
                "abi": self.encrypt_data(abi) if abi else "",
                "private_key": self.encrypt_data(private_key) if private_key else "",
                "timestamp": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            
            logger.info("DeFi config secured with Militech encryption")
            return True
            
        except Exception as e:
            logger.error(f"Config security failed: {e}")
            return False
    
    def load_secure_config(self):
        """Load and decrypt DeFi configuration"""
        try:
            if not os.path.exists(self.config_file):
                return {
                    "rpc_url": None,
                    "pancake_swap_address": None,
                    "abi": None,
                    "private_key": None
                }
            
            with open(self.config_file, "r") as f:
                encrypted_config = json.load(f)
            
            return {
                "rpc_url": self.decrypt_data(encrypted_config.get("rpc_url", "")) or None,
                "pancake_swap_address": self.decrypt_data(encrypted_config.get("pancake_swap_address", "")) or None,
                "abi": self.decrypt_data(encrypted_config.get("abi", "")) or None,
                "private_key": self.decrypt_data(encrypted_config.get("private_key", "")) or None
            }
            
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            return {
                "rpc_url": None,
                "pancake_swap_address": None,
                "abi": None,
                "private_key": None
            }
    
    def verify_pin(self, pin):
        """Verify access PIN"""
        try:
            # Check lockout
            if self.lockout_time > time.time():
                remaining = int(self.lockout_time - time.time())
                logger.warning(f"Security lockout active: {remaining}s remaining")
                return False
            
            # Generate PIN hash if not set
            if not self.pin_hash:
                # Default PIN for first access
                self.pin_hash = hashlib.sha256("2077".encode()).hexdigest()
            
            # Verify PIN
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            
            if pin_hash == self.pin_hash:
                self.failed_attempts = 0
                logger.info("PIN verification successful")
                return True
            else:
                self.failed_attempts += 1
                
                # Lockout after 5 failed attempts
                if self.failed_attempts >= 5:
                    self.lockout_time = time.time() + 300  # 5 minute lockout
                    logger.warning(f"Security lockout activated: Too many failed attempts")
                
                logger.warning(f"PIN verification failed (attempt {self.failed_attempts})")
                return False
                
        except Exception as e:
            logger.error(f"PIN verification error: {e}")
            return False
    
    def check_tamper(self):
        """Check for system tampering"""
        try:
            current_time = time.time()
            
            # Only check every hour
            if current_time - self.last_tamper_check < 3600:
                return True
            
            # Calculate database hash
            trades = db.fetch_all("SELECT * FROM trades ORDER BY id")
            positions = db.fetch_all("SELECT * FROM positions ORDER BY id")
            
            db_content = str(trades) + str(positions)
            current_hash = hashlib.sha256(db_content.encode()).hexdigest()
            
            # Check for unexpected changes
            if self.last_db_hash and current_hash != self.last_db_hash:
                # Verify if changes are legitimate
                recent_trades = db.fetch_all(
                    "SELECT * FROM trades WHERE timestamp > datetime('now', '-1 hour')"
                )
                
                if not recent_trades:
                    logger.warning("Database tampering detected - No recent trades!")
                    return False
            
            self.last_db_hash = current_hash
            self.last_tamper_check = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Tamper check failed: {e}")
            return True  # Don't lock out on error
    
    def emergency_lock(self):
        """Emergency system lockdown"""
        try:
            logger.critical("EMERGENCY LOCK ACTIVATED - Militech protocols engaged!")
            
            # Wipe sensitive data
            sensitive_tables = ["trades", "positions", "reserves"]
            
            for table in sensitive_tables:
                try:
                    db.execute_query(f"DELETE FROM {table}")
                    logger.info(f"Wiped {table} table")
                except:
                    pass
            
            # Delete config files
            sensitive_files = [
                self.config_file,
                "config/.env",
                "ml/model.pkl",
                "ml/rl_model.h5"
            ]
            
            for file in sensitive_files:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                        logger.info(f"Deleted {file}")
                except:
                    pass
            
            # Create lockout file
            with open("SYSTEM_LOCKED", "w") as f:
                f.write(f"System locked at {datetime.now().isoformat()}")
            
            logger.critical("Emergency lock complete - System secured")
            
        except Exception as e:
            logger.error(f"Emergency lock error: {e}")
    
    def self_test(self):
        """Run security self-test"""
        try:
            # Check critical files
            critical_files = [
                "logs/trading.log",
                self.key_file
            ]
            
            for file in critical_files:
                if not os.path.exists(file):
                    logger.warning(f"Self-test failed: {file} missing")
                    return False
            
            # Check database connection
            try:
                db.fetch_one("SELECT 1")
            except:
                logger.warning("Self-test failed: Database offline")
                return False
            
            # Check for system lock
            if os.path.exists("SYSTEM_LOCKED"):
                logger.warning("Self-test failed: System is locked")
                return False
            
            logger.info("Security self-test passed")
            return True
            
        except Exception as e:
            logger.error(f"Self-test error: {e}")
            return False

# Create singleton instance
security_manager = SecurityManager()
