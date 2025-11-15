"""Unit tests for MQTT client wrapper."""

import time
from unittest.mock import MagicMock, Mock, call, patch

import paho.mqtt.client as mqtt
import pytest

from src.config import MQTTConfig
from src.mqtt_client import MQTTClient


@pytest.fixture
def mqtt_config():
    """Create a basic MQTT configuration for testing."""
    return MQTTConfig(
        host="test.mqtt.broker",
        port=1883,
        username="testuser",
        password="testpass",
        use_tls=False,
        ca_cert=None,
    )


@pytest.fixture
def mqtt_config_tls():
    """Create an MQTT configuration with TLS enabled."""
    return MQTTConfig(
        host="test.mqtt.broker",
        port=8883,
        username="testuser",
        password="testpass",
        use_tls=True,
        ca_cert="/path/to/ca.crt",
    )


@pytest.fixture
def message_callback():
    """Create a mock message callback."""
    return Mock()


class TestMQTTClientInitialization:
    """Test MQTT client initialization."""

    @patch("src.mqtt_client.mqtt.Client")
    def test_client_initialization(self, mock_client_class, mqtt_config, message_callback):
        """Test that client is initialized with correct parameters."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        
        # Verify client was created
        mock_client_class.assert_called_once_with(client_id="", clean_session=True)
        
        # Verify callbacks were set
        assert client._client.on_connect is not None
        assert client._client.on_disconnect is not None
        assert client._client.on_message is not None
        
        # Verify authentication was set
        mock_client.username_pw_set.assert_called_once_with("testuser", "testpass")

    @patch("src.mqtt_client.mqtt.Client")
    def test_client_initialization_without_auth(self, mock_client_class, message_callback):
        """Test client initialization without authentication."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        config = MQTTConfig(host="test.broker", port=1883, username=None, password=None)
        client = MQTTClient(config, message_callback)
        
        # Verify authentication was not set
        mock_client.username_pw_set.assert_not_called()

    @patch("src.mqtt_client.ssl.create_default_context")
    @patch("src.mqtt_client.mqtt.Client")
    def test_client_initialization_with_tls(
        self, mock_client_class, mock_ssl_context, mqtt_config_tls, message_callback
    ):
        """Test client initialization with TLS enabled."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        
        client = MQTTClient(mqtt_config_tls, message_callback)
        
        # Verify TLS was configured
        mock_ssl_context.assert_called_once()
        mock_context.load_verify_locations.assert_called_once_with(
            cafile="/path/to/ca.crt"
        )
        mock_client.tls_set_context.assert_called_once_with(mock_context)


class TestMQTTClientConnection:
    """Test MQTT client connection handling."""

    @patch("src.mqtt_client.mqtt.Client")
    def test_connect_success(self, mock_client_class, mqtt_config, message_callback):
        """Test successful connection to MQTT broker."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        result = client.connect()
        
        # Verify connection was attempted
        assert result is True
        mock_client.connect.assert_called_once_with(
            "test.mqtt.broker", 1883, keepalive=60
        )
        mock_client.loop_start.assert_called_once()

    @patch("src.mqtt_client.mqtt.Client")
    def test_connect_failure(self, mock_client_class, mqtt_config, message_callback):
        """Test connection failure handling."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        result = client.connect()
        
        # Verify connection failure was handled
        assert result is False

    @patch("src.mqtt_client.mqtt.Client")
    def test_disconnect(self, mock_client_class, mqtt_config, message_callback):
        """Test disconnection from MQTT broker."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        client.disconnect()
        
        # Verify disconnection
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
        assert client._is_connected is False
        assert client._should_reconnect is False

    @patch("src.mqtt_client.mqtt.Client")
    def test_is_connected(self, mock_client_class, mqtt_config, message_callback):
        """Test connection status check."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        
        # Initially not connected
        assert client.is_connected() is False
        
        # Simulate connection
        client._is_connected = True
        assert client.is_connected() is True


class TestMQTTClientSubscription:
    """Test MQTT client topic subscription."""

    @patch("src.mqtt_client.mqtt.Client")
    def test_subscribe_success(self, mock_client_class, mqtt_config, message_callback):
        """Test successful topic subscription."""
        mock_client = MagicMock()
        mock_client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 1)
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        
        result = client.subscribe("test/topic/#")
        
        # Verify subscription
        assert result is True
        mock_client.subscribe.assert_called_once_with("test/topic/#", qos=0)
        assert "test/topic/#" in client._subscribed_topics

    @patch("src.mqtt_client.mqtt.Client")
    def test_subscribe_not_connected(self, mock_client_class, mqtt_config, message_callback):
        """Test subscription attempt when not connected."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = False
        
        result = client.subscribe("test/topic")
        
        # Verify subscription was not attempted
        assert result is False
        mock_client.subscribe.assert_not_called()

    @patch("src.mqtt_client.mqtt.Client")
    def test_subscribe_failure(self, mock_client_class, mqtt_config, message_callback):
        """Test subscription failure handling."""
        mock_client = MagicMock()
        mock_client.subscribe.return_value = (mqtt.MQTT_ERR_NO_CONN, 1)
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        
        result = client.subscribe("test/topic")
        
        # Verify subscription failure was handled
        assert result is False


