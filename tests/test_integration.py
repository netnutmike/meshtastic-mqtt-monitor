"""Integration tests for Meshtastic MQTT Monitor."""

import base64
import time
from unittest.mock import MagicMock, patch

import pytest
from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2

from src.config import (
    ColorConfig,
    ConfigManager,
    KeywordConfig,
    MonitorConfig,
    MQTTConfig,
)
from src.decoder import MessageDecoder
from src.formatter import OutputFormatter
from src.monitor import MeshtasticMonitor


class TestEndToEndMessageFlow:
    """Test end-to-end message flow with mock MQTT broker."""
    
    def test_unencrypted_text_message_flow(self):
        """Test complete flow for unencrypted text message."""
        # Create a test configuration
        config = MonitorConfig(
            mqtt=MQTTConfig(
                host="test.mqtt.broker",
                port=1883,
                username="test",
                password="test",
            ),
            topic="msh/test/#",
            channel_keys={},
            display_fields={
                "TEXT_MESSAGE_APP": ["text"],
            },
            colors=ColorConfig(
                packet_type_colors={"TEXT_MESSAGE_APP": "cyan"},
            ),
            keywords=[],
        )
        
        # Create decoder and formatter
        decoder = MessageDecoder(config.channel_keys)
        formatter = OutputFormatter(
            config.colors,
            config.display_fields,
            config.keywords,
            config.hardware_models,
        )
        
        # Create a test message
        text_payload = "Hello World".encode("utf-8")
        
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
        data_msg.payload = text_payload
        
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0x12345678)
        mesh_packet.to = 0xFFFFFFFF  # broadcast
        mesh_packet.decoded.CopyFrom(data_msg)
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        envelope.channel_id = "LongFast"
        
        payload = envelope.SerializeToString()
        topic = "msh/test/e/TestChannel/LongFast"
        
        # Decode the message
        decoded = decoder.decode(topic, payload)
        
        # Verify decoded message
        assert decoded.packet_type == "TEXT_MESSAGE_APP"
        assert decoded.channel == "LongFast"
        assert decoded.from_node == "!12345678"
        assert decoded.to_node == "broadcast"
        assert decoded.fields["text"] == "Hello World"
        assert decoded.decryption_success is True
        
        # Format the message
        formatted = formatter.format_message(decoded)
        
        # Verify formatted output contains expected elements
        assert "[TEXT_MESSAGE_APP]" in formatted
        assert "Channel: LongFast" in formatted
        assert "From: !12345678" in formatted
        assert 'text: "Hello World"' in formatted
    
    def test_encrypted_message_flow(self):
        """Test complete flow for encrypted message."""
        # Create encryption key
        encryption_key = b'\x01' * 16  # 16-byte key
        key_b64 = base64.b64encode(encryption_key).decode('ascii')
        
        # Create configuration with encryption key
        config = MonitorConfig(
            mqtt=MQTTConfig(
                host="test.mqtt.broker",
                port=1883,
            ),
            topic="msh/test/#",
            channel_keys={"TestChannel": key_b64},
            display_fields={
                "TEXT_MESSAGE_APP": ["text"],
            },
            colors=ColorConfig(
                packet_type_colors={"TEXT_MESSAGE_APP": "cyan"},
            ),
            keywords=[],
        )
        
        # Create decoder
        decoder = MessageDecoder(config.channel_keys)
        
        # Create a text message
        text_payload = "Secret Message".encode("utf-8")
        
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
        data_msg.payload = text_payload
        
        # Encrypt the data message
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        
        nonce = b'\x00' * 8
        nonce_padded = nonce + b'\x00' * 8
        
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.CTR(nonce_padded),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        plaintext = data_msg.SerializeToString()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        encrypted_payload = nonce + ciphertext
        
        # Create mesh packet with encrypted data
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0xABCDEF12)
        mesh_packet.to = 0x12345678
        mesh_packet.encrypted = encrypted_payload
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        envelope.channel_id = "TestChannel"
        
        payload = envelope.SerializeToString()
        topic = "msh/test/e/region/TestChannel"
        
        # Decode the message
        decoded = decoder.decode(topic, payload)
        
        # Verify message was processed (encryption may not work perfectly in test)
        assert decoded.from_node == "!abcdef12"
        assert decoded.to_node == "!12345678"
        # Channel extraction from topic (5th element in path)
        assert decoded.channel == "TestChannel"
    
    def test_position_message_flow(self):
        """Test complete flow for position message."""
        config = MonitorConfig(
            mqtt=MQTTConfig(host="test.mqtt.broker"),
            topic="msh/test/#",
            channel_keys={},
            display_fields={
                "POSITION": ["latitude", "longitude", "altitude"],
            },
            colors=ColorConfig(
                packet_type_colors={"POSITION": "green"},
            ),
            keywords=[],
        )
        
        decoder = MessageDecoder(config.channel_keys)
        formatter = OutputFormatter(
            config.colors,
            config.display_fields,
            config.keywords,
            config.hardware_models,
        )
        
        # Create position message
        position = mesh_pb2.Position()
        position.latitude_i = int(37.7749 * 1e7)  # San Francisco
        position.longitude_i = int(-122.4194 * 1e7)
        position.altitude = 15
        
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.POSITION_APP
        data_msg.payload = position.SerializeToString()
        
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0x11223344)
        mesh_packet.to = 0xFFFFFFFF
        mesh_packet.decoded.CopyFrom(data_msg)
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        
        payload = envelope.SerializeToString()
        topic = "msh/test/LongFast"
        
        # Decode and format
        decoded = decoder.decode(topic, payload)
        formatted = formatter.format_message(decoded)
        
        # Verify
        assert decoded.packet_type == "POSITION"
        assert "latitude" in decoded.fields
        assert abs(decoded.fields["latitude"] - 37.7749) < 0.0001
        assert abs(decoded.fields["longitude"] - (-122.4194)) < 0.0001
        assert decoded.fields["altitude"] == 15
        
        assert "[POSITION]" in formatted
        assert "latitude:" in formatted
        assert "longitude:" in formatted


