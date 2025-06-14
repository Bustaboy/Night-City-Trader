
# Add this to handle simulation trades
@app.post("/simulation/trade")
async def simulation_trade(trade: TradeRequest):
    """Handle trades in simulation mode"""
    try:
        # Generate mock trade result
        trade_id = str(uuid.uuid4())
        
        # Simulate trade execution
        db.execute_query(
            """
            INSERT INTO trades (id, symbol, side, amount, price, fee, leverage, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_id,
                trade.symbol if ":" in trade.symbol else f"binance:{trade.symbol}",
                trade.side,
                trade.amount,
                45000.0,  # Mock price
                trade.amount * 45000.0 * 0.001,  # Mock fee
                trade.leverage,
                datetime.now().isoformat()
            )
        )
        
        # Update portfolio value
        current_value = db.get_portfolio_value()
        if trade.side == "buy":
            new_value = current_value - (trade.amount * 45000.0 * 1.001)
        else:
            new_value = current_value + (trade.amount * 45000.0 * 0.999)
        
        db.update_portfolio_value(new_value)
        
        return {
            "status": "trade_placed",
            "trade_id": trade_id,
            "message": "Simulation trade executed!"
        }
        
    except Exception as e:
        logger.error(f"Simulation trade failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Modify the main trade endpoint to check for simulation mode
original_trade = app.routes[5].endpoint  # Get the original trade endpoint

@app.post("/trade")
async def trade_wrapper(trade: TradeRequest):
    """Trade endpoint wrapper that handles simulation mode"""
    # Check if we have valid API keys
    if not settings.BINANCE_API_KEY or settings.BINANCE_API_KEY == "your_api_key_here":
        # Use simulation endpoint
        return await simulation_trade(trade)
    else:
        # Use real endpoint
        return await execute_trade(trade)
