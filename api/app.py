# api/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.database import db
from market.data_fetcher import DataFetcher
from market.pair_selector import PairSelector
from market.sentiment_analyzer import SentimentAnalyzer
from market.social_signal_analyzer import SocialSignalAnalyzer
from market.onchain_analyzer import OnChainAnalyzer
from trading.trading_bot import TradingBot
from trading.risk_manager import RiskManager
from config.settings import settings
from utils.logger import logger

app = FastAPI(title="Arasaka Neural-Net Trading Matrix")
fetcher = DataFetcher()
bot = TradingBot()
risk_manager = RiskManager()
pair_selector = PairSelector()
sentiment_analyzer = SentimentAnalyzer()
social_analyzer = SocialSignalAnalyzer()
onchain_analyzer = OnChainAnalyzer()

class TradeRequest(BaseModel):
    symbol: str
    side: str
    amount: float
    risk_profile: str = "moderate"
    leverage: float = 1.0

class TestnetToggle(BaseModel):
    testnet: bool

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    strategy: str

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
        logger.error(f"Data retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    try:
        # Validate with sentiment, social, and on-chain signals
        sentiment_score = await sentiment_analyzer.get_sentiment(trade.symbol)
        social_score = await social_analyzer.get_signal(trade.symbol)
        onchain_score = await onchain_analyzer.get_metrics(trade.symbol)
        if sentiment_score < -0.5 or social_score < 0 or onchain_score < 0:
            raise Exception("Trade rejected: Negative market signals")

        # Verify profitability
        if not risk_manager.check_profitability(trade.symbol, trade.side, trade.amount, trade.leverage):
            raise Exception("Trade rejected: Insufficient Eurodollars after fees")

        # Apply risk profile and adaptive sizing
        risk_manager.set_risk_profile(trade.risk_profile)
        adjusted_amount = risk_manager.adjust_position_size(trade.symbol, trade.amount)
        if not risk_manager.check_trade_risk(trade.symbol, trade.side, adjusted_amount, trade.leverage):
            raise Exception("Trade rejected: Arasaka risk protocols breached")

        # Execute trade with smart routing and SL/TP
        result = await bot.execute_trade(trade.symbol, trade.side, adjusted_amount, trade.leverage)
        logger.info(f"Trade executed: {trade.symbol}, {trade.side}, {adjusted_amount} Eddies")
        return {"status": "trade_placed", "trade_id": result["id"]}
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    try:
        trades = db.fetch_all("SELECT * FROM trades ORDER BY timestamp DESC")
        positions = db.fetch_all("SELECT * FROM positions")
        optimized_weights = risk_manager.optimize_portfolio()
        logger.info("Netrunner's portfolio fetched")
        return {"trades": trades, "positions": positions, "optimized_weights": optimized_weights}
    except Exception as e:
        logger.error(f"Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model():
    try:
        data = await fetcher.fetch_ohlcv(settings.TRADING["symbol"], settings.TRADING["timeframe"], limit=1000)
        bot.trainer.train(data)
        bot.rl_trainer.train(data)
        logger.info("Neural-Net retrained for maximum Eurodollars")
        return {"status": "model_trained"}
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/best_pair")
async def get_best_pair():
    try:
        pair = await pair_selector.select_best_pair(settings.TRADING["timeframe"])
        logger.info(f"Optimal pair locked: {pair}")
        return {"pair": pair}
    except Exception as e:
        logger.error(f"Pair selection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/testnet")
async def toggle_testnet(toggle: TestnetToggle):
    try:
        settings.TESTNET = toggle.testnet
        fetcher.set_sandbox_mode(toggle.testnet)
        bot.set_sandbox_mode(toggle.testnet)
        pair_selector.set_sandbox_mode(toggle.testnet)
        logger.info(f"Testnet mode: {toggle.testnet}")
        return {"status": "testnet_updated", "testnet": toggle.testnet}
    except Exception as e:
        logger.error(f"Testnet toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage")
async def detect_arbitrage():
    try:
        opportunities = await pair_selector.detect_arbitrage()
        logger.info(f"Arbitrage scan: {len(opportunities)} opportunities")
        return {"opportunities": opportunities}
    except Exception as e:
        logger.error(f"Arbitrage detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market_regime")
async def get_market_regime():
    try:
        regime = await bot.detect_market_regime()
        logger.info(f"Market regime: {regime}")
        return {"regime": regime}
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        result = await bot.backtest_strategy(request.symbol, request.timeframe, request.start_date, request.end_date, request.strategy)
        logger.info(f"Backtest for {request.symbol} using {request.strategy}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
