# Requirements Document

## Introduction

This document specifies the requirements for a Meshtastic MQTT Monitor application. The application monitors MQTT traffic from Meshtastic devices, decodes protobuf messages, and displays formatted output to assist with debugging and development. The monitor supports configurable MQTT connections, channel-specific encryption, customizable message formatting, and keyword highlighting.

## Glossary

- **Monitor Application**: The Python-based command-line application that subscribes to MQTT topics and displays decoded Meshtastic messages
- **MQTT Broker**: The message broker server that receives and distributes Meshtastic device traffic
- **Meshtastic Protocol**: The communication protocol used by Meshtastic mesh network devices, utilizing Protocol Buffers for message encoding
- **Channel**: A logical communication path in Meshtastic that may have its own encryption key
- **Protobuf**: Protocol Buffers, a language-neutral mechanism for serializing structured data
- **Packet Type**: The category of Meshtastic message (e.g., Location, Text Message, Telemetry)
- **Topic Filter**: An MQTT topic pattern that determines which messages the Monitor Application subscribes to
- **Encryption Key**: A cryptographic key used to decrypt messages on a specific Meshtastic channel
- **Keyword Highlight**: A user-defined term that triggers visual emphasis when found in message content
- **Configuration File**: A YAML file containing all Monitor Application settings and preferences

## Requirements

### Requirement 1

**User Story:** As a Meshtastic developer, I want to configure MQTT connection parameters in a YAML file, so that I can easily connect to different MQTT brokers without modifying code

#### Acceptance Criteria

1. THE Monitor Application SHALL read connection parameters from a YAML configuration file located in the application directory
2. THE Configuration File SHALL include fields for MQTT broker address, port number, username, password, and security settings
3. THE Monitor Application SHALL use default values of host "mqtt.thevillages.com", username "meshdev", and password "large4cats" when no configuration is provided
4. WHEN the Configuration File is missing, THE Monitor Application SHALL create a default configuration file with the standard default values
5. THE Monitor Application SHALL support both secure and non-secure MQTT connections based on the security configuration
6. WHEN connection to the MQTT Broker fails, THE Monitor Application SHALL display the connection error details and retry mechanism status

### Requirement 2

**User Story:** As a user, I want to specify which MQTT topics and channels to monitor, so that I can focus on relevant traffic and reduce noise

#### Acceptance Criteria

1. THE Configuration File SHALL include a topic filter field that specifies the base MQTT topic to monitor
2. THE Monitor Application SHALL subscribe to all channels under the specified topic by default
3. WHERE the user specifies a channel filter list, THE Monitor Application SHALL subscribe only to the specified channels
4. THE Monitor Application SHALL support MQTT wildcard patterns in topic specifications
5. WHEN a message arrives on a subscribed topic, THE Monitor Application SHALL process and display the message

### Requirement 3

**User Story:** As a Meshtastic network operator, I want to configure encryption keys for different channels, so that I can decrypt and view encrypted messages

#### Acceptance Criteria

1. THE Configuration File SHALL include a section for defining channel-specific encryption keys
2. THE Monitor Application SHALL support multiple encryption key definitions, each associated with a channel identifier
3. WHEN a message arrives on an encrypted channel, THE Monitor Application SHALL attempt decryption using the configured key for that channel
4. IF decryption fails or no key is configured, THEN THE Monitor Application SHALL display the message as encrypted with an indicator
5. THE Monitor Application SHALL handle unencrypted messages without requiring encryption key configuration

### Requirement 4

**User Story:** As a developer debugging Meshtastic traffic, I want messages decoded from protobuf format with clear packet type indicators, so that I can quickly understand message content

#### Acceptance Criteria

1. THE Monitor Application SHALL use Meshtastic protobuf definitions to decode incoming messages
2. THE Monitor Application SHALL identify the packet type for each message (Location, Text Message, Telemetry, etc.)
3. THE Monitor Application SHALL display a packet type indicator at the beginning of each output line (e.g., [Location], [Message])
4. WHEN a message cannot be decoded, THE Monitor Application SHALL display an error indicator with available raw data
5. THE Monitor Application SHALL display timestamp information for each received message

