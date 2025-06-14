# api/app.py
"""
Arasaka Neural-Net Trading Matrix API - RESTful interface for the trading bot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import Optional

from config.settings import settings
from core.database import db
from utils.logger import logger

# Initialize FastAPI
app = FastAPI(
    title="Arasaka Neural-Net Trading Matrix",
    description="Cyberpunk-themed AI crypto trading system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy imports to avoid circular dependencies
bot = None
risk_manager = None
fetcher = None
pair_selector = None
sentiment_analyzer = None
social_analyzer = None
onchain_analyzer = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global bot, risk_manager, fetcher, pair_selector
    global sentiment_analyzer, social_analyzer, onchain_analyzer
    
    try:
        # Import components
        from trading.trading_bot import bot as trading_bot
        from trading.risk_manager import risk_manager as risk_mgr
        from market.data_fetcher import fetcher as data_fetcher
        from market.pair_selector import pair_selector as pair_sel
        
        bot = trading_bot
        risk_manager = risk_mgr
        fetcher = data_fetcher
        pair_selector = pair_sel
        
        # Initialize components
        await bot.initialize()
        await fetcher.initialize()
        await pair_selector.initialize()
        
        logger.info("API components initialized - Neural-Net online!")
        
        # Try to import optional components
        try:
            from market.sentiment_analyzer import sentiment_analyzer as sent_analyzer
            sentiment_analyzer = sent_analyzer
        except:
            logger.warning("Sentiment analyzer not available")
            
        try:
            from market.social_signal_analyzer import social_analyzer as soc_analyzer
            social_analyzer = soc_analyzer
        except:
            logger.warning("Social analyzer not available")
            
        try:
            from market.onchain_analyzer import onchain_analyzer as chain_analyzer
            onchain_analyzer = chain_analyzer
        except:
            logger.warning("On-chain analyzer not available")
            
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if bot:
            await bot.close()
        if fetcher:
            await fetcher.close()
        if pair_selector:
            await pair_selector.close()
        logger.info("API shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Request/Response models
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

class PredictionRequest(BaseModel):
    symbol: str

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Arasaka Neural-Net Trading Matrix",
        "status": "online",
        "mode": "testnet" if settings.TESTNET else "live"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        portfolio_value = db.get_portfolio_value()
        
        return {
            "status": "cybernetically enhanced",
            "portfolio_value": portfolio_value,
            "testnet": settings.TESTNET
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="System malfunction")

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol"""
    try:
        if not fetcher:
            raise HTTPException(status_code=503, detail="Data fetcher offline")
            
        data = await fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"])
        
        return {
            "symbol": symbol,
            "timeframe": settings.TRADING["timeframe"],
            "data": data[-100:] if data else []  # Last 100 candles
        }
    except Exception as e:
        logger.error(f"Market data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    """Execute a trade"""
    try:
        if not bot or not risk_manager:
            raise HTTPException(status_code=503, detail="Trading bot offline")
        
        # Set risk profile
        risk_manager.set_risk_profile(trade.risk_profile)
        
        # Check profitability
        if not risk_manager.check_profitability(
            trade.symbol, trade.side, trade.amount, trade.leverage
        ):
            raise HTTPException(
                status_code=400, 
                detail="Trade rejected: Insufficient profit after fees"
            )
        
        # Check risk
        if not risk_manager.check_trade_risk(
            trade.symbol, trade.side, trade.amount, trade.leverage
        ):
            raise HTTPException(
                status_code=400,
                detail="Trade rejected: Risk parameters exceeded"
            )
        
        # Execute trade
        result = await bot.execute_trade(
            trade.symbol, trade.side, trade.amount, trade.leverage
        )
        
        return {
            "status": "trade_placed",
            "trade_id": result["id"],
            "message": "Trade executed - Eddies stacked!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    """Get portfolio information"""
    try:
        # Get trades
        trades = db.fetch_all(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 50"
        )
        
        # Get positions
        positions = db.fetch_all("SELECT * FROM positions")
        
        # Get portfolio value
        portfolio_value = db.get_portfolio_value()
        
        # Get optimized weights if available
        optimized_weights = {}
        if risk_manager:
            optimized_weights = risk_manager.optimize_portfolio()
        
        return {
            "portfolio_value": portfolio_value,
            "trades": [
                {
                    "id": t[0],
                    "symbol": t[1],
                    "side": t[2],
                    "amount": t[3],
                    "price": t[4],
                    "fee": t[5],
                    "leverage": t[6],
                    "timestamp": t[7]
                } for t in trades
            ],
            "positions": [
                {
                    "id": p[0],
                    "symbol": p[1],
                    "side": p[2],
                    "amount": p[3],
                    "entry_price": p[4],
                    "stop_loss": p[5],
                    "take_profit": p[6],
                    "timestamp": p[7]
                } for p in positions
            ],
            "optimized_weights": optimized_weights
        }
        
    except Exception as e:
        logger.error(f"Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model():
    """Train ML and RL models"""
    try:
        if not bot:
            raise HTTPException(status_code=503, detail="Trading bot offline")
        
        # Import trainers
        from ml.trainer import trainer
        from ml.rl_trainer import rl_trainer
        
        # Fetch training data
        data = await fetcher.fetch_ohlcv(
            settings.TRADING["symbol"],
            settings.TRADING["timeframe"],
            limit=1000
        )
        
        if not data:
            raise HTTPException(status_code=400, detail="No data available for training")
        
        # Train models
        await trainer.train(data)
        await rl_trainer.train(data)
        
        return {
            "status": "model_trained",
            "message": "Neural-Net enhanced with new training data!"
        }
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{symbol}")
async def get_prediction(symbol: str):
    """Get ML/RL predictions for a symbol"""
    try:
        if not bot:
            raise HTTPException(status_code=503, detail="Trading bot offline")
            
        from ml.trainer import trainer
        from ml.rl_trainer import rl_trainer
        
        # Get latest data
        data = await fetcher.fetch_ohlcv(symbol, "1h", limit=1)
        
        if not data:
            raise HTTPException(status_code=400, detail="No data available")
        
        # Get predictions
        ml_prediction = trainer.predict(data[0])
        rl_action = rl_trainer.predict(data[0])
        
        # Calculate confidence
        state = bot.prepare_state(data[0])
        state_array = np.array(state).reshape(1, -1)
        
        try:
            rl_predictions = rl_trainer.model.predict(state_array, verbose=0)
            confidence = float(np.max(rl_predictions)) if rl_predictions.size > 0 else 0.5
        except:
            confidence = 0.5
        
        return {
            "symbol": symbol,
            "ml_prediction": int(ml_prediction),
            "rl_action": float(rl_action),
            "confidence": confidence,
            "recommendation": "buy" if ml_prediction == 1 and rl_action < 0.5 else "sell" if ml_prediction == 0 and rl_action > 0.5 else "hold"
        }
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/best_pair")
async def get_best_pair():
    """Get the best trading pair"""
    try:
        if not pair_selector:
            raise HTTPException(status_code=503, detail="Pair selector offline")
            
        pair = await pair_selector.select_best_pair(settings.TRADING["timeframe"])
        
        return {
            "pair": pair,
            "message": "Optimal pair locked for maximum Eddies!"
        }
        
    except Exception as e:
        logger.error(f"Pair selection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/testnet")
async def toggle_testnet(toggle: TestnetToggle):
    """Toggle testnet mode"""
    try:
        settings.TESTNET = toggle.testnet
        
        if fetcher:
            fetcher.set_sandbox_mode(toggle.testnet)
        if bot:
            bot.set_sandbox_mode(toggle.testnet)
        if pair_selector:
            pair_selector.set_sandbox_mode(toggle.testnet)
        
        return {
            "status": "testnet_updated",
            "testnet": toggle.testnet,
            "message": f"{'Test' if toggle.testnet else 'Live'} mode activated!"
        }
        
    except Exception as e:
        logger.error(f"Testnet toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/arbitrage")
async def detect_arbitrage():
    """Detect arbitrage opportunities"""
    try:
        if not pair_selector:
            raise HTTPException(status_code=503, detail="Pair selector offline")
            
        opportunities = await pair_selector.detect_arbitrage()
        
        return {
            "opportunities": opportunities[:10],  # Top 10 opportunities
            "count": len(opportunities),
            "message": f"Found {len(opportunities)} arbitrage opportunities!"
        }
        
    except Exception as e:
        logger.error(f"Arbitrage detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market_regime")
async def get_market_regime():
    """Get current market regime"""
    try:
        if not bot:
            raise HTTPException(status_code=503, detail="Trading bot offline")
            
        regime = await bot.detect_market_regime()
        
        return {
            "regime": regime,
            "message": f"Market in {regime} mode - Adjust strategy accordingly!"
        }
        
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run strategy backtest"""
    try:
        if not bot:
            raise HTTPException(status_code=503, detail="Trading bot offline")
            
        result = await bot.backtest_strategy(
            request.symbol,
            request.timeframe,
            request.start_date,
            request.end_date,
            request.strategy
        )
        
        return {
            "result": result,
            "message": "Backtest complete - Check the metrics!"
        }
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preload_data")
async def preload_data():
    """Preload historical data"""
    try:
        if not fetcher:
            raise HTTPException(status_code=503, detail="Data fetcher offline")
            
        await fetcher.preload_historical_data()
        
        return {
            "status": "data_preloaded",
            "message": "Historical data jacked into the Matrix!"
        }
        
    except Exception as e:
        logger.error(f"Data preload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Get sentiment analysis (if available)"""
    try:
        if not sentiment_analyzer:
            return {
                "symbol": symbol,
                "score": 0.0,
                "message": "Sentiment analyzer not configured"
            }
            
        sentiment = await sentiment_analyzer.analyze_sentiment(symbol)
        
        return {
            "symbol": symbol,
            "score": sentiment.get("score", 0.0),
            "message": "Sentiment analyzed from the Net!"
        }
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {"symbol": symbol, "score": 0.0, "message": "Analysis unavailable"}

@app.get("/onchain/{symbol}")
async def get_onchain_metrics(symbol: str):
    """Get on-chain metrics (if available)"""
    try:
        if not onchain_analyzer:
            return {
                "symbol": symbol,
                "metrics": {},
                "message": "On-chain analyzer not configured"
            }
            
        metrics = await onchain_analyzer.get_metrics(symbol)
        
        return {
            "symbol": symbol,
            "metrics": metrics,
            "message": "On-chain data retrieved!"
        }
        
    except Exception as e:
        logger.error(f"On-chain analysis failed: {e}")
        return {"symbol": symbol, "metrics": {}, "message": "Analysis unavailable"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
