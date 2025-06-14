# api/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.database import db
from market.data_fetcher import DataFetcher
from market.pair_selector import pair_selector
from trading.trading_bot import TradingBot
from trading.risk_manager import RiskManager
from config.settings import settings
from utils.logger import logger

app = FastAPI()
fetcher = DataFetcher()
bot = TradingBot()
risk_manager = RiskManager()

class TradeRequest(BaseModel):
    symbol: str
    side: str  # buy/sell
    amount: float
    risk_profile: str = "moderate"  # conservative, moderate, aggressive

class TestnetToggle(BaseModel):
    testnet: bool

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    try:
        data = await fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"])
        logger.info(f"Fetched market data for {symbol}")
        return {"data": data}
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    try:
        # Verify profitability after fees
        if not risk_manager.check_profitability(trade.symbol, trade.side, trade.amount):
            raise Exception("Trade rejected: Not profitable after fees")
        # Apply risk profile
        risk_manager.set_risk_profile(trade.risk_profile)
        if not risk_manager.check_trade_risk(trade.symbol, trade.side, trade.amount):
            raise Exception("Trade rejected due to risk limits")
        result = await bot.execute_trade(trade.symbol, trade.side, trade.amount)
        logger.info(f"Trade executed: {trade.symbol}, {trade.side}, {trade.amount}")
        return {"status": "trade_placed", "trade_id": result["id"]}
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    try:
        trades = db.fetch_all("SELECT * FROM trades ORDER BY timestamp DESC")
        positions = db.fetch_all("SELECT * FROM positions")
        logger.info("Portfolio data fetched")
        return {"trades": trades, "positions": positions}
    except Exception as e:
        logger.error(f"Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model():
    try:
        data = await fetcher.fetch_ohlcv(settings.TRADING["symbol"], settings.TRADING["timeframe"], limit=1000)
        bot.trainer.train(data)
        logger.info("ML model retrained")
        return {"status": "model_trained"}
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/best_pair")
async def get_best_pair():
    try:
        pair = await pair_selector.select_best_pair(settings.TRADING["timeframe"])
        logger.info(f"Best pair selected: {pair}")
        return {"pair": pair}
    except Exception as e:
        logger.error(f"Best pair selection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/testnet")
async def toggle_testnet(toggle: TestnetToggle):
    try:
        settings.TESTNET = toggle.testnet
        fetcher.exchange.set_sandbox_mode(toggle.testnet)
        bot.exchange.set_sandbox_mode(toggle.testnet)
        pair_selector.exchange.set_sandbox_mode(toggle.testnet)
        logger.info(f"Testnet mode set to: {toggle.testnet}")
        return {"status": "testnet_updated", "testnet": toggle.testnet}
    except Exception as e:
        logger.error(f"Testnet toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