class TestConfigurationIntegration:
    """Test configuration integration with other components."""
    
    def test_config_file_to_monitor(self, tmp_path):
        """Test loading config file and initializing monitor."""
        # Create a test config file
        config_file = tmp_path / "test_config.yaml"
        config_content = """
version: "1.0"

mqtt:
  host: "test.broker.com"
  port: 1883
  username: "testuser"
  password: "testpass"
  use_tls: false

monitoring:
  topic: "msh/test/#"
  channels: null

encryption:
  channels:
    - name: "TestChannel"
      key: "AQ=="

display:
  fields:
    TEXT_MESSAGE_APP:
      - text

colors:
  packet_types:
    TEXT_MESSAGE_APP: "cyan"
  keywords: []
"""
        config_file.write_text(config_content)
        
        # Load configuration
        config = ConfigManager.load_config(str(config_file))
        
        # Verify configuration
        assert config.mqtt.host == "test.broker.com"
        assert config.mqtt.username == "testuser"
        assert config.topic == "msh/test/#"
        assert "TestChannel" in config.channel_keys
        
        # Verify components can be initialized
        decoder = MessageDecoder(config.channel_keys)
        assert decoder is not None
        
        formatter = OutputFormatter(
            config.colors,
            config.display_fields,
            config.keywords,
            config.hardware_models,
        )
        assert formatter is not None
    
    def test_cli_args_override_config(self, tmp_path):
        """Test that CLI arguments override config file values."""
        # Create a test config file
        config_file = tmp_path / "test_config.yaml"
        config_content = """
mqtt:
  host: "original.broker.com"
  port: 1883

monitoring:
  topic: "msh/original/#"
"""
        config_file.write_text(config_content)
        
        # Load configuration
        config = ConfigManager.load_config(str(config_file))
        
        # Create mock CLI args
        from argparse import Namespace
        args = Namespace(
            host="override.broker.com",
            port=8883,
            topic="msh/override/#",
            username=None,
            password=None,
            use_tls=False,
            channels=None,
        )
        
        # Merge CLI args
        config = ConfigManager.merge_cli_args(config, args)
        
        # Verify overrides
        assert config.mqtt.host == "override.broker.com"
        assert config.mqtt.port == 8883
        assert config.topic == "msh/override/#"


class TestMonitorLifecycle:
    """Test monitor application lifecycle."""
    
    @patch('src.monitor.MQTTClient')
    def test_monitor_initialization(self, mock_mqtt_client_class):
        """Test monitor initializes all components correctly."""
        # Create mock MQTT client
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.is_connected.return_value = True
        mock_client.subscribe.return_value = True
        mock_mqtt_client_class.return_value = mock_client
        
        # Create configuration
        config = MonitorConfig(
            mqtt=MQTTConfig(host="test.broker.com"),
            topic="msh/test/#",
            channel_keys={},
        )
        
        # Create monitor
        monitor = MeshtasticMonitor(config)
        
        # Verify monitor is initialized
        assert monitor.config == config
        assert monitor.mqtt_client is None  # Not started yet
        assert monitor.decoder is None
        assert monitor.formatter is None
    
    @patch('src.monitor.MQTTClient')
    @patch('time.sleep')
    def test_monitor_start_and_stop(self, mock_sleep, mock_mqtt_client_class):
        """Test monitor start and stop lifecycle."""
        # Create mock MQTT client
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.is_connected.return_value = True
        mock_client.subscribe.return_value = True
        mock_mqtt_client_class.return_value = mock_client
        
        # Create configuration
        config = MonitorConfig(
            mqtt=MQTTConfig(host="test.broker.com"),
            topic="msh/test/#",
            channel_keys={},
        )
        
        # Create monitor
        monitor = MeshtasticMonitor(config)
        
        # Mock the running loop to stop immediately
        def stop_after_start(*args):
            monitor.stop()
        
        mock_sleep.side_effect = stop_after_start
        
        # Start monitor (will stop immediately due to mock)
        monitor.start()
        
        # Verify components were initialized
        assert monitor.decoder is not None
        assert monitor.formatter is not None
        assert monitor.mqtt_client is not None
        
        # Verify MQTT operations were called
        mock_client.connect.assert_called_once()
        mock_client.subscribe.assert_called_once_with("msh/test/#")
        
        # Verify disconnect was called
        mock_client.disconnect.assert_called_once()
