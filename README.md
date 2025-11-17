# Meshtastic MQTT Monitor

A Python-based command-line tool for monitoring, decoding, and displaying Meshtastic MQTT traffic in real-time. Perfect for debugging, development, and monitoring Meshtastic mesh networks.

## Features

- **Real-time MQTT Monitoring**: Subscribe to Meshtastic MQTT topics and view messages as they arrive
- **Protobuf Decoding**: Automatically decode Meshtastic protobuf messages into human-readable format
- **Encryption Support**: Decrypt messages using channel-specific encryption keys
- **Customizable Display**: Configure which fields to display for each packet type
- **Color-Coded Output**: Visual distinction between packet types with ANSI color support
- **Keyword Highlighting**: Highlight specific keywords in messages with custom colors
- **Flexible Configuration**: YAML configuration file with command-line overrides
- **Multiple Packet Types**: Support for Position, Text Messages, Telemetry, Node Info, and more

## Example Output

```
[2025-11-17 11:51:24] | [TEXT_MESSAGE_APP] | Channel: TheVillages | From: !a2ebd930 | text: "hello villages"
[2025-11-17 11:51:26] | [POSITION] | Channel: LongFast | From: !16cd802c | latitude: 28.862054 | longitude: -81.972429 | altitude: 30
[2025-11-17 11:51:26] | [POSITION] | Channel: LongFast | From: !16cd802c | To: !ffffffff | altitude: 30 | timestamp: 1763398286
[2025-11-17 11:51:45] | [MAP_REPORT_APP] | Channel:  | From: !7c5ab850 | payload_size: 72 | payload_text: "
sm-0 Steve's heltec v3, 6dBism-0 +*2.5.18.89ebafc0@M4U`h*"
[2025-11-17 11:51:54] | [NODEINFO_APP] | Channel: LongFast | From: !433d2df8 | To: !caa16791 | node_id: "!433d2df8" | long_name: "Dispatcher" | short_name: "Hans" | hardware_model: 43 (TWC_MESH_V4)
[2025-11-17 11:51:54] | [NODEINFO_APP] | Channel: LongFast | From: !433d2df8 | To: !caa16791 | role: 0
[2025-11-17 11:53:13] | [TEXT_MESSAGE_APP] | Channel: TheVillages | From: !a2ebd930 | text: "hello villages"
[2025-11-17 11:53:38] | [ENCRYPTED] | Channel: GolfCart | From: !5e55aa92 | status: "Unable to decrypt or decode"
[2025-11-17 11:54:59] | [ENCRYPTED] | Channel: LongFast | From: !5a0f6f1d | status: "Unable to decrypt or decode"
[2025-11-17 11:55:15] | [ENCRYPTED] | Channel: LongFast | From: !2e9acc5a | status: "Unable to decrypt or decode"
[2025-11-17 11:55:22] | [ENCRYPTED] | Channel: LongFast | From: !7a6d7944 | status: "Unable to decrypt or decode"
[2025-11-17 11:55:50] | [TRACEROUTE_APP] | Channel: LongFast | From: !7c5ccbd0 | To: !21ad7a1c
[2025-11-17 11:55:50] | [] | Channel: LongFast | From: !7c5ccbd0 | To: !21ad7a1c | channel: 0 | id: 4086964994 | sender: "!433d2df8" | timestamp: 1763398470
[2025-11-17 11:56:12] | [POSITION] | Channel: LongFast | From: !da63b944 | latitude: 28.852224 | longitude: -82.001920 | altitude: 23
[2025-11-17 11:56:12] | [POSITION] | Channel: LongFast | From: !da63b944 | To: !ffffffff | altitude: 23 | timestamp: 1763398571
[2025-11-17 11:56:39] | [ENCRYPTED] | Channel: LongFast | From: !a2ebd930 | To: !33665f5c | status: "Unable to decrypt or decode"
[2025-11-17 11:56:41] | [NODEINFO_APP] | Channel: LongFast | From: !a2ebd930 | To: !33665f5c | node_id: "!a2ebd930" | long_name: "K3DO FL GW 🛰" | short_name: "🛰" | hardware_model: 31 (PICOMPUTER_S3)
[2025-11-17 11:56:41] | [NODEINFO_APP] | Channel: LongFast | From: !a2ebd930 | To: !33665f5c | role: 0
[2025-11-17 11:58:08] | [POSITION] | Channel: LongFast | From: !433d2df8 | latitude: 42.952294 | longitude: -70.791987 | altitude: 10
[2025-11-17 11:58:08] | [POSITION] | Channel: LongFast | From: !433d2df8 | To: !ffffffff | altitude: 10 | timestamp: 1763398608
[2025-11-17 11:58:11] | [POSITION] | Channel: LongFast | From: !433d2df8 | latitude: 42.952294 | longitude: -70.791987 | altitude: 10
[2025-11-17 11:58:11] | [POSITION] | Channel: LongFast | From: !433d2df8 | To: !ffffffff | altitude: 10 | timestamp: 1763398611
[2025-11-17 11:58:41] | [ENCRYPTED] | Channel: GolfCart | From: !5e55aa92 | status: "Unable to decrypt or decode"
[2025-11-17 12:00:14] | [ENCRYPTED] | Channel: GolfCart | From: !da63b944 | status: "Unable to decrypt or decode"
```
## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/meshtastic/meshtastic-mqtt-monitor.git
cd meshtastic-mqtt-monitor

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Install from PyPI (Coming Soon)

```bash
pip install meshtastic-mqtt-monitor
```

## Quick Start

1. **Run with default configuration** (connects to public Meshtastic MQTT server):

```bash
meshtastic-monitor
```

2. **Create a custom configuration file**:

```bash
# Copy the example configuration
cp config.example.yaml config.yaml