class TestMQTTClientCallbacks:
    """Test MQTT client callback handling."""

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_connect_success(self, mock_client_class, mqtt_config, message_callback):
        """Test successful connection callback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._subscribed_topics = ["test/topic"]
        
        # Simulate successful connection
        client._on_connect(mock_client, None, {}, 0)
        
        # Verify connection state
        assert client._is_connected is True
        assert client._reconnect_delay == 1
        
        # Verify resubscription
        mock_client.subscribe.assert_called_once_with("test/topic", qos=0)

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_connect_auth_failure(self, mock_client_class, mqtt_config, message_callback):
        """Test connection callback with authentication failure."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        
        # Simulate authentication failure (rc=4)
        client._on_connect(mock_client, None, {}, 4)
        
        # Verify connection state
        assert client._is_connected is False
        assert client._should_reconnect is False

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_disconnect_unexpected(self, mock_client_class, mqtt_config, message_callback):
        """Test unexpected disconnection callback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        client._reconnect_delay = 1
        
        # Simulate unexpected disconnection
        with patch("time.sleep"):
            client._on_disconnect(mock_client, None, 1)
        
        # Verify disconnection state
        assert client._is_connected is False
        
        # Verify reconnection was attempted
        mock_client.reconnect.assert_called_once()

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_disconnect_clean(self, mock_client_class, mqtt_config, message_callback):
        """Test clean disconnection callback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        
        # Simulate clean disconnection
        client._on_disconnect(mock_client, None, 0)
        
        # Verify disconnection state
        assert client._is_connected is False
        
        # Verify no reconnection attempt
        mock_client.reconnect.assert_not_called()

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_message(self, mock_client_class, mqtt_config, message_callback):
        """Test message received callback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        
        # Create mock MQTT message
        mock_msg = MagicMock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b"test payload"
        
        # Simulate message received
        client._on_message(mock_client, None, mock_msg)
        
        # Verify callback was invoked
        message_callback.assert_called_once_with("test/topic", b"test payload")

    @patch("src.mqtt_client.mqtt.Client")
    def test_on_message_callback_exception(
        self, mock_client_class, mqtt_config, message_callback
    ):
        """Test message callback exception handling."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Make callback raise exception
        message_callback.side_effect = Exception("Callback error")
        
        client = MQTTClient(mqtt_config, message_callback)
        
        # Create mock MQTT message
        mock_msg = MagicMock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b"test payload"
        
        # Simulate message received - should not raise exception
        client._on_message(mock_client, None, mock_msg)


class TestMQTTClientReconnection:
    """Test MQTT client reconnection logic."""

    @patch("src.mqtt_client.mqtt.Client")
    @patch("time.sleep")
    def test_exponential_backoff(
        self, mock_sleep, mock_client_class, mqtt_config, message_callback
    ):
        """Test exponential backoff for reconnection."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        
        # Simulate multiple disconnections
        initial_delay = client._reconnect_delay
        
        # First disconnection
        client._on_disconnect(mock_client, None, 1)
        assert client._reconnect_delay == initial_delay * 2
        
        # Second disconnection
        client._on_disconnect(mock_client, None, 1)
        assert client._reconnect_delay == initial_delay * 4
        
        # Third disconnection
        client._on_disconnect(mock_client, None, 1)
        assert client._reconnect_delay == initial_delay * 8

    @patch("src.mqtt_client.mqtt.Client")
    @patch("time.sleep")
    def test_max_reconnect_delay(
        self, mock_sleep, mock_client_class, mqtt_config, message_callback
    ):
        """Test that reconnect delay doesn't exceed maximum."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._is_connected = True
        client._reconnect_delay = 32  # Start near max
        
        # Simulate disconnection
        client._on_disconnect(mock_client, None, 1)
        
        # Verify delay doesn't exceed max
        assert client._reconnect_delay <= client._max_reconnect_delay

    @patch("src.mqtt_client.mqtt.Client")
    def test_reconnect_on_successful_connection(
        self, mock_client_class, mqtt_config, message_callback
    ):
        """Test that reconnect delay resets on successful connection."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = MQTTClient(mqtt_config, message_callback)
        client._reconnect_delay = 16  # Set to high value
        
        # Simulate successful connection
        client._on_connect(mock_client, None, {}, 0)
        
        # Verify delay was reset
        assert client._reconnect_delay == 1
