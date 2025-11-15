# Developer Documentation

This document provides technical details about the Meshtastic MQTT Monitor architecture, components, and extension points for developers who want to understand or extend the codebase.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Adding Support for New Packet Types](#adding-support-for-new-packet-types)
- [Extension Points](#extension-points)
- [Code Examples](#code-examples)
- [Testing Strategy](#testing-strategy)
- [Performance Considerations](#performance-considerations)

## Architecture Overview

The Meshtastic MQTT Monitor follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                      │
│                          (main.py)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Manager                     │
│                       (config.py)                            │
│  - Load YAML config                                          │
│  - Parse CLI arguments                                       │
│  - Merge configurations                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Meshtastic Monitor                        │
│                       (monitor.py)                           │
│  - Coordinate components                                     │
│  - Handle application lifecycle                              │
└───────┬──────────────────┬──────────────────┬───────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ MQTT Client  │  │   Message    │  │   Output     │
│              │  │   Decoder    │  │  Formatter   │
│(mqtt_client) │  │  (decoder)   │  │ (formatter)  │
│              │  │              │  │              │
│- Connect     │  │- Decrypt     │  │- Format      │
│- Subscribe   │  │- Decode      │  │- Colorize    │
│- Receive     │  │- Extract     │  │- Highlight   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Design Principles

1. **Modularity**: Each component has a single, well-defined responsibility
2. **Testability**: Components can be tested in isolation with mocks
3. **Extensibility**: Easy to add new packet types, formatters, or outputs
4. **Configuration-Driven**: Behavior controlled through configuration, not code changes
5. **Error Resilience**: Graceful handling of errors without crashing

## Component Details

### 1. Configuration Manager (`src/config.py`)

**Purpose**: Manage all application configuration from YAML files and CLI arguments.

**Key Classes**:

```python
@dataclass
class MQTTConfig:
    """MQTT broker connection settings"""
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    use_tls: bool
    ca_cert: Optional[str]

@dataclass
class MonitorConfig:
    """Complete application configuration"""
    mqtt: MQTTConfig
    topic: str
    channels: Optional[List[str]]
    channel_keys: Dict[str, str]
    display_fields: Dict[str, List[str]]
    colors: ColorConfig
    keywords: List[KeywordConfig]

class ConfigManager:
    """Configuration loading and management"""
    @staticmethod
    def load_config(file_path: str) -> MonitorConfig
    
    @staticmethod
    def merge_cli_args(config: MonitorConfig, args: Namespace) -> MonitorConfig
    
    @staticmethod
    def validate_config(config: MonitorConfig) -> bool
```

**Responsibilities**:
- Load and parse YAML configuration files
- Create default configuration if none exists
- Parse command-line arguments
- Merge CLI args with file config (CLI takes precedence)
- Validate configuration for correctness
- Provide typed access to configuration values

**Extension Points**:
- Add new configuration sections by extending dataclasses
- Add new CLI arguments in `create_argument_parser()`
- Add validation rules in `validate_config()`

### 2. MQTT Client (`src/mqtt_client.py`)

**Purpose**: Handle MQTT broker connection and message reception.

**Key Classes**:

```python
class MQTTClient:
    """MQTT client wrapper with reconnection logic"""
    
    def __init__(self, config: MQTTConfig, on_message_callback: Callable):
        """Initialize with config and message callback"""
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
    
    def subscribe(self, topic: str) -> bool:
        """Subscribe to MQTT topic pattern"""
    
    def disconnect(self):
        """Disconnect from broker"""
    
    def is_connected(self) -> bool:
        """Check connection status"""
```

**Responsibilities**:
- Establish connection to MQTT broker
- Handle TLS/SSL connections
- Subscribe to topic patterns with wildcards
- Receive messages and invoke callback
- Implement reconnection with exponential backoff
- Handle connection errors gracefully

**Internal Methods**:
- `_on_connect()`: Called when connection established
- `_on_disconnect()`: Called when connection lost
- `_on_message()`: Called when message received

**Extension Points**:
- Customize reconnection strategy
- Add connection status callbacks
- Implement message queuing during disconnection

### 3. Message Decoder (`src/decoder.py`)

**Purpose**: Decode and decrypt Meshtastic protobuf messages.

**Key Classes**:

```python
@dataclass
class DecodedMessage:
    """Decoded message with extracted fields"""
    packet_type: str
    channel: str
    from_node: str
    to_node: str
    timestamp: datetime
    fields: Dict[str, Any]
    raw_data: bytes
    decryption_success: bool

class MessageDecoder:
    """Decode Meshtastic protobuf messages"""
    
    def __init__(self, channel_keys: Dict[str, str]):
        """Initialize with encryption keys"""
    
    def decode(self, mqtt_topic: str, payload: bytes) -> DecodedMessage:
        """Decode MQTT message to structured data"""
    
    def _decrypt_payload(self, payload: bytes, channel: str) -> bytes:
        """Decrypt encrypted message payload"""
    
    def _identify_packet_type(self, decoded_proto: Any) -> str:
        """Identify packet type from protobuf"""
    
    def _extract_fields(self, decoded_proto: Any, packet_type: str) -> Dict[str, Any]:
        """Extract relevant fields based on packet type"""
```

**Responsibilities**:
- Parse MQTT topic to extract channel information
- Decrypt encrypted payloads using channel keys
- Decode protobuf ServiceEnvelope and Data messages
- Identify packet type from portnum field
- Extract relevant fields based on packet type
- Handle decoding errors gracefully

**Packet Type Handling**:

The decoder uses a dispatch pattern for packet-specific extraction:

```python
def _extract_fields(self, decoded_proto: Any, packet_type: str) -> Dict[str, Any]:
    """Extract fields based on packet type"""
    extractors = {
        "POSITION": self._extract_position_fields,
        "TEXT_MESSAGE_APP": self._extract_text_message_fields,
        "TELEMETRY_APP": self._extract_telemetry_fields,
        "NODEINFO_APP": self._extract_nodeinfo_fields,
        # Add more packet types here
    }
    
    extractor = extractors.get(packet_type, self._extract_default_fields)
    return extractor(decoded_proto)
```

**Extension Points**:
- Add new packet type extractors
- Customize field extraction logic
- Add custom decryption methods
- Implement caching for performance

### 4. Output Formatter (`src/formatter.py`)

**Purpose**: Format decoded messages for console display with colors and highlighting.

**Key Classes**:

```python
class ANSIColors:
    """ANSI color code constants"""
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    # ... more colors
    RED_BOLD = "\033[1;31m"
    # ... more bold variants

class OutputFormatter:
    """Format messages for console output"""
    
    def __init__(self, color_config: ColorConfig, 
                 display_fields: Dict[str, List[str]], 
                 keywords: List[KeywordConfig]):
        """Initialize with formatting configuration"""
    
    def format_message(self, message: DecodedMessage) -> str:
        """Format decoded message for display"""
    
    def _apply_packet_type_color(self, text: str, packet_type: str) -> str:
        """Apply color based on packet type"""
    
    def _apply_keyword_highlighting(self, text: str) -> str:
        """Highlight configured keywords"""
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp consistently"""
    
    def _format_fields(self, fields: Dict[str, Any], packet_type: str) -> str:
        """Format fields based on display configuration"""
```

**Responsibilities**:
- Format messages in consistent output format
- Apply ANSI color codes based on packet type
- Highlight keywords with configured colors
- Format timestamps consistently
- Display only configured fields for each packet type
- Handle missing or null field values

**Output Format**:
```
[TIMESTAMP] [PACKET_TYPE] Channel: CHANNEL | From: NODE_ID | FIELD1: VALUE1 | FIELD2: VALUE2
```

**Extension Points**:
- Add new output formats (JSON, CSV, etc.)
- Customize field formatting
- Add new color schemes
- Implement output to file or logging

### 5. Meshtastic Monitor (`src/monitor.py`)

**Purpose**: Coordinate all components and manage application lifecycle.

**Key Classes**:

```python
class MeshtasticMonitor:
    """Main monitor application coordinator"""
    
    def __init__(self, config: MonitorConfig):
        """Initialize all components"""
    
    def start(self):
        """Start monitoring"""
    
    def stop(self):
        """Stop monitoring and cleanup"""
    
    def _on_message_received(self, topic: str, payload: bytes):
        """Handle received MQTT message"""
    
    def _display_startup_info(self):
        """Display startup information"""
```

**Responsibilities**:
- Initialize all components with configuration
- Start MQTT client and subscribe to topics
- Coordinate message flow: MQTT → Decoder → Formatter → Console
- Handle graceful shutdown
- Display startup and status information
- Manage application state

**Message Flow**:
1. MQTT client receives message
2. Calls `_on_message_received()` callback
3. Decoder decodes and decrypts message
4. Formatter formats message for display
5. Output printed to console

**Extension Points**:
- Add message filtering
- Implement message statistics
- Add multiple output destinations
- Implement message logging

### 6. CLI Entry Point (`main.py`)

**Purpose**: Application entry point with CLI argument parsing.

**Key Functions**:

```python
def main():
    """Main entry point"""
    # Parse arguments
    parser = ConfigManager.create_argument_parser()
    args = parser.parse_args()
    
    # Load configuration
    config = ConfigManager.load_config(args.config)
    config = ConfigManager.merge_cli_args(config, args)
    ConfigManager.validate_config(config)
    
    # Create and start monitor
    monitor = MeshtasticMonitor(config)
    
    # Handle graceful shutdown
    signal.signal(signal.SIGINT, lambda s, f: monitor.stop())
    signal.signal(signal.SIGTERM, lambda s, f: monitor.stop())
    
    monitor.start()
```

**Responsibilities**:
- Parse command-line arguments
- Load and merge configuration
- Create monitor instance
- Handle SIGINT/SIGTERM for graceful shutdown
- Display version information

## Data Flow

### Complete Message Flow

```
1. MQTT Broker
   │
   ▼
2. MQTT Client (mqtt_client.py)
   - Receives raw bytes on topic
   │
   ▼
3. Message Decoder (decoder.py)
   - Parse topic → extract channel
   - Decrypt payload (if encrypted)
   - Decode ServiceEnvelope protobuf
   - Decode Data protobuf
   - Identify packet type from portnum
   - Extract fields based on packet type
   │
   ▼
4. DecodedMessage Object
   - packet_type: str
   - channel: str
   - from_node: str
   - to_node: str
   - timestamp: datetime
   - fields: Dict[str, Any]
   │
   ▼
5. Output Formatter (formatter.py)
   - Format timestamp
   - Apply packet type color
   - Format fields based on config
   - Apply keyword highlighting
   │
   ▼
6. Console Output
   - Colored, formatted text
```

### Protobuf Decoding Flow

```
Raw MQTT Payload (bytes)
   │
   ▼
ServiceEnvelope.FromString()
   │
   ├─ channel_id (hash)
   ├─ gateway_id
   └─ packet (encrypted or plain)
      │
      ▼
   Decrypt (if encrypted)
      │
      ▼
   Data.FromString()
      │
      ├─ portnum (packet type identifier)
      ├─ payload (type-specific data)
      ├─ from (source node)
      ├─ to (destination node)
      └─ rx_time (timestamp)
         │
         ▼
   Type-Specific Decode
      │
      ├─ Position.FromString()
      ├─ User.FromString()
      ├─ Telemetry.FromString()
      └─ etc.
         │
         ▼
   Extract Fields
      │
      └─ Dict[str, Any]
```

## Adding Support for New Packet Types

Follow these steps to add support for a new Meshtastic packet type:

### Step 1: Identify the Packet Type

1. Check the Meshtastic protobuf definitions:
   - Look in the `meshtastic` Python package
   - Find the portnum value in `portnums.proto`
   - Find the message definition in relevant `.proto` file

Example: For `RANGE_TEST_APP` (portnum = 6):
```protobuf
message Position {
  int32 latitude_i = 1;
  int32 longitude_i = 2;
  int32 altitude = 3;
  // ... more fields
}
```

### Step 2: Add Field Extractor in Decoder

In `src/decoder.py`, add an extraction method:

```python
def _extract_range_test_fields(self, data_message: Any) -> Dict[str, Any]:
    """Extract fields from RANGE_TEST_APP packet."""
    try:
        # Import the protobuf message type
        from meshtastic.protobuf import mesh_pb2
        
        # Decode the payload
        range_test = mesh_pb2.Position()
        range_test.ParseFromString(data_message.payload)
        
        # Extract relevant fields
        fields = {
            "sequence": range_test.sequence,
            "distance": range_test.distance,
            "rssi": range_test.rssi,
            "snr": range_test.snr,
        }
        
        return fields
    except Exception as e:
        return {"error": str(e)}
```

### Step 3: Register the Extractor

Add the extractor to the dispatch dictionary in `_extract_fields()`:

```python
def _extract_fields(self, decoded_proto: Any, packet_type: str) -> Dict[str, Any]:
    extractors = {
        "POSITION": self._extract_position_fields,
        "TEXT_MESSAGE_APP": self._extract_text_message_fields,
        "TELEMETRY_APP": self._extract_telemetry_fields,
        "NODEINFO_APP": self._extract_nodeinfo_fields,
        "RANGE_TEST_APP": self._extract_range_test_fields,  # Add this
    }
    
    extractor = extractors.get(packet_type, self._extract_default_fields)
    return extractor(decoded_proto)
```

### Step 4: Add Default Display Configuration

In `src/config.py`, add default display fields:

```python
@staticmethod
def get_default_config() -> MonitorConfig:
    config = MonitorConfig()
    
    config.display_fields = {
        # ... existing packet types
        "RANGE_TEST_APP": ["sequence", "distance", "rssi", "snr"],
    }
    
    config.colors.packet_type_colors = {
        # ... existing colors
        "RANGE_TEST_APP": "cyan",
    }
    
    return config
```

### Step 5: Update Example Configuration

In `config.example.yaml`, add documentation:

```yaml
display:
  fields:
    # ... existing packet types
    
    # Range test packets
    RANGE_TEST_APP:
      - sequence
      - distance
      - rssi
      - snr

colors:
  packet_types:
    # ... existing colors
    RANGE_TEST_APP: "cyan"
```

### Step 6: Add Tests

In `tests/test_decoder.py`, add tests for the new packet type:

```python
def test_decode_range_test_message():
    """Test decoding of RANGE_TEST_APP messages."""
    decoder = MessageDecoder(channel_keys={})
    
    # Create test payload
    payload = create_test_range_test_payload(
        sequence=42,
        distance=1500,
        rssi=-85,
        snr=8.5
    )
    
    # Decode message
    result = decoder.decode("msh/US/2/e/LongFast", payload)
    
    # Assert expected results
    assert result.packet_type == "RANGE_TEST_APP"
    assert result.fields["sequence"] == 42
    assert result.fields["distance"] == 1500
    assert result.fields["rssi"] == -85
    assert result.fields["snr"] == 8.5
```

### Step 7: Update Documentation

Update `README.md` to list the new packet type in the "Supported Packet Types" section.

## Extension Points

### Custom Output Formatters

Create a new formatter class that implements the same interface:

```python
class JSONFormatter:
    """Format messages as JSON"""
    
    def format_message(self, message: DecodedMessage) -> str:
        """Format message as JSON string"""
        output = {
            "timestamp": message.timestamp.isoformat(),
            "packet_type": message.packet_type,
            "channel": message.channel,
            "from": message.from_node,
            "to": message.to_node,
            "fields": message.fields
        }
        return json.dumps(output)
```

Use it in the monitor:

```python
# In monitor.py
formatter = JSONFormatter()  # Instead of OutputFormatter
```

### Custom Message Filters

Add filtering logic in the monitor:

```python
class MeshtasticMonitor:
    def __init__(self, config: MonitorConfig, message_filter: Optional[Callable] = None):
        self.message_filter = message_filter or (lambda msg: True)
    
    def _on_message_received(self, topic: str, payload: bytes):
        decoded = self.decoder.decode(topic, payload)
        
        # Apply filter
        if not self.message_filter(decoded):
            return
        
        formatted = self.formatter.format_message(decoded)
        print(formatted)
```

Usage:

```python
# Filter to only position messages
def position_only(msg: DecodedMessage) -> bool:
    return msg.packet_type == "POSITION"

monitor = MeshtasticMonitor(config, message_filter=position_only)
```

### Message Statistics

Add statistics tracking:

```python
class MessageStatistics:
    """Track message statistics"""
    
    def __init__(self):
        self.total_messages = 0
        self.by_packet_type = defaultdict(int)
        self.by_channel = defaultdict(int)
        self.decryption_failures = 0
    
    def record_message(self, message: DecodedMessage):
        self.total_messages += 1
        self.by_packet_type[message.packet_type] += 1
        self.by_channel[message.channel] += 1
        if not message.decryption_success:
            self.decryption_failures += 1
    
    def print_summary(self):
        print(f"\nTotal messages: {self.total_messages}")
        print("\nBy packet type:")
        for ptype, count in self.by_packet_type.items():
            print(f"  {ptype}: {count}")
        print(f"\nDecryption failures: {self.decryption_failures}")
```

### Output to File

Add file logging:

```python
class FileLogger:
    """Log messages to file"""
    
    def __init__(self, filename: str):
        self.file = open(filename, 'a')
    
    def log_message(self, formatted_message: str):
        timestamp = datetime.now().isoformat()
        self.file.write(f"{timestamp} {formatted_message}\n")
        self.file.flush()
    
    def close(self):
        self.file.close()
```

## Code Examples

### Example 1: Custom Packet Type Handler

```python
# In src/decoder.py

def _extract_custom_sensor_fields(self, data_message: Any) -> Dict[str, Any]:
    """Extract fields from custom sensor packet."""
    try:
        # Assuming custom sensor data in payload
        payload = data_message.payload
        
        # Parse custom format (example: binary struct)
        import struct
        sensor_id, temperature, humidity = struct.unpack('!Hff', payload[:10])
        
        return {
            "sensor_id": sensor_id,
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
        }
    except Exception as e:
        return {"error": f"Failed to parse custom sensor: {e}"}
```

### Example 2: Custom Color Scheme

```python
# In src/formatter.py

class CustomColorScheme:
    """Custom color scheme for specific use case"""
    
    COLORS = {
        "POSITION": ANSIColors.GREEN_BOLD,
        "TEXT_MESSAGE_APP": ANSIColors.CYAN_BOLD,
        "TELEMETRY_APP": ANSIColors.YELLOW,
        "EMERGENCY": ANSIColors.RED_BOLD,
    }
    
    @classmethod
    def get_color(cls, packet_type: str) -> str:
        return cls.COLORS.get(packet_type, ANSIColors.WHITE)
```

### Example 3: Message Replay from File

```python
# Replay captured messages from file

class MessageReplayer:
    """Replay messages from captured file"""
    
    def __init__(self, filename: str, decoder: MessageDecoder, formatter: OutputFormatter):
        self.filename = filename
        self.decoder = decoder
        self.formatter = formatter
    
    def replay(self, speed: float = 1.0):
        """Replay messages at specified speed multiplier"""
        with open(self.filename, 'rb') as f:
            while True:
                # Read timestamp and message
                timestamp_bytes = f.read(8)
                if not timestamp_bytes:
                    break
                
                timestamp = struct.unpack('d', timestamp_bytes)[0]
                length = struct.unpack('I', f.read(4))[0]
                topic = f.read(length).decode('utf-8')
                length = struct.unpack('I', f.read(4))[0]
                payload = f.read(length)
                
                # Decode and display
                decoded = self.decoder.decode(topic, payload)
                formatted = self.formatter.format_message(decoded)
                print(formatted)
                
                # Sleep based on speed
                time.sleep(1.0 / speed)
```

## Testing Strategy

### Unit Test Structure

```python
# tests/test_decoder.py

class TestMessageDecoder:
    """Test suite for MessageDecoder"""
    
    @pytest.fixture
    def decoder(self):
        """Create decoder instance for tests"""
        channel_keys = {
            "TestChannel": "AQ=="
        }
        return MessageDecoder(channel_keys)
    
    def test_decode_position_message(self, decoder):
        """Test position message decoding"""
        # Arrange
        payload = create_test_position_payload()
        
        # Act
        result = decoder.decode("msh/US/2/e/TestChannel", payload)
        
        # Assert
        assert result.packet_type == "POSITION"
        assert "latitude" in result.fields
        assert "longitude" in result.fields
    
    def test_decrypt_encrypted_message(self, decoder):
        """Test decryption of encrypted messages"""
        # Test implementation
        pass
    
    def test_handle_invalid_payload(self, decoder):
        """Test error handling for invalid payloads"""
        # Test implementation
        pass
```

### Integration Test Example

```python
# tests/test_integration.py

def test_end_to_end_message_flow(mock_mqtt_broker):
    """Test complete message flow"""
    # Setup
    config = ConfigManager.get_default_config()
    monitor = MeshtasticMonitor(config)
    
    # Create test message
    test_payload = create_test_position_payload(
        latitude=37.7749,
        longitude=-122.4194
    )
    
    # Simulate MQTT message
    mock_mqtt_broker.publish("msh/US/2/e/LongFast", test_payload)
    
    # Verify
    assert monitor.message_count == 1
    # Additional assertions
```

## Performance Considerations

### Message Processing Performance

- **Protobuf Decoding**: Fast, typically <1ms per message
- **Decryption**: Adds ~1-2ms per encrypted message
- **Formatting**: Minimal overhead, <0.5ms per message

### Optimization Tips

1. **Reduce Field Extraction**: Only extract fields you need
2. **Batch Processing**: Process multiple messages before output
3. **Async I/O**: Use async MQTT client for high-throughput scenarios
4. **Caching**: Cache decoded protobuf schemas
5. **Filtering**: Filter messages early in the pipeline

### Memory Usage

- **Baseline**: ~20-30 MB for Python runtime and libraries
- **Per Message**: ~1-2 KB for decoded message objects
- **Connection**: ~5-10 MB for MQTT client buffers

### Scalability

For high-message-rate scenarios:
- Use message queuing between components
- Implement backpressure handling
- Consider multi-threaded processing
- Add message sampling/filtering

---

This developer documentation should help you understand the codebase and extend it for your needs. For questions or clarifications, please open an issue on GitHub.
