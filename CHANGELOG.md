# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

## Change Categories

Changes are grouped into the following categories:
- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security vulnerability fixes

---

## [0.1.0] - 2024-11-15

### Added
- Initial release of Meshtastic MQTT Monitor
- MQTT client wrapper with connection handling and reconnection logic
- Message decoder with support for encrypted and unencrypted messages
- Protobuf message decoding for common packet types (POSITION, TEXT_MESSAGE_APP, TELEMETRY_APP, NODEINFO_APP)
- Output formatter with ANSI color support and keyword highlighting
- YAML-based configuration management with default values
- Command-line argument support for all configuration options
- Comprehensive test suite with unit and integration tests
- Documentation including README, CONTRIBUTING, and DEVELOPER guides
- Example configuration file with detailed comments
- Support for multiple channels with channel-specific encryption keys
- Customizable display fields for each packet type
- Configurable color schemes for packet types and keyword highlights
- Graceful shutdown handling with SIGINT/SIGTERM support
- Version information display via --version flag and startup output

[0.1.0]: https://github.com/meshtastic/meshtastic-mqtt-monitor/releases/tag/v0.1.0