# Edit config.yaml with your settings
nano config.yaml

# Run with custom configuration
meshtastic-monitor --config config.yaml
```

3. **Override settings via command-line**:

```bash
# Connect to a different MQTT broker
meshtastic-monitor --host mqtt.example.com --username myuser --password mypass

# Monitor a specific topic
meshtastic-monitor --topic "msh/US/2/e/LongFast/#"

# Monitor specific channels only
meshtastic-monitor --channels "LongFast,Primary"
```

## Usage

### Basic Usage

```bash
meshtastic-monitor [OPTIONS]
```

### Command-Line Options

#### General Options

```
--version, -v          Show version information and exit
--config, -c PATH      Path to configuration file (default: config.yaml)
```

#### MQTT Connection Options

```
--host HOST            MQTT broker hostname or IP address
--port PORT            MQTT broker port (default: 1883)
--username USER        MQTT username for authentication
--password PASS        MQTT password for authentication
--use-tls              Enable TLS/SSL for MQTT connection
```

#### Monitoring Options

```
--topic TOPIC          MQTT topic pattern to monitor (supports wildcards)
--channels CHANNELS    Comma-separated list of channels to monitor
```

### Examples

#### Example 1: Monitor Public Meshtastic Server

```bash
# Uses default configuration (mqtt.villagesmesh.com)
meshtastic-monitor
```

#### Example 2: Monitor Specific Region and Channel

```bash
meshtastic-monitor --topic "msh/EU/1/e/#"
```

#### Example 3: Monitor with Custom MQTT Broker

```bash
meshtastic-monitor \
  --host mqtt.myserver.com \
  --port 8883 \
  --use-tls \
  --username myuser \
  --password mypassword
```

#### Example 4: Monitor Only Specific Channels

```bash
meshtastic-monitor --channels "LongFast,Primary"
```

#### Example 5: Use Custom Configuration File

```bash
meshtastic-monitor --config /path/to/my-config.yaml
```

## Configuration

### Configuration File

The monitor uses a YAML configuration file for settings. By default, it looks for `config.yaml` in the current directory. If not found, it creates one with default values.

See `config.example.yaml` for a comprehensive example with all available options and detailed comments.

### Configuration Structure

```yaml
version: "1.0"