### Requirement 5

**User Story:** As a user, I want to customize which fields are displayed for each message type, so that I can see the information most relevant to my debugging needs

#### Acceptance Criteria

1. THE Configuration File SHALL include a section defining display fields for each packet type
2. THE Monitor Application SHALL provide reasonable default field configurations for common packet types
3. THE Monitor Application SHALL display only the configured fields for each packet type
4. WHERE no custom configuration exists for a packet type, THE Monitor Application SHALL use the default field configuration
5. THE Configuration File SHALL support field ordering to control the display sequence

### Requirement 6

**User Story:** As a user monitoring specific events, I want to define keywords that highlight matching messages with configurable colors, so that I can quickly identify messages of interest

#### Acceptance Criteria

1. THE Configuration File SHALL include a section for defining keyword highlight rules with associated color specifications
2. THE Monitor Application SHALL support multiple keyword definitions with case-sensitive and case-insensitive matching options
3. WHEN a message contains a configured keyword, THE Monitor Application SHALL apply the configured color highlighting to the output line
4. THE Monitor Application SHALL support ANSI color codes for terminal output highlighting
5. THE Monitor Application SHALL perform keyword matching on decoded message content, not raw protobuf data

### Requirement 7

**User Story:** As a user running the monitor application, I want to override configuration file settings via command-line arguments, so that I can quickly test different settings without editing the configuration file

#### Acceptance Criteria

1. THE Monitor Application SHALL accept command-line arguments for all configuration options available in the Configuration File
2. WHEN a command-line argument is provided, THE Monitor Application SHALL use the command-line value instead of the Configuration File value
3. THE Monitor Application SHALL support command-line arguments for MQTT connection parameters (address, port, username, password, security)
4. THE Monitor Application SHALL support command-line arguments for topic filters and channel specifications
5. THE Monitor Application SHALL support command-line arguments for color configuration including packet type colors and keyword highlight colors
6. WHERE no command-line argument is provided for a setting, THE Monitor Application SHALL use the value from the Configuration File

### Requirement 8

**User Story:** As a developer contributing to the project, I want comprehensive developer documentation and a properly configured repository, so that I can understand the codebase and contribute effectively

#### Acceptance Criteria

1. THE Monitor Application repository SHALL include a README file with project overview, installation instructions, and usage examples
2. THE Monitor Application repository SHALL include a CONTRIBUTING file with guidelines for code style, testing, and pull request procedures
3. THE Monitor Application repository SHALL include dependency management files (requirements.txt or pyproject.toml) listing all required packages
4. THE Monitor Application repository SHALL include developer documentation explaining the architecture, key modules, and extension points
5. THE Monitor Application repository SHALL include example configuration files demonstrating common use cases

### Requirement 9

**User Story:** As a project maintainer, I want automated dependency updates and semantic versioning, so that the application stays secure and users can track releases

#### Acceptance Criteria

1. THE Monitor Application repository SHALL include a Renovate configuration file for automated dependency update pull requests
2. THE Monitor Application SHALL use semantic versioning (MAJOR.MINOR.PATCH) for release numbering
3. THE Monitor Application SHALL include version information accessible via a command-line flag (e.g., --version)
4. THE Monitor Application repository SHALL include a CHANGELOG file documenting version history and changes
5. THE Monitor Application SHALL display version information in the startup output

### Requirement 10

**User Story:** As a user running the monitor application, I want clear console output with configurable color-coded message information, so that I can easily read and analyze the traffic

#### Acceptance Criteria

1. THE Monitor Application SHALL display each message on a separate line with consistent formatting
2. THE Monitor Application SHALL include timestamp, packet type, channel identifier, and decoded content in each output line
3. THE Monitor Application SHALL use configurable ANSI color codes to distinguish different packet types
4. THE Configuration File SHALL include a section defining color mappings for each packet type with reasonable defaults
5. WHEN the application starts, THE Monitor Application SHALL display connection status and subscription information
6. THE Monitor Application SHALL continue running and displaying messages until terminated by the user
