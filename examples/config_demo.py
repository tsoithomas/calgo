"""Demonstration of Configuration Manager usage"""
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigurationManager
from src.config_models import Config, RiskParameters, TradingSchedule
from src.models import ExecutionMode
from datetime import time
from decimal import Decimal


def main():
    """Demonstrate configuration loading and validation"""
    
    # Create a dummy config for initialization
    dummy_config = Config(
        execution_mode=ExecutionMode.SIMULATION,
        data_sources=[],
        risk_parameters=RiskParameters(
            stop_loss_pct=Decimal("0.05"),
            take_profit_pct=Decimal("0.10"),
            max_position_size_pct=Decimal("0.20"),
            max_drawdown_pct=Decimal("0.15"),
            max_portfolio_value=Decimal("100000")
        ),
        active_models=[],
        trading_schedule=TradingSchedule(
            market_open=time(9, 30),
            market_close=time(16, 0),
            data_fetch_interval_seconds=300,
            trading_days=["MON"]
        ),
        broker_config=None,
        logging_config=None
    )
    
    manager = ConfigurationManager(dummy_config)
    
    # Load configuration from file
    config_path = "config/test_config.json"
    print(f"Loading configuration from: {config_path}")
    
    result = manager.load_config(config_path)
    
    if result.is_err():
        print(f"Error loading configuration: {result.unwrap_err()}")
        return
    
    config = result.unwrap()
    print("✓ Configuration loaded successfully!")
    
    # Update manager with loaded config
    manager = ConfigurationManager(config)
    
    # Display configuration details
    print("\n=== Configuration Details ===")
    print(f"Execution Mode: {manager.get_execution_mode().value}")
    
    print(f"\nData Sources ({len(manager.get_data_sources())}):")
    for ds in manager.get_data_sources():
        print(f"  - {ds.source.value} (priority: {ds.priority})")
    
    print(f"\nRisk Parameters:")
    risk = manager.get_risk_params()
    print(f"  - Stop Loss: {risk.stop_loss_pct * 100}%")
    print(f"  - Take Profit: {risk.take_profit_pct * 100}%")
    print(f"  - Max Position Size: {risk.max_position_size_pct * 100}%")
    print(f"  - Max Drawdown: {risk.max_drawdown_pct * 100}%")
    print(f"  - Max Portfolio Value: ${risk.max_portfolio_value:,.2f}")
    
    print(f"\nActive Models ({len(manager.get_active_models())}):")
    for model in manager.get_active_models():
        status = "enabled" if model.enabled else "disabled"
        print(f"  - {model.model_id} ({model.model_type}) - {status}")
    
    schedule = manager.get_trading_schedule()
    print(f"\nTrading Schedule:")
    print(f"  - Market Hours: {schedule.market_open} - {schedule.market_close}")
    print(f"  - Data Fetch Interval: {schedule.data_fetch_interval_seconds}s")
    print(f"  - Trading Days: {', '.join(schedule.trading_days)}")
    
    broker = manager.get_broker_config()
    print(f"\nBroker Configuration:")
    print(f"  - Broker: {broker.broker_name}")
    print(f"  - Base URL: {broker.base_url}")
    
    logging = manager.get_logging_config()
    print(f"\nLogging Configuration:")
    print(f"  - Directory: {logging.log_directory}")
    print(f"  - Level: {logging.log_level}")
    print(f"  - Rotation: {logging.rotation_policy}")


if __name__ == "__main__":
    main()
