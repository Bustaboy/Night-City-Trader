# api/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.database import db
from market.data_fetcher import DataFetcher
from trading.trading_bot import TradingBot
from config.settings import settings

app = FastAPI()
fetcher = DataFetcher()
bot = TradingBot()

class TradeRequest(BaseModel):
    symbol: str
    side: str  # buy/sell
    amount: float

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    try:
        data = fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"])
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    try:
        result = bot.execute_trade(trade.symbol, trade.side, trade.amount)
        return {"status": "trade_placed", "trade_id": result["id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/portfolio")
async def get_portfolio():
    trades = db.fetch_all("SELECT * FROM trades ORDER BY timestamp DESC")
    return {"trades": trades}