mqtt:
  host: "mqtt.villagesmesh.com"
  port: 1883
  username: "meshdev"
  password: "large4cats"
  use_tls: false
  ca_cert: null

monitoring:
  topic: "msh/US/2/e/#"
  channels: null  # null = all channels

encryption:
  channels:
    - name: "LongFast"
      key: "AQ=="  # Base64 encoded key
    - name: "Primary"
      key: "1PG7OiApB3XvvX7g8kYzDYQD+CW+3Oi+Qs/LoIWh/gg="

display:
  fields:
    POSITION:
      - latitude
      - longitude
      - altitude
      - timestamp
    TEXT_MESSAGE_APP:
      - from
      - to
      - text
      - timestamp
    # ... more packet types

colors:
  packet_types:
    POSITION: "green"
    TEXT_MESSAGE_APP: "cyan"
    TELEMETRY_APP: "yellow"
    # ... more packet types
  keywords:
    - keyword: "emergency"
      case_sensitive: false
      color: "red_bold"
```

### Encryption Keys

To decrypt encrypted channels, you need the channel's encryption key (PSK - Pre-Shared Key):

1. **Get the key from Meshtastic app**:
   - Open channel settings
   - Copy the base64-encoded PSK

2. **Get the key from Meshtastic CLI**:
   ```bash
   meshtastic --info
   ```

3. **Add to configuration**:
   ```yaml
   encryption:
     channels:
       - name: "YourChannelName"
         key: "YourBase64EncodedKeyHere=="
   ```

### Display Fields

Customize which fields are shown for each packet type:

```yaml
display:
  fields:
    POSITION:
      - latitude
      - longitude
      - altitude
    TEXT_MESSAGE_APP:
      - from
      - text
```

Available fields depend on the packet type. See the Meshtastic protobuf definitions for all available fields.

### Color Configuration

Available colors:
- `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- Add `_bold` suffix for bold text: `red_bold`, `green_bold`, etc.

```yaml
colors:
  packet_types:
    POSITION: "green"
    TEXT_MESSAGE_APP: "cyan_bold"
  keywords:
    - keyword: "emergency"
      color: "red_bold"
```

## Output Format

Messages are displayed in the following format:

```
[TIMESTAMP] [PACKET_TYPE] Channel: CHANNEL | From: NODE_ID | FIELD1: VALUE1 | FIELD2: VALUE2
```

### Example Output

```
[2024-11-15 14:23:45] [POSITION] Channel: LongFast | From: !a1b2c3d4 | Lat: 37.7749 | Lon: -122.4194 | Alt: 15m
[2024-11-15 14:23:46] [TEXT_MESSAGE_APP] Channel: LongFast | From: !a1b2c3d4 | To: !e5f6g7h8 | Text: "Hello World"
[2024-11-15 14:23:47] [TELEMETRY_APP] Channel: LongFast | From: !a1b2c3d4 | Battery: 85% | Voltage: 4.1V | Temp: 22°C
[2024-11-15 14:23:48] [NODEINFO_APP] Channel: LongFast | From: !a1b2c3d4 | Name: "Base Station" | Model: TBEAM
```

## Supported Packet Types

The monitor supports the following Meshtastic packet types:

- **POSITION**: GPS location data (latitude, longitude, altitude)
- **TEXT_MESSAGE_APP**: Text messages between nodes
- **TELEMETRY_APP**: Device telemetry (battery, voltage, temperature)
- **NODEINFO_APP**: Node information (name, hardware model)
- **ROUTING_APP**: Mesh routing information
- **ADMIN_APP**: Administrative messages
- **WAYPOINT_APP**: Waypoint data
- **NEIGHBORINFO_APP**: Neighbor node information
- **TRACEROUTE_APP**: Network trace route data
- **DETECTION_SENSOR_APP**: Sensor detection data
- **REMOTE_HARDWARE_APP**: Remote hardware control
- **REPLY_APP**: Reply/acknowledgment messages
- **STORE_FORWARD_APP**: Store and forward messages

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MQTT broker

