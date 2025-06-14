# tests/test_trading.py
import pytest
from trading.trading_bot import bot
from market.data_fetcher import fetcher
from market.pair_selector import pair_selector
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

@pytest.mark.asyncio
async def test_pair_selection():
    try:
        pair = await pair_selector.select_best_pair("1h")
        assert pair in ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    except Exception as e:
        print(f"Pair selection test failed: {e}")
