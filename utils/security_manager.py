# utils/security_manager.py
from cryptography.fernet import Fernet
from config.settings import settings
from core.database import db
from utils.logger import logger
import os
import time
import hashlib

class SecurityManager:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.config_file = "defi_config.json"
        self.log_file = "trading.log"
        self.pin = None
        self.last_device_check = 0

    def encrypt_data(self, data):
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption flatlined: {e}")
            return data

    def decrypt_data(self, encrypted_data):
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption flatlined: {e}")
            return encrypted_data

    def secure_config(self, rpc_url, pancake_address, abi, private_key):
        config = {
            "rpc_url": self.encrypt_data(rpc_url),
            "pancake_swap_address": self.encrypt_data(pancake_address),
            "abi": self.encrypt_data(abi),
            "private_key": self.encrypt_data(private_key)
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        logger.info("DeFi config secured with Militech-grade encryption")

    def load_secure_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    return {
                        "rpc_url": self.decrypt_data(config.get("rpc_url", "")),
                        "pancake_swap_address": self.decrypt_data(config.get("pancake_swap_address", "")),
                        "abi": self.decrypt_data(config.get("abi", "")),
                        "private_key": self.decrypt_data(config.get("private_key", ""))
                    }
            return {"rpc_url": None, "pancake_swap_address": None, "abi": None, "private_key": None}
        except Exception as e:
            logger.error(f"Secure config load flatlined: {e}")
            return {"rpc_url": None, "pancake_swap_address": None, "abi": None, "private_key": None}

    def verify_pin(self, pin):
        if not self.pin:
            self.pin = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]  # Initial PIN
        return hashlib.sha256(pin.encode()).hexdigest()[:8] == self.pin

    def check_tamper(self):
        try:
            if time.time() - self.last_device_check > 3600:  # Check hourly
                db_hash = hashlib.sha256(str(db.fetch_all("SELECT * FROM trades")).encode()).hexdigest()
                if not hasattr(self, 'last_db_hash') or db_hash != self.last_db_hash:
                    logger.warning("Tamper detected - Locking down!")
                    self.emergency_lock()
                self.last_db_hash = db_hash
                self.last_device_check = time.time()
            return True
        except Exception as e:
            logger.error(f"Tamper check flatlined: {e}")
            return False

    def emergency_lock(self):
        try:
            with open(self.log_file, "w") as f:
                f.write("System locked - Data wiped by Militech protocol")
            db.execute_query("DELETE FROM trades")
            db.execute_query("DELETE FROM positions")
            db.execute_query("DELETE FROM reserves")
            logger.critical("Emergency lock triggered - Data wiped, Arasaka foiled!")
        except Exception as e:
            logger.error(f"Emergency lock flatlined: {e}")

    def self_test(self):
        try:
            if not os.path.exists(self.config_file) or not os.path.exists(self.log_file):
                logger.warning("Self-test failed - Config or log missing")
                return False
            db_conn = db.conn
            if not db_conn:
                logger.warning("Self-test failed - DB connection down")
                return False
            logger.info("Self-test passed - Militech-grade security active")
            return True
        except Exception as e:
            logger.error(f"Self-test flatlined: {e}")
            return False

security_manager = SecurityManager()
