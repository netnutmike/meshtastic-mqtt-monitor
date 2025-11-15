"""Main monitor application for Meshtastic MQTT Monitor."""

import logging
import signal
import sys
from typing import Optional

from src import __version__
from src.config import MonitorConfig
from src.decoder import MessageDecoder
from src.formatter import OutputFormatter
from src.mqtt_client import MQTTClient


logger = logging.getLogger(__name__)


class MeshtasticMonitor:
    """
    Main monitor application that coordinates all components.
    
    Manages MQTT client, message decoder, and output formatter to provide
    a complete monitoring solution for Meshtastic MQTT traffic.
    """
    
    def __init__(self, config: MonitorConfig):
        """
        Initialize Meshtastic monitor.
        
        Args:
            config: Complete monitor configuration
        """
        self.config = config
        self.mqtt_client: Optional[MQTTClient] = None
        self.decoder: Optional[MessageDecoder] = None
        self.formatter: Optional[OutputFormatter] = None
        self._running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self) -> None:
        """
        Start the monitor application.
        
        Initializes all components, connects to MQTT broker, subscribes to topics,
        and begins monitoring messages.
        """
        self._running = True
        
        # Display startup information
        self._display_startup_info()
        
        try:
            # Initialize decoder
            logger.info("Initializing message decoder...")
            self.decoder = MessageDecoder(self.config.channel_keys)
            
            # Initialize formatter
            logger.info("Initializing output formatter...")
            self.formatter = OutputFormatter(
                self.config.colors,
                self.config.display_fields,
                self.config.keywords,
                self.config.hardware_models,
            )
            
            # Initialize MQTT client
            logger.info("Initializing MQTT client...")
            self.mqtt_client = MQTTClient(
                self.config.mqtt,
                self._on_message_received,
            )
            
            # Connect to MQTT broker
            if not self.mqtt_client.connect():
                logger.error("Failed to connect to MQTT broker")
                sys.exit(1)
            
            # Wait for connection to establish
            import time
            max_wait = 10  # seconds
            waited = 0
            while not self.mqtt_client.is_connected() and waited < max_wait:
                time.sleep(0.5)
                waited += 0.5
            
            if not self.mqtt_client.is_connected():
                logger.error("Connection timeout - could not connect to MQTT broker")
                sys.exit(1)
            
            # Subscribe to configured topic
            logger.info(f"Subscribing to topic: {self.config.topic}")
            if not self.mqtt_client.subscribe(self.config.topic):
                logger.error(f"Failed to subscribe to topic: {self.config.topic}")
                sys.exit(1)
            
            print("\n" + "="*80)
            print("Monitor is running. Press Ctrl+C to stop.")
            print("="*80 + "\n")
            
            # Keep the main thread alive
            while self._running:
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in monitor application: {e}", exc_info=True)
            self.stop()
            sys.exit(1)
    
    def stop(self) -> None:
        """
        Stop the monitor application gracefully.
        
        Disconnects from MQTT broker and cleans up resources.
        """
        if not self._running:
            return
        
        self._running = False
        
        print("\n" + "="*80)
        print("Shutting down monitor...")
        print("="*80)
        
        # Disconnect MQTT client
        if self.mqtt_client:
            logger.info("Disconnecting from MQTT broker...")
            self.mqtt_client.disconnect()
        
        logger.info("Monitor stopped")
        print("Monitor stopped successfully.")
    
    def _on_message_received(self, topic: str, payload: bytes) -> None:
        """
        Callback for when a message is received from MQTT.
        
        Coordinates decoder and formatter to process and display the message.
        
        Args:
            topic: MQTT topic the message was received on
            payload: Raw message payload bytes
        """
        try:
            # Decode the message
            decoded_message = self.decoder.decode(topic, payload)
            
            # Apply filters if configured
            if self.config.filter_type:
                # Filter by packet type
                if decoded_message.packet_type != self.config.filter_type:
                    return  # Skip this message
            
            # Format the message
            formatted_output = self.formatter.format_message(decoded_message)
            
            # Apply text filter if configured
            if self.config.filter_text:
                # Case-insensitive search in the formatted output
                if self.config.filter_text.lower() not in formatted_output.lower():
                    return  # Skip this message
            
            # Display the formatted message
            print(formatted_output)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    def _display_startup_info(self) -> None:
        """Display startup information including version and configuration."""
        print("\n" + "="*80)
        print(f"Meshtastic MQTT Monitor v{__version__}")
        print("="*80)
        print(f"MQTT Broker: {self.config.mqtt.host}:{self.config.mqtt.port}")
        print(f"Username: {self.config.mqtt.username or '(none)'}")
        print(f"TLS/SSL: {'Enabled' if self.config.mqtt.use_tls else 'Disabled'}")
        print(f"Topic: {self.config.topic}")
        
        if self.config.channels:
            print(f"Channels: {', '.join(self.config.channels)}")
        else:
            print("Channels: All")
        
        if self.config.channel_keys:
            print(f"Encryption keys configured for: {', '.join(self.config.channel_keys.keys())}")
        else:
            print("Encryption keys: None configured")
        
        if self.config.keywords:
            print(f"Keyword highlights: {len(self.config.keywords)} configured")
        
        # Display active filters
        if self.config.filter_type:
            print(f"Filter: Only showing {self.config.filter_type} messages")
        if self.config.filter_text:
            print(f"Filter: Only showing messages containing '{self.config.filter_text}'")
        
        print("="*80 + "\n")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle shutdown signals (SIGINT, SIGTERM).
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
