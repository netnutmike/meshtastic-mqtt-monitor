# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Python package structure with src/ directory
  - Create pyproject.toml with project metadata and dependencies
  - Add core dependencies: paho-mqtt, meshtastic, cryptography, PyYAML, colorama
  - Add development dependencies: pytest, pytest-mock, pytest-cov, black, flake8, mypy
  - Create .gitignore with Python-specific entries and config.yaml
  - Create LICENSE file with GPL v3 license text
  - Create initial README.md with project overview
  - _Requirements: 8.1, 8.3_

- [x] 2. Implement configuration management
  - [x] 2.1 Create configuration data models
    - Define MQTTConfig, ChannelConfig, DisplayFieldConfig, ColorConfig, KeywordConfig, and MonitorConfig classes
    - Use dataclasses or Pydantic for type safety
    - _Requirements: 1.2, 2.1_
  
  - [x] 2.2 Implement YAML configuration loading
    - Create ConfigManager class with load_config method
    - Implement default configuration generation with host=mqtt.thevillages.com, username=meshdev, password=large4cats
    - Add YAML schema validation
    - Handle missing or invalid configuration files
    - _Requirements: 1.1, 1.3, 1.4_
  
  - [x] 2.3 Implement command-line argument parsing
    - Create argument parser with all configuration options
    - Add --version flag support
    - Implement merge_cli_args method to override config file values
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.3_
  
  - [x] 2.4 Write unit tests for configuration manager
    - Test YAML parsing with valid and invalid inputs
    - Test CLI argument merging
    - Test default value generation
    - Test configuration validation
    - _Requirements: 1.1, 1.3, 7.2_

- [x] 3. Implement MQTT client wrapper
  - [x] 3.1 Create MQTTClient class
    - Implement connection handling with paho-mqtt
    - Add support for TLS/SSL connections
    - Implement topic subscription with wildcards
    - Add connection callback and message callback
    - _Requirements: 1.2, 1.5, 2.1, 2.2_
  
  - [x] 3.2 Implement reconnection logic
    - Add exponential backoff for reconnection attempts
    - Handle authentication failures gracefully
    - Implement connection status tracking
    - _Requirements: 1.5_
  
  - [x] 3.3 Write unit tests for MQTT client
    - Mock MQTT broker for testing
    - Test connection handling
    - Test subscription logic
    - Test reconnection behavior
    - _Requirements: 1.5_

- [x] 4. Implement message decoder
  - [x] 4.1 Create message decryption functionality
    - Implement channel key management
    - Add decryption using cryptography library
    - Handle decryption failures gracefully
    - Support base64-encoded keys from config
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.2 Implement protobuf message decoding
    - Create DecodedMessage data class
    - Decode ServiceEnvelope and Data messages using meshtastic library
    - Identify packet type from portnum
    - Extract fields for common packet types (POSITION, TEXT_MESSAGE_APP, TELEMETRY_APP, NODEINFO_APP)
    - Handle unknown packet types
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 4.3 Implement field extraction for packet types
    - Extract position data (latitude, longitude, altitude)
    - Extract text message data
    - Extract telemetry data
    - Extract node info data
    - Handle missing or malformed fields
    - _Requirements: 4.2, 5.1, 5.2_
  
  - [x] 4.4 Write unit tests for message decoder
    - Test decryption with valid and invalid keys
    - Test protobuf decoding for each packet type
    - Test field extraction accuracy
    - Test error handling for malformed messages
    - _Requirements: 3.3, 3.4, 4.4_

- [x] 5. Implement output formatter
  - [x] 5.1 Create ANSI color code utilities
    - Define ANSIColors class with color constants
    - Implement color code application functions
    - Add support for bold variants
    - Handle color mapping from config (string names to ANSI codes)
    - _Requirements: 6.4, 9.3, 9.4_
  
  - [x] 5.2 Implement message formatting
    - Create OutputFormatter class
    - Format timestamp consistently
    - Format packet type indicator with colors
    - Format message fields based on display configuration
    - Generate consistent output line format
    - _Requirements: 5.2, 5.3, 9.1, 9.2, 9.3_
  
  - [x] 5.3 Implement keyword highlighting
    - Add keyword matching (case-sensitive and case-insensitive)
    - Apply configured colors to matching keywords
    - Support multiple keywords with different colors
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [x] 5.4 Write unit tests for output formatter
    - Test color code application
    - Test keyword highlighting
    - Test field formatting
    - Test timestamp formatting
    - _Requirements: 6.3, 9.3_

