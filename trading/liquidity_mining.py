# trading/liquidity_mining.py
"""
Arasaka Liquidity Mining - Passive income from DeFi protocols
"""
import json
import time
from web3 import Web3

from utils.security_manager import security_manager
from utils.logger import logger
from core.database import db

class LiquidityMiner:
    def __init__(self):
        self.config = security_manager.load_secure_config()
        self.w3 = None
        self.contract = None
        self.account = None
        self._initialized = False
    
    def initialize(self):
        """Initialize Web3 connection"""
        if self._initialized:
            return True
            
        try:
            if not self.config.get("rpc_url"):
                logger.warning("DeFi not configured - RPC URL missing")
                return False
            
            # Connect to blockchain
            self.w3 = Web3(Web3.HTTPProvider(self.config["rpc_url"]))
            
            if not self.w3.is_connected():
                logger.error("Failed to connect to blockchain")
                return False
            
            # Load contract if configured
            if self.config.get("pancake_swap_address") and self.config.get("abi"):
                try:
                    abi = json.loads(self.config["abi"]) if isinstance(self.config["abi"], str) else self.config["abi"]
                    self.contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(self.config["pancake_swap_address"]),
                        abi=abi
                    )
                except Exception as e:
                    logger.error(f"Contract initialization failed: {e}")
                    return False
            
            # Load account if private key available
            if self.config.get("private_key"):
                try:
                    self.account = self.w3.eth.account.from_key(self.config["private_key"])
                    logger.info(f"DeFi account loaded: {self.account.address}")
                except Exception as e:
                    logger.error(f"Account load failed: {e}")
                    return False
            
            self._initialized = True
            logger.info("Liquidity miner initialized")
            return True
            
        except Exception as e:
            logger.error(f"DeFi initialization failed: {e}")
            return False
    
    def save_config(self, rpc_url, pancake_address, abi, private_key):
        """Save DeFi configuration"""
        try:
            # Validate inputs
            if not rpc_url:
                raise ValueError("RPC URL required")
            
            # Validate ABI
            if abi:
                try:
                    if isinstance(abi, str):
                        json.loads(abi)
                except:
                    raise ValueError("Invalid ABI format")
            
            # Save encrypted config
            security_manager.secure_config(
                rpc_url,
                pancake_address or "",
                abi or "[]",
                private_key or ""
            )
            
            # Reload config
            self.config = security_manager.load_secure_config()
            self._initialized = False  # Force re-initialization
            
            logger.info("DeFi configuration saved")
            return True
            
        except Exception as e:
            logger.error(f"Config save failed: {e}")
            return False
    
    def load_config(self):
        """Load DeFi configuration"""
        self.config = security_manager.load_secure_config()
        return self.config
    
    async def auto_mine_liquidity(self):
        """Automatically mine liquidity rewards"""
        try:
            if not self.initialize():
                logger.warning("Liquidity mining skipped - Not configured")
                return
            
            if not all([self.w3, self.contract, self.account]):
                logger.warning("Liquidity mining skipped - Missing components")
                return
            
            # Check security
            if not security_manager.self_test():
                logger.warning("Security check failed - Mining aborted")
                return
            
            # Get available reserves
            reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
            available = reserves[0] if reserves and reserves[0] else 0
            
            if available < 100:  # Minimum threshold
                logger.info(f"Insufficient reserves for mining: {available:.2f} Eddies")
                return
            
            # Calculate mining amount (10% of reserves)
            mining_amount = available * 0.1
            
            # Check gas price
            gas_price = self.w3.eth.gas_price
            
            # Set reasonable gas price (max 50 gwei)
            max_gas = self.w3.to_wei("50", "gwei")
            recommended_gas = min(gas_price, max_gas)
            
            logger.info(f"Mining {mining_amount:.2f} Eddies into liquidity pool")
            logger.info(f"Gas price: {self.w3.from_wei(recommended_gas, 'gwei'):.1f} gwei")
            
            # Example: Add liquidity to a pool
            # This is a simplified example - actual implementation depends on the protocol
            try:
                # Get token addresses (example)
                token_a = self.w3.to_checksum_address("0x0000000000000000000000000000000000000000")  # Replace with actual
                token_b = self.w3.to_checksum_address("0x0000000000000000000000000000000000000000")  # Replace with actual
                
                # Build transaction
                nonce = self.w3.eth.get_transaction_count(self.account.address)
                
                tx = self.contract.functions.addLiquidityETH(
                    token_a,
                    int(mining_amount * 0.5 * 10**18),  # Half the amount
                    0,  # Min amount A
                    0,  # Min amount B
                    self.account.address,
                    int(time.time()) + 3600  # Deadline
                ).build_transaction({
                    "from": self.account.address,
                    "value": int(mining_amount * 0.5 * 10**18),  # Other half in ETH
                    "nonce": nonce,
                    "gas": 300000,
                    "gasPrice": recommended_gas
                })
                
                # Sign and send transaction
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                logger.info(f"Liquidity mining transaction sent: {tx_hash.hex()}")
                
                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                
                if receipt["status"] == 1:
                    logger.info("Liquidity successfully added - Earning passive Eddies!")
                    
                    # Track in database
                    db.execute_query(
                        """
                        INSERT INTO trades (id, symbol, side, amount, price, fee, leverage, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tx_hash.hex(),
                            "DEFI:LIQUIDITY",
                            "mine",
                            mining_amount,
                            0,
                            receipt["gasUsed"] * recommended_gas / 10**18,
                            1.0,
                            datetime.now().isoformat()
                        )
                    )
                else:
                    logger.error("Liquidity mining transaction failed")
                    
            except Exception as e:
                logger.error(f"Mining transaction failed: {e}")
                
        except Exception as e:
            logger.error(f"Auto liquidity mining failed: {e}")
    
    async def check_rewards(self):
        """Check pending rewards"""
        try:
            if not self.initialize():
                return 0
            
            if not all([self.contract, self.account]):
                return 0
            
            # Example: Check pending rewards
            # This depends on the specific protocol
            pending = self.contract.functions.pendingReward(
                0,  # Pool ID
                self.account.address
            ).call()
            
            rewards = pending / 10**18  # Convert from wei
            logger.info(f"Pending rewards: {rewards:.4f} tokens")
            
            return rewards
            
        except Exception as e:
            logger.error(f"Reward check failed: {e}")
            return 0
    
    async def harvest_rewards(self):
        """Harvest accumulated rewards"""
        try:
            if not self.initialize():
                return False
            
            if not all([self.contract, self.account]):
                return False
            
            # Check if rewards are worth harvesting
            rewards = await self.check_rewards()
            
            if rewards < 1:  # Minimum threshold
                logger.info("Rewards too small to harvest")
                return False
            
            # Build harvest transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = min(self.w3.eth.gas_price, self.w3.to_wei("50", "gwei"))
            
            tx = self.contract.functions.harvest(
                0  # Pool ID
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": 200000,
                "gasPrice": gas_price
            })
            
            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Harvest transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt["status"] == 1:
                logger.info(f"Harvested {rewards:.4f} tokens - Eddies secured!")
                return True
            else:
                logger.error("Harvest transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Harvest failed: {e}")
            return False
    
    def estimate_apy(self):
        """Estimate current APY for liquidity mining"""
        try:
            # This would typically fetch from the protocol or calculate based on rewards
            # Placeholder implementation
            base_apy = 15.0  # 15% base APY
            
            # Adjust based on market conditions
            market_multiplier = 1.0
            
            # Could fetch from protocol
            # apy = self.contract.functions.getAPY(0).call() / 100
            
            estimated_apy = base_apy * market_multiplier
            
            logger.info(f"Estimated liquidity mining APY: {estimated_apy:.1f}%")
            return estimated_apy
            
        except Exception as e:
            logger.error(f"APY estimation failed: {e}")
            return 0

# Create singleton instance
liquidity_miner = LiquidityMiner()
