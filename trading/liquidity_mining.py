# trading/liquidity_mining.py
from web3 import Web3
from config.settings import settings
from core.database import db
from utils.logger import logger
import asyncio

class LiquidityMiner:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.DEFI["rpc_url"]))
        self.contract_address = settings.DEFI["pancake_swap_address"]
        self.private_key = settings.DEFI["private_key"]
        self.account = self.w3.eth.account.from_key(self.private_key).address

    async def auto_mine_liquidity(self):
        try:
            reserves = db.fetch_all("SELECT SUM(amount) FROM reserves")[0][0] or 0
            if reserves > 100:  # Min threshold
                contract = self.w3.eth.contract(address=self.contract_address, abi=settings.DEFI["abi"])
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
