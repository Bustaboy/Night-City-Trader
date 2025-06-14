# trading/liquidity_mining.py
from web3 import Web3
from utils.security_manager import security_manager
from utils.logger import logger
import asyncio
import json
import os

class LiquidityMiner:
    def __init__(self):
        self.config_file = "defi_config.json"
        self.load_config()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url)) if self.rpc_url else None
        self.contract_address = self.pancake_swap_address
        self.abi = self.abi
        self.private_key = self.private_key
        self.account = self.w3.eth.account.from_key(self.private_key).address if self.w3 and self.private_key else None

    def load_config(self):
        try:
            config = security_manager.load_secure_config()
            self.rpc_url = config["rpc_url"]
            self.pancake_swap_address = config["pancake_swap_address"]
            self.abi = config["abi"]
            self.private_key = config["private_key"]
        except Exception as e:
            logger.error(f"Config load flatlined: {e}")
            self.rpc_url = None
            self.pancake_swap_address = None
            self.abi = None
            self.private_key = None

    def save_config(self, rpc_url, pancake_swap_address, abi, private_key):
        security_manager.secure_config(rpc_url, pancake_swap_address, abi, private_key)

    async def auto_mine_liquidity(self):
        try:
            if not all([self.w3, self.contract_address, self.abi, self.private_key, self.account]):
                logger.warning("DeFi config incomplete - Mining skipped")
                return
            if not security_manager.self_test():
                logger.warning("Security check failed - Mining aborted")
                return
            reserves = db.fetch_all("SELECT SUM(amount) FROM reserves")[0][0] or 0
            if reserves > 100:  # Min threshold
                contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
                tx = contract.functions.addLiquidityETH(
                    self.w3.to_checksum_address(settings.TRADING["symbol"].split("/")[0]),
                    int(reserves * 0.1),  # 10% of reserves
                    0, 0,
                    self.account,
                    int(time.time()) + 3600
                ).build_transaction({
                    "from": self.account,
                    "nonce": self.w3.eth.get_transaction_count(self.account),
                    "gas": 200000,
                    "gasPrice": self.w3.to_wei("50", "gwei")
                })
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info(f"Liquidity mined: {tx_hash.hex()} - Stacking passive Eddies!")
        except Exception as e:
            logger.error(f"Liquidity mining flatlined: {e}")

liquidity_miner = LiquidityMiner()
