#!/usr/bin/env python3
"""CLI entry point for Meshtastic MQTT Monitor."""

import logging
import sys

from src import __version__
from src.config import ConfigManager
from src.monitor import MeshtasticMonitor


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Reduce noise from paho-mqtt library
    logging.getLogger('paho').setLevel(logging.WARNING)


def main() -> None:
    """Main entry point for the application."""
    # Create argument parser
    parser = ConfigManager.create_argument_parser()
    
    # Add verbose flag for logging
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging',
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration from file
        logger.info(f"Loading configuration from {args.config}")
        config = ConfigManager.load_config(args.config)
        
        # Merge CLI arguments
        logger.info("Merging command-line arguments")
        config = ConfigManager.merge_cli_args(config, args)
        
        # Validate configuration
        logger.info("Validating configuration")
        ConfigManager.validate_config(config)
        
        # Create and start monitor
        logger.info("Starting Meshtastic MQTT Monitor")
        monitor = MeshtasticMonitor(config)
        monitor.start()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
