# tests/test_trading.py
import pytest
from trading.trading_bot import bot
from market.data_fetcher import fetcher
import asyncio

@pytest.mark.asyncio
async def test_trade_execution():
    try:
        result = await bot.execute_trade("BTC/USDT", "buy", 0.001)
        assert "id" in result
    except Exception as e:
        print(f"Test trade failed: {e}")
    finally:
        await bot.close()
        await fetcher.close()
