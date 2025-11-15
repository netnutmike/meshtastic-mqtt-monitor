"""Unit tests for message decoder."""

import base64
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.decoder import DecodedMessage, MessageDecoder
from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2


@pytest.fixture
def channel_keys():
    """Create test channel keys."""
    return {
        "LongFast": base64.b64encode(b"0123456789abcdef").decode(),  # 16-byte key
        "Primary": base64.b64encode(b"fedcba9876543210").decode(),
    }


@pytest.fixture
def decoder(channel_keys):
    """Create MessageDecoder instance with test keys."""
    return MessageDecoder(channel_keys)


class TestMessageDecoderInitialization:
    """Test MessageDecoder initialization."""

    def test_decoder_initialization(self, channel_keys):
        """Test decoder initializes with channel keys."""
        decoder = MessageDecoder(channel_keys)
        
        assert len(decoder._decoded_keys) == 2
        assert "LongFast" in decoder._decoded_keys
        assert "Primary" in decoder._decoded_keys

    def test_decoder_with_invalid_key(self):
        """Test decoder handles invalid base64 keys gracefully."""
        invalid_keys = {
            "BadChannel": "not-valid-base64!!!",
        }
        
        decoder = MessageDecoder(invalid_keys)
        
        # Should not crash, but key won't be in decoded_keys
        assert "BadChannel" not in decoder._decoded_keys

    def test_decoder_with_empty_keys(self):
        """Test decoder with no keys."""
        decoder = MessageDecoder({})
        
        assert len(decoder._decoded_keys) == 0


class TestChannelExtraction:
    """Test channel extraction from MQTT topics."""

    def test_extract_channel_from_standard_topic(self, decoder):
        """Test extracting channel from standard MQTT topic."""
        topic = "msh/US/2/e/LongFast"
        channel = decoder._extract_channel_from_topic(topic)
        
        assert channel == "LongFast"

    def test_extract_channel_from_short_topic(self, decoder):
        """Test extracting channel from short topic."""
        topic = "msh/US"
        channel = decoder._extract_channel_from_topic(topic)
        
        assert channel == "unknown"

    def test_extract_channel_with_subtopics(self, decoder):
        """Test extracting channel with additional subtopics."""
        topic = "msh/US/2/e/Primary/extra/path"
        channel = decoder._extract_channel_from_topic(topic)
        
        assert channel == "Primary"


