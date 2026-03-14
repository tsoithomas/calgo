"""Calgo System Core - Main orchestration and state machine"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from src.models import SystemState, Signal, PriceData, PortfolioSnapshot, DataSource, Recommendation, ExecutionMode
from src.result import Result
from src.config_manager import ConfigurationManager
from src.market_data_ingester import MarketDataIngester
from src.signal_generator import SignalGenerator
from src.portfolio_manager import PortfolioManager
from src.trade_executor import TradeExecutor
from src.risk_manager import RiskManager
from src.logger import Logger
from src.analytics_engine import AnalyticsEngine
from src.cache_manager import CacheManager, CacheEntry, CacheError


class StateTransitionError(Exception):
    """Invalid state transition attempted"""
    pass


class CalgoSystem:
    """
    Main Calgo trading system orchestrator.
    
    Manages system lifecycle through state machine:
    INITIALIZING -> READY -> RUNNING -> HALTED -> SHUTDOWN
                      ^         |
                      |_________|
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        SystemState.INITIALIZING: [SystemState.READY, SystemState.SHUTDOWN],
        SystemState.READY: [SystemState.RUNNING, SystemState.SHUTDOWN],
        SystemState.RUNNING: [SystemState.HALTED, SystemState.SHUTDOWN],
        SystemState.HALTED: [SystemState.READY, SystemState.SHUTDOWN],
        SystemState.SHUTDOWN: []  # Terminal state
    }
    
    def __init__(self):
        """Initialize Calgo system in INITIALIZING state"""
        self._state = SystemState.INITIALIZING
        self._config_manager: Optional[ConfigurationManager] = None
        self._cache_manager: Optional[CacheManager] = None
        self._market_data_ingester: Optional[MarketDataIngester] = None
        self._signal_generator: Optional[SignalGenerator] = None
        self._portfolio_manager: Optional[PortfolioManager] = None
        self._trade_executor: Optional[TradeExecutor] = None
        self._risk_manager: Optional[RiskManager] = None
        self._logger: Optional[Logger] = None
        self._analytics_engine: Optional[AnalyticsEngine] = None
    
    @property
    def state(self) -> SystemState:
        """Get current system state"""
        return self._state
    
    def transition_to(self, new_state: SystemState) -> Result[SystemState, str]:
        """
        Transition to a new state with validation.
        
        Args:
            new_state: Target state to transition to
            
        Returns:
            Result containing new state or error message
        """
        if not self._is_valid_transition(self._state, new_state):
            return Result.err(
                f"Invalid state transition: {self._state.value} -> {new_state.value}. "
                f"Valid transitions from {self._state.value}: "
                f"{[s.value for s in self.VALID_TRANSITIONS[self._state]]}"
            )
        
        old_state = self._state
        self._state = new_state
        
        # Log state transition if logger is available
        if self._logger:
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "INFO",
                "component": "CalgoSystem",
                "message": f"State transition: {old_state.value} -> {new_state.value}"
            })
        
        return Result.ok(new_state)
    
    def _is_valid_transition(self, from_state: SystemState, to_state: SystemState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is valid, False otherwise
        """
        return to_state in self.VALID_TRANSITIONS.get(from_state, [])
    
    def can_transition_to(self, target_state: SystemState) -> bool:
        """
        Check if system can transition to target state.
        
        Args:
            target_state: State to check
            
        Returns:
            True if transition is valid, False otherwise
        """
        return self._is_valid_transition(self._state, target_state)
    
    def get_valid_transitions(self) -> List[SystemState]:
        """
        Get list of valid transitions from current state.
        
        Returns:
            List of valid target states
        """
        return self.VALID_TRANSITIONS.get(self._state, [])

    
    def initialize(self, config_path: str, symbols: List[str] = None) -> Result[None, str]:
        """
        Initialize system components from configuration file.
        
        Loads configuration, initializes all components, and transitions to READY state.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Result indicating success or error message
        """
        try:
            # Load configuration
            temp_config_manager = ConfigurationManager(None)
            config_result = temp_config_manager.load_config(config_path)
            
            if config_result.is_err():
                error_msg = f"Configuration loading failed: {config_result.unwrap_err()}"
                if self._logger:
                    self._logger.log_error({
                        "timestamp": datetime.now().isoformat(),
                        "severity": "CRITICAL",
                        "component": "CalgoSystem",
                        "message": error_msg
                    })
                return Result.err(error_msg)
            
            config = config_result.unwrap()
            self._config_manager = ConfigurationManager(config)
            
            # Initialize CacheManager (non-fatal if it fails)
            try:
                self._cache_manager = CacheManager(self._config_manager.get_cache_config())
            except CacheError as e:
                if self._logger:
                    self._logger.log_error({
                        "timestamp": datetime.now().isoformat(),
                        "severity": "WARNING",
                        "component": "CalgoSystem",
                        "message": f"CacheManager initialization failed (non-fatal): {e}"
                    })
                self._cache_manager = None
            
            # Initialize Logger first (needed by other components)
            from src.logger import Logger
            logging_config = self._config_manager.get_logging_config()
            self._logger = Logger(
                log_directory=logging_config.log_directory,
                log_level=logging_config.log_level
            )
            
            # Initialize Market Data Ingester
            from src.data_sources import YahooFinanceAdapter, AlpacaAdapter
            from src.market_data_ingester import MarketDataIngester
            
            adapters = {}
            data_source_configs = self._config_manager.get_data_sources()
            for ds_config in data_source_configs:
                if ds_config.source == DataSource.YAHOO_FINANCE:
                    adapters[DataSource.YAHOO_FINANCE] = YahooFinanceAdapter(ds_config.api_key)
                elif ds_config.source == DataSource.ALPACA:
                    adapters[DataSource.ALPACA] = AlpacaAdapter(
                        api_key=ds_config.api_key,
                        api_secret=ds_config.api_secret
                    )
            
            self._market_data_ingester = MarketDataIngester(adapters, data_source_configs)
            
            # Initialize Signal Generator
            from src.signal_generator import SignalGenerator, AggregationStrategy
            self._signal_generator = SignalGenerator(AggregationStrategy.VOTING)
            
            # Load and activate models
            from src.trading_models import MovingAverageCrossover, MLClassifierModel
            model_configs = self._config_manager.get_active_models()
            active_model_ids = []
            
            for model_config in model_configs:
                if not model_config.enabled:
                    continue
                
                if model_config.model_type == "moving_average_crossover":
                    model = MovingAverageCrossover(
                        model_id=model_config.model_id,
                        short_window=model_config.parameters.get("short_window", 20),
                        long_window=model_config.parameters.get("long_window", 50)
                    )
                    self._signal_generator.add_model(model)
                    active_model_ids.append(model_config.model_id)
                elif model_config.model_type == "ml_classifier":
                    model = MLClassifierModel(model_id=model_config.model_id)
                    self._signal_generator.add_model(model)
                    active_model_ids.append(model_config.model_id)
            
            if active_model_ids:
                self._signal_generator.set_active_models(active_model_ids)
            
            # Initialize Portfolio Manager
            from src.portfolio_manager import PortfolioManager
            risk_params = self._config_manager.get_risk_params()
            self._portfolio_manager = PortfolioManager(
                initial_cash=risk_params.max_portfolio_value,
                max_position_size_pct=risk_params.max_position_size_pct,
                max_portfolio_value=risk_params.max_portfolio_value
            )
            
            # Initialize Risk Manager
            from src.risk_manager import RiskManager
            self._risk_manager = RiskManager(risk_params)
            
            # Initialize Trade Executor
            from src.trade_executor import TradeExecutor
            from src.paper_broker_adapter import PaperBrokerAdapter
            from src.live_broker_adapter import LiveBrokerAdapter
            
            execution_mode = self._config_manager.get_execution_mode()
            broker_config = self._config_manager.get_broker_config()
            
            if execution_mode == ExecutionMode.SIMULATION:
                broker_adapter = PaperBrokerAdapter(
                    api_key=broker_config.api_key,
                    api_secret=broker_config.api_secret,
                    base_url=broker_config.base_url
                )
            else:
                broker_adapter = LiveBrokerAdapter(
                    api_key=broker_config.api_key,
                    api_secret=broker_config.api_secret,
                    base_url=broker_config.base_url
                )
            
            self._trade_executor = TradeExecutor(execution_mode, broker_adapter)
            
            # Initialize Analytics Engine
            from src.analytics_engine import AnalyticsEngine
            self._analytics_engine = AnalyticsEngine(self._logger)
            
            # Seed price history from cache (non-fatal)
            if self._cache_manager is not None:
                try:
                    seed_symbols: List[str] = list(symbols) if symbols else []
                    if not seed_symbols:
                        # Fall back to symbols declared in model parameters
                        for model_config in model_configs:
                            if model_config.enabled:
                                for sym in model_config.parameters.get("symbols", []):
                                    if sym not in seed_symbols:
                                        seed_symbols.append(sym)
                    if seed_symbols:
                        self._seed_price_history(seed_symbols)
                except Exception as e:
                    if self._logger:
                        self._logger.log_error({
                            "timestamp": datetime.now().isoformat(),
                            "severity": "WARNING",
                            "component": "CalgoSystem",
                            "message": f"Price history seeding failed (non-fatal): {e}"
                        })
            
            # Transition to READY state
            transition_result = self.transition_to(SystemState.READY)
            if transition_result.is_err():
                return Result.err(f"Failed to transition to READY: {transition_result.unwrap_err()}")
            
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "INFO",
                "component": "CalgoSystem",
                "message": "System initialization complete"
            })
            
            return Result.ok(None)
            
        except Exception as e:
            error_msg = f"System initialization failed: {str(e)}"
            if self._logger:
                self._logger.log_error({
                    "timestamp": datetime.now().isoformat(),
                    "severity": "CRITICAL",
                    "component": "CalgoSystem",
                    "message": error_msg,
                    "exception": str(e)
                })
            return Result.err(error_msg)
    
    def start_trading(self, symbols: List[str]) -> Result[None, str]:
        """
        Start the main trading loop.
        
        Transitions to RUNNING state and begins autonomous trading operations.
        
        Args:
            symbols: List of symbols to trade
            
        Returns:
            Result indicating success or error message
        """
        if self._state != SystemState.READY:
            return Result.err(f"Cannot start trading from state {self._state.value}. Must be in READY state.")
        
        # Transition to RUNNING
        transition_result = self.transition_to(SystemState.RUNNING)
        if transition_result.is_err():
            return Result.err(f"Failed to transition to RUNNING: {transition_result.unwrap_err()}")
        
        self._logger.log_error({
            "timestamp": datetime.now().isoformat(),
            "severity": "INFO",
            "component": "CalgoSystem",
            "message": f"Starting trading loop for symbols: {symbols}"
        })
        
        # Main trading loop
        import time
        trading_schedule = self._config_manager.get_trading_schedule()
        fetch_interval = trading_schedule.data_fetch_interval_seconds
        
        try:
            while self._state == SystemState.RUNNING:
                # Check if trading is halted by risk manager
                portfolio_snapshot = self._portfolio_manager.get_snapshot()
                if self._risk_manager.is_trading_halted(portfolio_snapshot):
                    self._logger.log_error({
                        "timestamp": datetime.now().isoformat(),
                        "severity": "WARNING",
                        "component": "CalgoSystem",
                        "message": "Trading halted by risk manager"
                    })
                    self.transition_to(SystemState.HALTED)
                    break
                
                # Process each symbol
                for symbol in symbols:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self._logger.log_error({
                            "timestamp": datetime.now().isoformat(),
                            "severity": "ERROR",
                            "component": "CalgoSystem",
                            "message": f"Error processing symbol {symbol}: {str(e)}"
                        })
                
                # Wait for next fetch interval
                time.sleep(fetch_interval)
                
        except KeyboardInterrupt:
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "INFO",
                "component": "CalgoSystem",
                "message": "Trading loop interrupted by user"
            })
            self.shutdown()
        except Exception as e:
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "CRITICAL",
                "component": "CalgoSystem",
                "message": f"Critical error in trading loop: {str(e)}"
            })
            self.transition_to(SystemState.HALTED)
            return Result.err(f"Trading loop failed: {str(e)}")
        
        return Result.ok(None)
    
    def _process_symbol(self, symbol: str) -> None:
        """
        Process a single symbol through the trading pipeline.
        
        Steps:
        1. Fetch market data
        2. Generate signal
        3. Evaluate signal with risk manager
        4. Execute approved trades
        5. Update portfolio
        6. Log all state changes
        
        Args:
            symbol: Symbol to process
        """
        # 1. Fetch market data
        market_data_result = self._market_data_ingester.fetch_realtime(symbol)
        if market_data_result.is_err():
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "WARNING",
                "component": "CalgoSystem",
                "message": f"Failed to fetch market data for {symbol}: {market_data_result.unwrap_err()}"
            })
            return
        
        market_data = market_data_result.unwrap()
        
        # 2. Generate signal
        portfolio_snapshot = self._portfolio_manager.get_snapshot()
        signal = self._signal_generator.generate_signal(market_data, portfolio_snapshot)
        
        # Log signal
        self._logger.log_signal(signal)
        
        # 3. Check for protective signals (stop-loss, take-profit)
        protective_signals = self._risk_manager.generate_protective_signals(portfolio_snapshot)
        if protective_signals:
            for protective_signal in protective_signals:
                self._logger.log_signal(protective_signal)
                self._execute_signal(protective_signal, market_data)
        
        # 4. Evaluate signal with risk manager
        evaluation_result = self._risk_manager.evaluate_signal(signal, portfolio_snapshot)
        if evaluation_result.is_err():
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "INFO",
                "component": "CalgoSystem",
                "message": f"Signal rejected by risk manager: {evaluation_result.unwrap_err()}"
            })
            return
        
        # 5. Execute approved signal
        self._execute_signal(signal, market_data)
    
    def _execute_signal(self, signal: Signal, market_data: PriceData) -> None:
        """
        Execute a trading signal.
        
        Args:
            signal: Signal to execute
            market_data: Current market data
        """
        from src.models import Order, OrderAction, OrderType
        
        if signal.recommendation == Recommendation.HOLD:
            return
        
        # Determine order action
        if signal.recommendation == Recommendation.BUY:
            action = OrderAction.BUY
            # Calculate quantity based on available cash and position limits
            # Simplified: use 10% of available cash
            cash = self._portfolio_manager.get_snapshot().cash_balance
            quantity = int((cash * Decimal("0.1")) / market_data.close)
            if quantity <= 0:
                return
        else:  # SELL
            action = OrderAction.SELL
            # Get current position
            position_opt = self._portfolio_manager.get_position(signal.symbol)
            if position_opt.is_none():
                return  # No position to sell
            position = position_opt.unwrap()
            quantity = position.quantity
        
        # Create and submit order
        order = Order(
            symbol=signal.symbol,
            quantity=quantity,
            action=action,
            order_type=OrderType.MARKET
        )
        
        order_result = self._trade_executor.submit_order(order)
        if order_result.is_err():
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "ERROR",
                "component": "CalgoSystem",
                "message": f"Order execution failed: {order_result.unwrap_err()}"
            })
            return
        
        confirmation = order_result.unwrap()
        
        # Log trade
        from src.models import TradeRecord
        trade_record = TradeRecord(
            timestamp=confirmation.timestamp,
            order_id=confirmation.order_id,
            symbol=confirmation.symbol,
            action=action,
            quantity=confirmation.quantity,
            execution_price=confirmation.execution_price
        )
        self._logger.log_trade(trade_record)
        
        # Update portfolio
        if action == OrderAction.BUY:
            self._portfolio_manager.add_position(
                symbol=confirmation.symbol,
                quantity=confirmation.quantity,
                entry_price=confirmation.execution_price
            )
        else:  # SELL
            self._portfolio_manager.close_position(
                symbol=confirmation.symbol,
                exit_price=confirmation.execution_price
            )
        
        # Log portfolio change
        self._logger.log_portfolio_change(self._portfolio_manager.get_snapshot())
    
    def _get_long_window(self) -> int:
        """Return long_window from the first enabled moving_average_crossover model, or 50."""
        if self._config_manager is None:
            return 50
        for model_config in self._config_manager.get_active_models():
            if model_config.enabled and model_config.model_type == "moving_average_crossover":
                return model_config.parameters.get("long_window", 50)
        return 50

    def _fetch_and_cache(self, symbol: str) -> Optional[CacheEntry]:
        """Fetch historical data for symbol, write to cache, and return a CacheEntry."""
        long_window = self._get_long_window()
        lookback_multiplier = 2
        start_date = datetime.today() - timedelta(days=long_window * lookback_multiplier)
        end_date = datetime.today()

        result = self._market_data_ingester.fetch_historical(symbol, start_date, end_date)
        if result.is_err():
            if self._logger:
                self._logger.log_error({
                    "timestamp": datetime.now().isoformat(),
                    "severity": "WARNING",
                    "component": "CalgoSystem",
                    "message": f"Failed to fetch historical data for {symbol}: {result.unwrap_err()}"
                })
            return None

        records = result.unwrap()
        self._cache_manager.write(symbol, records)
        return CacheEntry(symbol=symbol, fetched_at=datetime.now(), records=records)

    def _inject_price_history(self, symbol: str, records: List[PriceData]) -> None:
        """Inject closing prices from records into each MovingAverageCrossover model."""
        from src.trading_models import MovingAverageCrossover

        long_window = self._get_long_window()
        slice_records = records[-long_window:]

        if len(records) < long_window and self._logger:
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "WARNING",
                "component": "CalgoSystem",
                "message": (
                    f"Only {len(records)} records available for {symbol}; "
                    f"need {long_window} for full warm-up"
                )
            })

        closing_prices = [r.close for r in slice_records]

        if self._signal_generator is None:
            return
        for model in self._signal_generator._models.values():
            if isinstance(model, MovingAverageCrossover):
                model._price_history[symbol] = closing_prices

    def _seed_price_history(self, symbols: List[str]) -> None:
        """Pre-populate model price history from cache or network for each symbol."""
        for symbol in symbols:
            entry: Optional[CacheEntry] = None

            entry_result = self._cache_manager.read(symbol)
            if entry_result.is_ok():
                cached = entry_result.unwrap()
                if cached is None or self._cache_manager.is_stale(cached):
                    entry = self._fetch_and_cache(symbol)
                else:
                    entry = cached
            else:
                entry = self._fetch_and_cache(symbol)

            if entry is not None:
                self._inject_price_history(symbol, entry.records)

    def shutdown(self) -> Result[None, str]:
        """
        Gracefully shutdown the system.
        
        Transitions to SHUTDOWN state and cleans up resources.
        
        Returns:
            Result indicating success or error message
        """
        transition_result = self.transition_to(SystemState.SHUTDOWN)
        if transition_result.is_err():
            return Result.err(f"Failed to transition to SHUTDOWN: {transition_result.unwrap_err()}")
        
        if self._logger:
            self._logger.log_error({
                "timestamp": datetime.now().isoformat(),
                "severity": "INFO",
                "component": "CalgoSystem",
                "message": "System shutdown complete"
            })
        
        return Result.ok(None)
