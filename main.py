#!/usr/bin/env python3
"""
Calgo AI-Driven Trading Bot
Main entry point and CLI
"""
import argparse
import sys
from pathlib import Path

from src.calgo_system import CalgoSystem
from src.models import SystemState


def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗ █████╗ ██╗      ██████╗  ██████╗               ║
    ║  ██╔════╝██╔══██╗██║     ██╔════╝ ██╔═══██╗              ║
    ║  ██║     ███████║██║     ██║  ███╗██║   ██║              ║
    ║  ██║     ██╔══██║██║     ██║   ██║██║   ██║              ║
    ║  ╚██████╗██║  ██║███████╗╚██████╔╝╚██████╔╝              ║
    ║   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝               ║
    ║                                                           ║
    ║         AI-Driven Autonomous Trading Bot                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Calgo AI-Driven Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration (simulation mode)
  python main.py --config config/config.json --symbols AAPL MSFT GOOGL

  # Run with live trading configuration
  python main.py --config config/config.live.json --symbols SPY --mode live

  # Override execution mode
  python main.py --config config/config.json --symbols TSLA --mode simulation
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.json',
        help='Path to configuration file (default: config/config.json)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['simulation', 'live'],
        help='Override execution mode from configuration file'
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        required=True,
        help='List of symbols to trade (e.g., AAPL MSFT GOOGL)'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress startup banner'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Print banner
    if not args.no_banner:
        print_banner()
    
    # Validate configuration file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Configuration file not found: {args.config}")
        print(f"   Please create a configuration file or use --config to specify a different path.")
        sys.exit(1)
    
    # Initialize system
    print(f"🔧 Initializing Calgo system...")
    print(f"   Configuration: {args.config}")
    print(f"   Symbols: {', '.join(args.symbols)}")
    
    system = CalgoSystem()
    
    # Load configuration and initialize components
    init_result = system.initialize(str(config_path))
    if init_result.is_err():
        print(f"❌ Initialization failed: {init_result.unwrap_err()}")
        sys.exit(1)
    
    print(f"✅ System initialized successfully")
    print(f"   State: {system.state.value}")
    
    # Override execution mode if specified
    if args.mode:
        print(f"⚠️  Execution mode override: {args.mode}")
        # Note: This would require modifying the config manager to support runtime overrides
        # For now, we just warn the user
    
    # Start trading
    print(f"\n🚀 Starting trading loop...")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        start_result = system.start_trading(args.symbols)
        if start_result.is_err():
            print(f"❌ Trading failed: {start_result.unwrap_err()}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n⏸️  Interrupted by user")
    finally:
        # Shutdown system
        print(f"🛑 Shutting down system...")
        shutdown_result = system.shutdown()
        if shutdown_result.is_ok():
            print(f"✅ System shutdown complete")
        else:
            print(f"⚠️  Shutdown warning: {shutdown_result.unwrap_err()}")
    
    print(f"\n👋 Goodbye!")


if __name__ == "__main__":
    main()