- [x] 6. Implement main monitor application
  - [x] 6.1 Create MeshtasticMonitor class
    - Initialize all components (config, MQTT client, decoder, formatter)
    - Implement message callback that coordinates decoder and formatter
    - Add startup information display with version
    - Implement graceful shutdown handling
    - _Requirements: 9.5, 9.6_
  
  - [x] 6.2 Implement CLI entry point
    - Create main.py with argument parsing
    - Initialize ConfigManager and load configuration
    - Create and start MeshtasticMonitor
    - Handle SIGINT/SIGTERM for graceful shutdown
    - Display version information when requested
    - _Requirements: 7.1, 7.2, 9.3, 9.5_
  
  - [x] 6.3 Write integration tests
    - Test end-to-end message flow with mock MQTT broker
    - Test configuration integration
    - Test with encrypted and unencrypted messages
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 7. Create example configuration and documentation
  - [x] 7.1 Create example configuration file
    - Create config.example.yaml with all options documented
    - Include examples for multiple channels with encryption
    - Include examples for display field customization
    - Include examples for color configuration
    - Include examples for keyword highlighting
    - _Requirements: 8.5_
  
  - [x] 7.2 Write comprehensive README
    - Add project overview and features
    - Add installation instructions
    - Add usage examples with command-line arguments
    - Add configuration file documentation
    - Add troubleshooting section
    - _Requirements: 8.1_
  
  - [x] 7.3 Create CONTRIBUTING guide
    - Add code style guidelines (Black, Flake8)
    - Add testing requirements
    - Add pull request process
    - Add development setup instructions
    - _Requirements: 8.2_
  
  - [x] 7.4 Create developer documentation
    - Document architecture and component responsibilities
    - Document how to add support for new packet types
    - Document extension points
    - Add code examples for common customizations
    - _Requirements: 8.4_

- [x] 8. Set up versioning and dependency management
  - [x] 8.1 Implement version management
    - Add __version__ variable in package __init__.py
    - Display version in --version flag output
    - Display version in startup output
    - Use semantic versioning format
    - _Requirements: 9.2, 9.3, 9.5_
  
  - [x] 8.2 Create CHANGELOG
    - Create CHANGELOG.md with initial version entry
    - Document version format and change categories
    - _Requirements: 9.4_
  
  - [x] 8.3 Configure Renovate
    - Create renovate.json configuration file
    - Configure auto-merge rules for patch updates
    - Configure grouping for related dependencies
    - _Requirements: 9.1_

- [x] 9. Final integration and polish
  - [x] 9.1 Add default display field configurations
    - Define reasonable defaults for POSITION packet type
    - Define reasonable defaults for TEXT_MESSAGE_APP packet type
    - Define reasonable defaults for TELEMETRY_APP packet type
    - Define reasonable defaults for NODEINFO_APP packet type
    - Define reasonable defaults for other common packet types
    - _Requirements: 5.2, 5.4_
  
  - [x] 9.2 Add default color configurations
    - Define default colors for each packet type
    - Define reasonable default keyword highlight colors
    - Ensure colors are visible on both light and dark terminals
    - _Requirements: 9.4_
  
  - [x] 9.3 Verify all command-line arguments work
    - Test MQTT connection parameter overrides
    - Test topic and channel overrides
    - Test color configuration overrides
    - Test keyword highlight additions via CLI
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 9.4 Create package distribution setup
    - Configure pyproject.toml for package distribution
    - Add entry point for command-line script
    - Test installation from source
    - _Requirements: 8.3_
