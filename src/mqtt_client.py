"""MQTT client wrapper for Meshtastic MQTT Monitor."""

import logging
import ssl
import time
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from src.config import MQTTConfig


logger = logging.getLogger(__name__)


class MQTTClient:
    """
    MQTT client wrapper with connection management and reconnection logic.
    
    Handles connection to MQTT broker, topic subscription, and message callbacks
    with automatic reconnection using exponential backoff.
    """

    def __init__(
        self,
        config: MQTTConfig,
        on_message_callback: Callable[[str, bytes], None],
    ):
        """
        Initialize MQTT client.
        
        Args:
            config: MQTT connection configuration
            on_message_callback: Callback function for received messages.
                                 Signature: callback(topic: str, payload: bytes)
        """
        self.config = config
        self.on_message_callback = on_message_callback
        self._client: Optional[mqtt.Client] = None
        self._subscribed_topics: list[str] = []
        self._is_connected = False
        self._reconnect_delay = 1  # Initial reconnect delay in seconds
        self._max_reconnect_delay = 60  # Maximum reconnect delay
        self._should_reconnect = True
        
        # Create MQTT client instance
        self._client = mqtt.Client(client_id="", clean_session=True)
        
        # Set up callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        # Set up authentication if provided
        if self.config.username and self.config.password:
            self._client.username_pw_set(self.config.username, self.config.password)
        
        # Set up TLS if enabled
        if self.config.use_tls:
            self._setup_tls()

    def _setup_tls(self) -> None:
        """Configure TLS/SSL for secure MQTT connection."""
        tls_context = ssl.create_default_context()
        
        # Load custom CA certificate if provided
        if self.config.ca_cert:
            tls_context.load_verify_locations(cafile=self.config.ca_cert)
        
        self._client.tls_set_context(tls_context)
        logger.info("TLS/SSL enabled for MQTT connection")

    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection initiated successfully, False otherwise
        """
        try:
            logger.info(
                f"Connecting to MQTT broker at {self.config.host}:{self.config.port}"
            )
            self._client.connect(
                self.config.host,
                self.config.port,
                keepalive=60,
            )
            
            # Start network loop in background thread
            self._client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker and stop network loop."""
        self._should_reconnect = False
        self._is_connected = False
        
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("Disconnected from MQTT broker")

    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to MQTT topic.
        
        Supports MQTT wildcard patterns (+ for single level, # for multi-level).
        
        Args:
            topic: MQTT topic or topic pattern to subscribe to
            
        Returns:
            True if subscription initiated successfully, False otherwise
        """
        if not self._is_connected:
            logger.warning(f"Cannot subscribe to {topic}: not connected")
            return False
        
        try:
            result, mid = self._client.subscribe(topic, qos=0)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                self._subscribed_topics.append(topic)
                logger.info(f"Subscribed to topic: {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to {topic}: error code {result}")
                return False
                
        except Exception as e:
            logger.error(f"Exception while subscribing to {topic}: {e}")
            return False

    def is_connected(self) -> bool:
        """
        Check if client is connected to MQTT broker.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: any,
        flags: dict,
        rc: int,
    ) -> None:
        """
        Callback for when client connects to MQTT broker.
        
        Args:
            client: MQTT client instance
            userdata: User data (unused)
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            self._is_connected = True
            self._reconnect_delay = 1  # Reset reconnect delay on successful connection
            logger.info("Successfully connected to MQTT broker")
            
            # Resubscribe to topics after reconnection
            for topic in self._subscribed_topics:
                self._client.subscribe(topic, qos=0)
                logger.info(f"Resubscribed to topic: {topic}")
        else:
            self._is_connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"Connection failed: {error_msg}")
            
            # Don't retry on authentication failures
            if rc == 4 or rc == 5:
                self._should_reconnect = False
                logger.error("Authentication failed. Please check credentials.")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: any,
        rc: int,
    ) -> None:
        """
        Callback for when client disconnects from MQTT broker.
        
        Implements exponential backoff for reconnection attempts.
        
        Args:
            client: MQTT client instance
            userdata: User data (unused)
            rc: Disconnection result code
        """
        self._is_connected = False
        
        if rc != 0:
            logger.warning(f"Unexpected disconnection (code: {rc})")
            
            if self._should_reconnect:
                logger.info(
                    f"Attempting to reconnect in {self._reconnect_delay} seconds..."
                )
                time.sleep(self._reconnect_delay)
                
                # Exponential backoff: double the delay up to max
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay,
                )
                
                try:
                    self._client.reconnect()
                except Exception as e:
                    logger.error(f"Reconnection attempt failed: {e}")
        else:
            logger.info("Clean disconnection from MQTT broker")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """
        Callback for when a message is received.
        
        Args:
            client: MQTT client instance
            userdata: User data (unused)
            msg: Received MQTT message
        """
        try:
            # Call the user-provided callback with topic and payload
            self.on_message_callback(msg.topic, msg.payload)
        except Exception as e:
            logger.error(f"Error in message callback: {e}")