class TestPacketTypeIdentification:
    """Test packet type identification."""

    def test_identify_text_message(self, decoder):
        """Test identifying TEXT_MESSAGE_APP packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
        
        packet_type = decoder._identify_packet_type(data_msg)
        
        assert packet_type == "TEXT_MESSAGE_APP"

    def test_identify_position(self, decoder):
        """Test identifying POSITION packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.POSITION_APP
        
        packet_type = decoder._identify_packet_type(data_msg)
        
        assert packet_type == "POSITION"

    def test_identify_telemetry(self, decoder):
        """Test identifying TELEMETRY_APP packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TELEMETRY_APP
        
        packet_type = decoder._identify_packet_type(data_msg)
        
        assert packet_type == "TELEMETRY_APP"

    def test_identify_nodeinfo(self, decoder):
        """Test identifying NODEINFO_APP packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.NODEINFO_APP
        
        packet_type = decoder._identify_packet_type(data_msg)
        
        assert packet_type == "NODEINFO_APP"

    def test_identify_unknown_packet(self, decoder):
        """Test identifying unknown packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = 999  # Unknown portnum
        
        packet_type = decoder._identify_packet_type(data_msg)
        
        assert "UNKNOWN" in packet_type


class TestFieldExtraction:
    """Test field extraction for different packet types."""

    def test_extract_text_message_fields(self, decoder):
        """Test extracting text message fields."""
        payload = b"Hello, Meshtastic!"
        
        fields = decoder._extract_text_message_fields(payload)
        
        assert "text" in fields
        assert fields["text"] == "Hello, Meshtastic!"

    def test_extract_text_message_with_unicode(self, decoder):
        """Test extracting text message with unicode characters."""
        payload = "Hello 🌐 World".encode("utf-8")
        
        fields = decoder._extract_text_message_fields(payload)
        
        assert "text" in fields
        assert "🌐" in fields["text"]

    def test_extract_position_fields(self, decoder):
        """Test extracting position fields."""
        position = mesh_pb2.Position()
        position.latitude_i = 377490000  # 37.749 * 1e7
        position.longitude_i = -1224194000  # -122.4194 * 1e7
        position.altitude = 15
        position.time = 1700000000
        
        payload = position.SerializeToString()
        fields = decoder._extract_position_fields(payload)
        
        assert "latitude" in fields
        assert "longitude" in fields
        assert "altitude" in fields
        assert abs(fields["latitude"] - 37.749) < 0.001
        assert abs(fields["longitude"] - (-122.4194)) < 0.001
        assert fields["altitude"] == 15

    def test_extract_position_fields_zero_values(self, decoder):
        """Test extracting position with zero values (should be omitted)."""
        position = mesh_pb2.Position()
        position.latitude_i = 0
        position.longitude_i = 0
        
        payload = position.SerializeToString()
        fields = decoder._extract_position_fields(payload)
        
        # Zero values should not be included
        assert "latitude" not in fields
        assert "longitude" not in fields

    def test_extract_telemetry_device_metrics(self, decoder):
        """Test extracting telemetry device metrics."""
        telemetry = telemetry_pb2.Telemetry()
        telemetry.device_metrics.battery_level = 85
        telemetry.device_metrics.voltage = 4.2
        telemetry.device_metrics.channel_utilization = 15.5
        
        payload = telemetry.SerializeToString()
        fields = decoder._extract_telemetry_fields(payload)
        
        assert "battery_level" in fields
        assert fields["battery_level"] == 85
        assert "voltage" in fields
        assert abs(fields["voltage"] - 4.2) < 0.01

    def test_extract_telemetry_environment_metrics(self, decoder):
        """Test extracting telemetry environment metrics."""
        telemetry = telemetry_pb2.Telemetry()
        telemetry.environment_metrics.temperature = 25.5
        telemetry.environment_metrics.relative_humidity = 60.0
        telemetry.environment_metrics.barometric_pressure = 1013.25
        
        payload = telemetry.SerializeToString()
        fields = decoder._extract_telemetry_fields(payload)
        
        assert "temperature" in fields
        assert abs(fields["temperature"] - 25.5) < 0.01
        assert "humidity" in fields
        assert "pressure" in fields

    def test_extract_nodeinfo_fields(self, decoder):
        """Test extracting node info fields."""
        user = mesh_pb2.User()
        user.id = "!a1b2c3d4"
        user.long_name = "Test Node"
        user.short_name = "TST"
        user.hw_model = 1
        
        payload = user.SerializeToString()
        fields = decoder._extract_nodeinfo_fields(payload)
        
        assert "node_id" in fields
        assert fields["node_id"] == "!a1b2c3d4"
        assert "long_name" in fields
        assert fields["long_name"] == "Test Node"
        assert "short_name" in fields
        assert fields["short_name"] == "TST"


class TestNodeIdFormatting:
    """Test node ID formatting."""

    def test_format_regular_node_id(self, decoder):
        """Test formatting regular node ID."""
        node_id = 0xa1b2c3d4
        formatted = decoder._format_node_id(node_id)
        
        assert formatted == "!a1b2c3d4"

    def test_format_broadcast_node_id(self, decoder):
        """Test formatting broadcast node ID."""
        node_id = 0
        formatted = decoder._format_node_id(node_id)
        
        assert formatted == "broadcast"

    def test_format_small_node_id(self, decoder):
        """Test formatting small node ID with leading zeros."""
        node_id = 0x123
        formatted = decoder._format_node_id(node_id)
        
        assert formatted == "!00000123"


class TestMessageDecoding:
    """Test complete message decoding."""

    def test_decode_text_message(self, decoder):
        """Test decoding a complete text message."""
        # Create a Data message
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
        data_msg.payload = b"Test message"
        
        # Create MeshPacket with decoded data
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0xa1b2c3d4)
        mesh_packet.to = 0xe5f6a7b8
        mesh_packet.decoded.CopyFrom(data_msg)
        
        # Create ServiceEnvelope
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        
        # Decode
        topic = "msh/US/2/e/LongFast"
        result = decoder.decode(topic, envelope.SerializeToString())
        
        assert isinstance(result, DecodedMessage)
        assert result.packet_type == "TEXT_MESSAGE_APP"
        assert result.channel == "LongFast"
        assert result.from_node == "!a1b2c3d4"
        assert result.to_node == "!e5f6a7b8"
        assert "text" in result.fields
        assert result.fields["text"] == "Test message"
        assert result.decryption_success is True

    def test_decode_position_message(self, decoder):
        """Test decoding a position message."""
        # Create position
        position = mesh_pb2.Position()
        position.latitude_i = 377490000
        position.longitude_i = -1224194000
        position.altitude = 100
        
        # Create Data message
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.POSITION_APP
        data_msg.payload = position.SerializeToString()
        
        # Create MeshPacket with decoded data
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0x12345678)
        mesh_packet.to = 0
        mesh_packet.decoded.CopyFrom(data_msg)
        
        # Create ServiceEnvelope
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        
        # Decode
        topic = "msh/US/2/e/Primary"
        result = decoder.decode(topic, envelope.SerializeToString())
        
        assert result.packet_type == "POSITION"
        assert result.channel == "Primary"
        assert result.from_node == "!12345678"
        assert result.to_node == "broadcast"
        assert "latitude" in result.fields
        assert "longitude" in result.fields
        assert "altitude" in result.fields

    def test_decode_invalid_message(self, decoder):
        """Test decoding invalid message data."""
        # Send garbage data
        result = decoder.decode("msh/US/2/e/Test", b"invalid protobuf data")
        
        assert result.packet_type == "DECODE_ERROR"
        assert result.error is not None
        assert result.decryption_success is False

    def test_decode_message_without_channel_key(self):
        """Test decoding message for channel without encryption key."""
        decoder = MessageDecoder({})  # No keys
        
        # Create a simple message
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
        data_msg.payload = b"Unencrypted"
        
        # Create MeshPacket with decoded data
        mesh_packet = mesh_pb2.MeshPacket()
        setattr(mesh_packet, 'from', 0x11111111)
        mesh_packet.to = 0x22222222
        mesh_packet.decoded.CopyFrom(data_msg)
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        
        result = decoder.decode("msh/US/2/e/Public", envelope.SerializeToString())
        
        assert result.packet_type == "TEXT_MESSAGE_APP"
        assert result.channel == "Public"


class TestDecryption:
    """Test message decryption functionality."""

    def test_decrypt_with_valid_key(self, decoder):
        """Test decryption with valid key."""
        # Note: This is a simplified test. Real Meshtastic encryption is more complex.
        # We're testing that the method handles the decryption attempt gracefully.
        
        encrypted_data = b"\x00\x01\x02\x03\x04\x05\x06\x07" + b"encrypted_payload"
        
        # Attempt decryption (may return None if format doesn't match)
        result = decoder._decrypt_payload(encrypted_data, "LongFast")
        
        # Should not crash, result may be None or decrypted data
        assert result is None or isinstance(result, bytes)

    def test_decrypt_without_key(self, decoder):
        """Test decryption attempt without key."""
        encrypted_data = b"some_encrypted_data"
        
        result = decoder._decrypt_payload(encrypted_data, "UnknownChannel")
        
        assert result is None

    def test_decrypt_with_short_data(self, decoder):
        """Test decryption with data too short for nonce."""
        encrypted_data = b"short"
        
        result = decoder._decrypt_payload(encrypted_data, "LongFast")
        
        assert result is None


class TestExtractFieldsGeneric:
    """Test generic field extraction."""

    def test_extract_fields_unknown_type(self, decoder):
        """Test extracting fields from unknown packet type."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = 999
        data_msg.payload = b"unknown payload"
        
        fields = decoder._extract_fields(data_msg, "UNKNOWN_999")
        
        assert "payload_size" in fields
        assert fields["payload_size"] == len(b"unknown payload")

    def test_extract_fields_with_exception(self, decoder):
        """Test field extraction handles exceptions gracefully."""
        data_msg = mesh_pb2.Data()
        data_msg.portnum = portnums_pb2.PortNum.POSITION_APP
        data_msg.payload = b"invalid position data"
        
        # Should not crash
        fields = decoder._extract_fields(data_msg, "POSITION")
        
        # May have parse_error or be empty
        assert isinstance(fields, dict)
