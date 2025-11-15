"""Message decoder for Meshtastic MQTT Monitor."""

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2


logger = logging.getLogger(__name__)


@dataclass
class DecodedMessage:
    """Represents a decoded Meshtastic message."""

    packet_type: str
    channel: str
    from_node: str
    to_node: str
    timestamp: datetime
    fields: Dict[str, Any] = field(default_factory=dict)
    raw_data: bytes = b""
    decryption_success: bool = True
    error: Optional[str] = None


class MessageDecoder:
    """
    Decodes and decrypts Meshtastic protobuf messages.
    
    Handles ServiceEnvelope messages from MQTT, decrypts payloads using
    channel-specific keys, and extracts fields based on packet type.
    """

    def __init__(self, channel_keys: Dict[str, str]):
        """
        Initialize message decoder.
        
        Args:
            channel_keys: Dictionary mapping channel names to base64-encoded encryption keys
        """
        self.channel_keys = channel_keys
        self._decoded_keys: Dict[str, bytes] = {}
        
        # Decode and cache encryption keys
        for channel_name, key_b64 in channel_keys.items():
            try:
                decoded_key = base64.b64decode(key_b64)
                self._decoded_keys[channel_name] = decoded_key
                logger.debug(f"Loaded encryption key for channel: {channel_name}")
            except Exception as e:
                logger.warning(f"Invalid base64 key for channel {channel_name}: {e}")

    def decode(self, mqtt_topic: str, payload: bytes) -> DecodedMessage:
        """
        Decode a Meshtastic MQTT message.
        
        Args:
            mqtt_topic: MQTT topic the message was received on
            payload: Raw message payload bytes
            
        Returns:
            DecodedMessage object with decoded information
        """
        try:
            # Check if this is a status message (plain text on /stat/ topic)
            if "/stat/" in mqtt_topic:
                try:
                    status_text = payload.decode('utf-8', errors='ignore')
                    logger.debug(f"Status message on topic {mqtt_topic}: {status_text}")
                    return DecodedMessage(
                        packet_type="STATUS",
                        channel=self._extract_channel_from_topic(mqtt_topic),
                        from_node=mqtt_topic.split("/")[-1] if "/" in mqtt_topic else "unknown",
                        to_node="broadcast",
                        timestamp=datetime.now(),
                        fields={"status": status_text},
                        raw_data=payload,
                        decryption_success=True,
                    )
                except:
                    pass  # If decode fails, continue to protobuf parsing
            
            # Check if payload is JSON (some MQTT messages are JSON, not protobuf)
            if payload.startswith(b'{') or payload.startswith(b'['):
                try:
                    json_data = json.loads(payload.decode('utf-8'))
                    logger.debug(f"Parsing JSON message on topic {mqtt_topic}")
                    
                    # Extract common fields from JSON
                    raw_type = json_data.get('type', 'UNKNOWN')
                    
                    # Normalize JSON message types to standard packet types
                    type_mapping = {
                        'sendtext': 'TEXT_MESSAGE_APP',
                        'text': 'TEXT_MESSAGE_APP',
                        'position': 'POSITION',
                        'nodeinfo': 'NODEINFO_APP',
                        'telemetry': 'TELEMETRY_APP',
                    }
                    packet_type = type_mapping.get(raw_type.lower(), raw_type)
                    
                    from_node = json_data.get('from', 'unknown')
                    to_node = json_data.get('to', 'unknown')
                    
                    # Convert from_node to hex format if it's a number
                    if isinstance(from_node, int):
                        from_node = f"!{from_node:08x}"
                    if isinstance(to_node, int):
                        to_node = f"!{to_node:08x}"
                    
                    # Extract payload fields
                    fields = {}
                    if 'payload' in json_data:
                        payload_data = json_data['payload']
                        if isinstance(payload_data, dict):
                            fields = payload_data
                        else:
                            fields = {'payload': payload_data}
                    
                    # Add other top-level fields
                    for key in ['channel', 'id', 'sender', 'timestamp']:
                        if key in json_data and key not in fields:
                            fields[key] = json_data[key]
                    
                    return DecodedMessage(
                        packet_type=packet_type,
                        channel=self._extract_channel_from_topic(mqtt_topic),
                        from_node=from_node,
                        to_node=to_node,
                        timestamp=datetime.now(),
                        fields=fields,
                        raw_data=payload,
                        decryption_success=True,
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON message: {e}")
                    return DecodedMessage(
                        packet_type="JSON_ERROR",
                        channel=self._extract_channel_from_topic(mqtt_topic),
                        from_node="unknown",
                        to_node="unknown",
                        timestamp=datetime.now(),
                        fields={"error": f"Invalid JSON: {e}"},
                        raw_data=payload,
                        decryption_success=False,
                    )
            
            # Try to parse as ServiceEnvelope first
            envelope = mqtt_pb2.ServiceEnvelope()
            mesh_packet = None
            
            try:
                bytes_parsed = envelope.ParseFromString(payload)
                logger.debug(f"Successfully parsed {bytes_parsed} bytes as ServiceEnvelope")
                # Check if envelope has a packet
                if envelope.HasField("packet"):
                    mesh_packet = envelope.packet
                else:
                    logger.debug("ServiceEnvelope has no packet field, trying direct MeshPacket parse")
            except Exception as parse_error:
                logger.debug(f"Failed to parse as ServiceEnvelope: {parse_error}, trying direct MeshPacket")
            
            # If ServiceEnvelope didn't work, try parsing directly as MeshPacket
            if mesh_packet is None:
                try:
                    mesh_packet = mesh_pb2.MeshPacket()
                    mesh_packet.ParseFromString(payload)
                    logger.debug("Successfully parsed as direct MeshPacket")
                except Exception as packet_error:
                    logger.error(f"Failed to parse as both ServiceEnvelope and MeshPacket")
                    logger.error(f"Topic: {mqtt_topic}")
                    logger.error(f"Payload length: {len(payload)} bytes")
                    logger.error(f"Payload (first 100 bytes hex): {payload[:min(100, len(payload))].hex()}")
                    raise ValueError(f"Could not parse message as ServiceEnvelope or MeshPacket: {packet_error}")
            
            # Extract channel from topic (e.g., "msh/US/2/e/LongFast" -> "LongFast")
            channel = self._extract_channel_from_topic(mqtt_topic)
            
            # Determine if we need to decrypt
            data_msg = None
            decryption_success = True
            
            if mesh_packet.HasField("decoded"):
                # Already decoded (unencrypted)
                data_msg = mesh_packet.decoded
            elif len(mesh_packet.encrypted) > 0:
                # Encrypted - attempt to decrypt
                if channel in self._decoded_keys:
                    try:
                        decrypted_bytes = self._decrypt_payload(mesh_packet.encrypted, channel)
                        if decrypted_bytes:
                            data_msg = mesh_pb2.Data()
                            data_msg.ParseFromString(decrypted_bytes)
                        else:
                            decryption_success = False
                    except Exception as e:
                        logger.debug(f"Decryption failed for channel {channel}: {e}")
                        decryption_success = False
                else:
                    decryption_success = False
            
            # If we couldn't get data_msg, return error
            if data_msg is None:
                return DecodedMessage(
                    packet_type="ENCRYPTED" if not decryption_success else "UNKNOWN",
                    channel=channel,
                    from_node=self._format_node_id(getattr(mesh_packet, 'from')),
                    to_node=self._format_node_id(mesh_packet.to),
                    timestamp=datetime.now(),
                    fields={"status": "Unable to decrypt or decode"},
                    raw_data=payload,
                    decryption_success=False,
                )
            
            # Identify packet type
            packet_type = self._identify_packet_type(data_msg)
            
            # Extract fields based on packet type
            fields = self._extract_fields(data_msg, packet_type)
            
            # Don't add channel to fields since it's already shown in basic info
            # This avoids duplication in the output
            
            # Build DecodedMessage
            return DecodedMessage(
                packet_type=packet_type,
                channel=channel,
                from_node=self._format_node_id(getattr(mesh_packet, 'from')),
                to_node=self._format_node_id(mesh_packet.to),
                timestamp=datetime.now(),
                fields=fields,
                raw_data=payload,
                decryption_success=decryption_success,
            )
            
        except ValueError as e:
            # Specific parsing error with more context
            logger.warning(f"Message parsing error: {e}")
            return DecodedMessage(
                packet_type="DECODE_ERROR",
                channel=self._extract_channel_from_topic(mqtt_topic),
                from_node="unknown",
                to_node="unknown",
                timestamp=datetime.now(),
                fields={"error": str(e)},
                raw_data=payload,
                decryption_success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error decoding message: {e}", exc_info=True)
            return DecodedMessage(
                packet_type="DECODE_ERROR",
                channel=self._extract_channel_from_topic(mqtt_topic),
                from_node="unknown",
                to_node="unknown",
                timestamp=datetime.now(),
                fields={"error": f"Unexpected error: {str(e)}"},
                raw_data=payload,
                decryption_success=False,
                error=str(e),
            )

    def _decrypt_payload(self, encrypted_data: bytes, channel: str) -> Optional[bytes]:
        """
        Decrypt message payload using channel-specific key.
        
        Uses AES-128-CTR cipher with nonce from packet header.
        
        Args:
            encrypted_data: Encrypted payload bytes
            channel: Channel name to get decryption key
            
        Returns:
            Decrypted payload bytes, or None if decryption fails
        """
        if channel not in self._decoded_keys:
            logger.debug(f"No decryption key available for channel: {channel}")
            return None
        
        key = self._decoded_keys[channel]
        
        try:
            # Meshtastic uses AES-128-CTR
            # The nonce is derived from packet ID and other metadata
            # For simplicity, we'll try to decrypt assuming standard format
            
            # Extract nonce (first 16 bytes) and ciphertext
            if len(encrypted_data) < 16:
                return None
            
            nonce = encrypted_data[:8]
            # Pad nonce to 16 bytes for CTR mode
            nonce_padded = nonce + b'\x00' * 8
            
            ciphertext = encrypted_data[8:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CTR(nonce_padded),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            logger.debug(f"Decryption error: {e}")
            return None

    def _extract_channel_from_topic(self, topic: str) -> str:
        """
        Extract channel name from MQTT topic.
        
        Args:
            topic: MQTT topic string (e.g., "msh/US/2/e/LongFast")
            
        Returns:
            Channel name, or "unknown" if not found
        """
        parts = topic.split("/")
        if len(parts) >= 5:
            return parts[4]
        return "unknown"

    def _identify_packet_type(self, data_msg: mesh_pb2.Data) -> str:
        """
        Identify packet type from portnum field.
        
        Args:
            data_msg: Decoded Data protobuf message
            
        Returns:
            String representation of packet type
        """
        portnum = data_msg.portnum
        
        # Map portnum to human-readable names
        portnum_names = {
            portnums_pb2.PortNum.UNKNOWN_APP: "UNKNOWN",
            portnums_pb2.PortNum.TEXT_MESSAGE_APP: "TEXT_MESSAGE_APP",
            portnums_pb2.PortNum.REMOTE_HARDWARE_APP: "REMOTE_HARDWARE_APP",
            portnums_pb2.PortNum.POSITION_APP: "POSITION",
            portnums_pb2.PortNum.NODEINFO_APP: "NODEINFO_APP",
            portnums_pb2.PortNum.ROUTING_APP: "ROUTING_APP",
            portnums_pb2.PortNum.ADMIN_APP: "ADMIN_APP",
            portnums_pb2.PortNum.TEXT_MESSAGE_COMPRESSED_APP: "TEXT_MESSAGE_COMPRESSED",
            portnums_pb2.PortNum.WAYPOINT_APP: "WAYPOINT_APP",
            portnums_pb2.PortNum.AUDIO_APP: "AUDIO_APP",
            portnums_pb2.PortNum.DETECTION_SENSOR_APP: "DETECTION_SENSOR_APP",
            portnums_pb2.PortNum.REPLY_APP: "REPLY_APP",
            portnums_pb2.PortNum.IP_TUNNEL_APP: "IP_TUNNEL_APP",
            portnums_pb2.PortNum.PAXCOUNTER_APP: "PAXCOUNTER_APP",
            portnums_pb2.PortNum.SERIAL_APP: "SERIAL_APP",
            portnums_pb2.PortNum.STORE_FORWARD_APP: "STORE_FORWARD_APP",
            portnums_pb2.PortNum.RANGE_TEST_APP: "RANGE_TEST_APP",
            portnums_pb2.PortNum.TELEMETRY_APP: "TELEMETRY_APP",
            portnums_pb2.PortNum.ZPS_APP: "ZPS_APP",
            portnums_pb2.PortNum.SIMULATOR_APP: "SIMULATOR_APP",
            portnums_pb2.PortNum.TRACEROUTE_APP: "TRACEROUTE_APP",
            portnums_pb2.PortNum.NEIGHBORINFO_APP: "NEIGHBORINFO_APP",
            portnums_pb2.PortNum.ATAK_PLUGIN: "ATAK_PLUGIN",
            portnums_pb2.PortNum.MAP_REPORT_APP: "MAP_REPORT_APP",
        }
        
        return portnum_names.get(portnum, f"UNKNOWN_{portnum}")

    def _extract_fields(self, data_msg: mesh_pb2.Data, packet_type: str) -> Dict[str, Any]:
        """
        Extract fields from message based on packet type.
        
        Args:
            data_msg: Decoded Data protobuf message
            packet_type: Identified packet type
            
        Returns:
            Dictionary of extracted fields
        """
        fields = {}
        
        try:
            payload = data_msg.payload
            
            if packet_type == "POSITION":
                fields = self._extract_position_fields(payload)
            elif packet_type == "TEXT_MESSAGE_APP":
                fields = self._extract_text_message_fields(payload)
            elif packet_type == "TELEMETRY_APP":
                fields = self._extract_telemetry_fields(payload)
            elif packet_type == "NODEINFO_APP":
                fields = self._extract_nodeinfo_fields(payload)
            else:
                # For unknown types, just show raw payload info
                fields["payload_size"] = len(payload)
                if len(payload) > 0 and len(payload) < 100:
                    try:
                        fields["payload_text"] = payload.decode("utf-8", errors="ignore")
                    except:
                        fields["payload_hex"] = payload.hex()[:100]
        
        except Exception as e:
            logger.debug(f"Error extracting fields for {packet_type}: {e}")
            fields["extraction_error"] = str(e)
        
        return fields

    def _extract_position_fields(self, payload: bytes) -> Dict[str, Any]:
        """Extract fields from POSITION packet."""
        fields = {}
        
        try:
            position = mesh_pb2.Position()
            position.ParseFromString(payload)
            
            # Convert fixed-point integers to floats
            if position.latitude_i != 0:
                fields["latitude"] = position.latitude_i * 1e-7
            if position.longitude_i != 0:
                fields["longitude"] = position.longitude_i * 1e-7
            if position.altitude != 0:
                fields["altitude"] = position.altitude
            if position.time != 0:
                fields["time"] = datetime.fromtimestamp(position.time)
            if position.precision_bits != 0:
                fields["precision_bits"] = position.precision_bits
                
        except Exception as e:
            logger.debug(f"Error parsing position: {e}")
            fields["parse_error"] = str(e)
        
        return fields

    def _extract_text_message_fields(self, payload: bytes) -> Dict[str, Any]:
        """Extract fields from TEXT_MESSAGE_APP packet."""
        fields = {}
        
        try:
            # Text messages are just UTF-8 strings
            text = payload.decode("utf-8", errors="replace")
            fields["text"] = text
        except Exception as e:
            logger.debug(f"Error parsing text message: {e}")
            fields["parse_error"] = str(e)
        
        return fields

    def _extract_telemetry_fields(self, payload: bytes) -> Dict[str, Any]:
        """Extract fields from TELEMETRY_APP packet."""
        fields = {}
        
        try:
            telemetry = telemetry_pb2.Telemetry()
            telemetry.ParseFromString(payload)
            
            # Check which telemetry variant is present
            if telemetry.HasField("device_metrics"):
                metrics = telemetry.device_metrics
                if metrics.battery_level != 0:
                    fields["battery_level"] = metrics.battery_level
                if metrics.voltage != 0:
                    fields["voltage"] = metrics.voltage
                if metrics.channel_utilization != 0:
                    fields["channel_utilization"] = metrics.channel_utilization
                if metrics.air_util_tx != 0:
                    fields["air_util_tx"] = metrics.air_util_tx
            
            if telemetry.HasField("environment_metrics"):
                env = telemetry.environment_metrics
                if env.temperature != 0:
                    fields["temperature"] = env.temperature
                if env.relative_humidity != 0:
                    fields["humidity"] = env.relative_humidity
                if env.barometric_pressure != 0:
                    fields["pressure"] = env.barometric_pressure
            
            if telemetry.HasField("power_metrics"):
                power = telemetry.power_metrics
                if power.ch1_voltage != 0:
                    fields["ch1_voltage"] = power.ch1_voltage
                if power.ch1_current != 0:
                    fields["ch1_current"] = power.ch1_current
                    
        except Exception as e:
            logger.debug(f"Error parsing telemetry: {e}")
            fields["parse_error"] = str(e)
        
        return fields

    def _extract_nodeinfo_fields(self, payload: bytes) -> Dict[str, Any]:
        """Extract fields from NODEINFO_APP packet."""
        fields = {}
        
        try:
            user = mesh_pb2.User()
            user.ParseFromString(payload)
            
            if user.id:
                fields["node_id"] = user.id
            if user.long_name:
                fields["long_name"] = user.long_name
            if user.short_name:
                fields["short_name"] = user.short_name
            if user.macaddr:
                fields["macaddr"] = user.macaddr.hex()
            if user.hw_model != 0:
                fields["hardware_model"] = user.hw_model
                
        except Exception as e:
            logger.debug(f"Error parsing nodeinfo: {e}")
            fields["parse_error"] = str(e)
        
        return fields

    def _format_node_id(self, node_id: int) -> str:
        """
        Format node ID as hex string.
        
        Args:
            node_id: Integer node ID
            
        Returns:
            Formatted node ID string (e.g., "!a1b2c3d4")
        """
        if node_id == 0 or node_id == 0xFFFFFFFF:
            return "broadcast"
        return f"!{node_id:08x}"
