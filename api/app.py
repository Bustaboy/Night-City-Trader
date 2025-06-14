# api/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.database import db
from market.data_fetcher import DataFetcher
from market.pair_selector import PairSelector
from market.sentiment_analyzer import SentimentAnalyzer
from trading.trading_bot import TradingBot
from trading.risk_manager import RiskManager
from config.settings import settings
from utils.logger import logger
import numpy as np

app = FastAPI(title="Arasaka Neural-Net Trading Matrix")
fetcher = DataFetcher()
bot = TradingBot()
risk_manager = RiskManager()
pair_selector = PairSelector()
sentiment_analyzer = SentimentAnalyzer()

class TradeRequest(BaseModel):
    symbol: str
    side: str  # buy/sell
    amount: float
    risk_profile: str = "moderate"  # conservative, moderate, aggressive

class TestnetToggle(BaseModel):
    testnet: bool

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    strategy: str  # breakout, mean_reversion, etc.

@app.get("/health")
async def health_check():
    logger.info("Netrunner health check initiated")
    return {"status": "cybernetically enhanced"}

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    try:
        data = await fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"])
        logger.info(f"Retrieved OHLCV data for {symbol} in the Net")
        return {"data": data}
    except Exception as e:
        logger.error(f"Data retrieval error in the Net: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    try:
        # Check sentiment
        sentiment_score = await sentiment_analyzer.get_sentiment(trade.symbol)
        if sentiment_score < -0.5 and trade.side == "buy":
            raise Exception("Trade rejected: Bearish sentiment detected")
        
        # Verify profitability after fees
        if not risk_manager.check_profitability(trade.symbol, trade.side, trade.amount):
            raise Exception("Trade rejected: Insufficient Eurodollars after fees")
        
        # Apply risk profile and adaptive sizing
        risk_manager.set_risk_profile(trade.risk_profile)
        adjusted_amount = risk_manager.adjust_position_size(trade.symbol, trade.amount)
        if not risk_manager.check_trade_risk(trade.symbol, trade.side, adjusted_amount):
            raise Exception("Trade rejected: Arasaka risk protocols breached")
        
        result = await bot.execute_trade(trade.symbol, trade.side, adjusted_amount)
        logger.info(f"Trade executed in the Matrix: {trade.symbol}, {side}, {adjusted_amount} Eddies")
        return {"status": "trade_placed", "trade_id": result["id"]}
    except Exception as e:
        logger.error(f"Trade execution failed in the Net: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    try:
        trades = db.fetch_all("SELECT * FROM trades ORDER BY timestamp DESC")
        positions = db.fetch_all("SELECT * FROM positions")
        optimized_weights = risk_manager.optimize_portfolio()
        logger.info("Netrunner's portfolio data fetched")
        return {"trades": trades, "positions": positions, "optimized_weights": optimized_weights}
    except Exception as e:
        logger.error(f"Portfolio fetch failed in the Matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model():
    try:
        data = await fetcher.fetch_ohlcv(settings.TRADING["symbol"], settings.TRADING["timeframe"], limit=1000)
        bot.trainer.train(data)
        bot.rl_trainer.train(data)  # Train RL model
        logger.info("Neural-Net retrained for maximum Eurodollars")
        return {"status": "model_trained"}
    except Exception as e:
        logger.error(f"Neural-Net training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/best_pair")
async def get_best_pair():
    try:
        pair = await pair_selector.select_best_pair(settings.TRADING["timeframe"])
        logger.info(f"Optimal pair locked in: {pair}")
        return {"pair": pair}
    except Exception as e:
        logger.error(f"Pair selection error in the Net: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/testnet")
async def toggle_testnet(toggle: TestnetToggle):
    try:
        settings.TESTNET = toggle.testnet
        fetcher.exchange.set_sandbox_mode(toggle.testnet)
        bot.exchange.set_sandbox_mode(toggle.testnet)
        pair_selector.exchange.set_sandbox_mode(toggle.testnet)
        logger.info(f"Testnet mode switched to: {toggle.testnet}")
        return {"status": "testnet_updated", "testnet": toggle.testnet}
    except Exception as e:
        logger.error(f"Testnet toggle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage")
async def detect_arbitrage():
    try:
        opportunities = await pair_selector.detect_arbitrage()
        logger.info(f"Arbitrage scan completed: {len(opportunities)} opportunities found")
        return {"opportunities": opportunities}
    except Exception as e:
        logger.error(f"Arbitrage detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market_regime")
async def get_market_regime():
    try:
        regime = await bot.detect_market_regime()
        logger.info(f"Market regime identified: {regime}")
        return {"regime": regime}
    except Exception as e:
        logger.error(f"Market regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        result = await bot.backtest_strategy(request.symbol, request.timeframe, request.start_date, request.end_date, request.strategy)
        logger.info(f"Backtest completed for {request.symbol} using {request.strategy}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
