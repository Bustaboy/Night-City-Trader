# scripts/setup_database.py
"""
Database setup script for the Arasaka Neural-Net Trading Matrix
Run this before first use to initialize the database
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db
from utils.logger import logger

def setup_database():
    """Initialize database with all required tables"""
    try:
        logger.info("=" * 60)
        logger.info("Arasaka Database Setup")
        logger.info("=" * 60)
        
        # Database is already initialized in __init__
        # Just verify tables exist
        tables = [
            "trades",
            "positions", 
            "market_data",
            "historical_data",
            "market_regimes",
            "seasonality_patterns",
            "reserves",
            "tax_rates",
            "portfolio"
        ]
        
        for table in tables:
            try:
                count = db.fetch_one(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"✓ Table '{table}' exists with {count[0]} records")
            except Exception as e:
                logger.error(f"✗ Table '{table}' check failed: {e}")
                # Try to recreate
                db.init_tables()
        
        # Insert default tax rates
        logger.info("\nInserting default tax rates...")
        default_rates = [
            ("US", 0.30),
            ("Germany", 0.25),
            ("UK", 0.20),
            ("Portugal", 0.00),
            ("Canada", 0.50),
            ("Japan", 0.20),
            ("Default", 0.30)
        ]
        
        for country, rate in default_rates:
            try:
                db.execute_query(
                    "INSERT OR REPLACE INTO tax_rates (country, rate) VALUES (?, ?)",
                    (country, rate)
                )
                logger.info(f"  Added tax rate: {country} = {rate*100:.0f}%")
            except Exception as e:
                logger.error(f"  Failed to add {country}: {e}")
        
        # Initialize portfolio with starting value
        try:
            current_value = db.get_portfolio_value()
            if current_value == 100:  # Default value
                db.update_portfolio_value(1000)  # Start with 1000 Eddies
                logger.info("\nInitialized portfolio with 1000 Eddies")
        except:
            pass
        
        logger.info("\n" + "=" * 60)
        logger.info("Database setup complete - Ready to jack into the Matrix!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    setup_database()