**Solutions**:
- Verify the broker hostname and port are correct
- Check if the broker requires authentication (username/password)
- Ensure firewall allows outbound connections on the MQTT port
- Try with `--use-tls` if the broker requires TLS (usually port 8883)
- Test connection with a simple MQTT client like `mosquitto_sub`:
  ```bash
  mosquitto_sub -h mqtt.villagesmesh.com -p 1883 -u meshdev -P large4cats -t "msh/#" -v
  ```

**Problem**: Authentication failed

**Solutions**:
- Verify username and password are correct
- Check if the broker requires TLS for authentication
- Ensure credentials are properly quoted in config file

### Decryption Issues

**Problem**: Messages show as [ENCRYPTED] or decryption fails

**Solutions**:
- Verify the encryption key is correct and properly base64-encoded
- Ensure the channel name in config matches the actual channel name
- Check that the key corresponds to the correct channel
- Try the default key "AQ==" for public channels
- Verify the key hasn't been changed on the Meshtastic device

**Problem**: Some messages decrypt, others don't

**Solutions**:
- Different channels may use different keys
- Add encryption keys for all channels you want to monitor
- Some messages may be on unencrypted channels (this is normal)

### Display Issues

**Problem**: Colors don't display correctly

**Solutions**:
- Ensure your terminal supports ANSI colors
- Try a different terminal emulator
- On Windows, use Windows Terminal or enable ANSI support
- Disable colors by setting all colors to "white" in config

**Problem**: Too much or too little information displayed

**Solutions**:
- Customize display fields in config.yaml
- Remove fields you don't need
- Add fields from protobuf definitions for more detail
- Use `--channels` to filter to specific channels

### Performance Issues

**Problem**: High CPU usage or slow performance

**Solutions**:
- Narrow the topic filter to reduce message volume
- Use `--channels` to monitor only specific channels
- Reduce the number of display fields
- Disable keyword highlighting if not needed

### Message Decoding Issues

**Problem**: Messages show as [DECODE_ERROR] or [UNKNOWN]

**Solutions**:
- This may indicate a new or unsupported packet type
- Check if you're using the latest version of the monitor
- Update the `meshtastic` Python library: `pip install --upgrade meshtastic`
- Report unknown packet types as issues on GitHub

### Configuration Issues

**Problem**: Configuration file not found or invalid

**Solutions**:
- Ensure config.yaml exists in the current directory
- Use `--config` to specify a different path
- Check YAML syntax (indentation, colons, quotes)
- Copy from config.example.yaml and modify
- Validate YAML syntax with an online validator

**Problem**: Command-line arguments not working

**Solutions**:
- Ensure arguments are spelled correctly (use `--help`)
- Quote values with spaces: `--topic "msh/US/2/e/#"`
- Use `=` or space: `--host=mqtt.example.com` or `--host mqtt.example.com`
- Check that config file isn't overriding your CLI arguments

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_decoder.py

# Run with verbose output
pytest -v
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Run flake8
flake8 src/ tests/

# Run mypy for type checking
mypy src/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later). See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Meshtastic](https://meshtastic.org/) - Open source mesh networking platform
- [Eclipse Paho](https://www.eclipse.org/paho/) - MQTT client library
- All contributors and users of this tool

## Support

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/meshtastic/meshtastic-mqtt-monitor/issues)
- **Discussions**: Join the conversation on [Meshtastic Discord](https://discord.gg/meshtastic)
- **Documentation**: See [Meshtastic Documentation](https://meshtastic.org/docs/)

## Related Projects

- [Meshtastic](https://github.com/meshtastic/Meshtastic) - Main Meshtastic firmware
- [Meshtastic Python](https://github.com/meshtastic/Meshtastic-python) - Official Python library
- [Meshtastic Web](https://github.com/meshtastic/web) - Web-based Meshtastic interface

---

Made with ❤️ for the Meshtastic community
