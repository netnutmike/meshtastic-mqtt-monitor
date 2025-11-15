"""Configuration management for Meshtastic MQTT Monitor."""

import argparse
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


# Hardware model mapping (number to name)
# Based on Meshtastic protobuf HardwareModel enum
HARDWARE_MODELS = {
    0: "UNSET",
    1: "TLORA_V2",
    2: "TLORA_V1",
    3: "TLORA_V2_1_1P6",
    4: "TBEAM",
    5: "HELTEC_V2_0",
    6: "TBEAM_V0P7",
    7: "T_ECHO",
    8: "TLORA_V1_1P3",
    9: "RAK4631",
    10: "HELTEC_V2_1",
    11: "HELTEC_V1",
    12: "LILYGO_TBEAM_S3_CORE",
    13: "RAK11200",
    14: "NANO_G1",
    15: "TLORA_V2_1_1P8",
    16: "TLORA_T3_S3",
    17: "NANO_G1_EXPLORER",
    18: "NANO_G2_ULTRA",
    19: "LORA_TYPE",
    20: "WIPHONE",
    21: "WIO_WM1110",
    22: "RAK11310",
    23: "SENSELORA_RP2040",
    24: "SENSELORA_S3",
    25: "CANARYONE",
    26: "RP2040_LORA",
    27: "STATION_G1",
    28: "RAK11310_EPAPER",
    29: "T_DECK",
    30: "T_WATCH_S3",
    31: "PICOMPUTER_S3",
    32: "HELTEC_V3",
    33: "HELTEC_WSL_V3",
    34: "BETAFPV_2400_TX",
    35: "BETAFPV_900_NANO_TX",
    36: "RPI_PICO",
    37: "HELTEC_WIRELESS_TRACKER",
    38: "HELTEC_WIRELESS_PAPER",
    39: "T_BEAM_SUPREME",
    40: "UNPHONE",
    41: "TD_LORAC",
    42: "CDEBYTE_EORA_S3",
    43: "TWC_MESH_V4",
    44: "NRF52840_PCA10059",
    45: "NRF52_UNKNOWN",
    46: "PORTDUINO",
    47: "ANDROID_SIM",
    48: "DIY_V1",
    49: "NRF52840_DK",
    50: "NRF52840_PPR",
    51: "GENIEBLOCKS",
    52: "NRF52_PROMICRO_DIY",
    53: "RADIOMASTER_900_BANDIT_NANO",
    54: "HELTEC_CAPSULE_SENSOR_V3",
    55: "HELTEC_VISION_MASTER_T190",
    56: "HELTEC_VISION_MASTER_E213",
    57: "HELTEC_VISION_MASTER_E290",
    58: "HELTEC_MESH_NODE_T114",
    59: "SENSECAP_INDICATOR",
    60: "TRACKER_T1000_E",
    61: "RAK3172",
    62: "WIO_E5",
    63: "RADIOMASTER_900_BANDIT",
    64: "ME25LS01_4Y10TD",
    65: "RP2040_FEATHER_RFM95",
    66: "M5STACK_COREBASIC",
    67: "M5STACK_CORE2",
    68: "RPI_PICO2",
    69: "M5STACK_CORES3",
    70: "SEEED_XIAO_S3",
    71: "BETAFPV_2400_RX",
    72: "HELTEC_WT32",
    73: "ESP32_S3_PICO",
    74: "CHATTER_2",
    75: "HELTEC_WIRELESS_PAPER_V1_0",
    76: "HELTEC_PRO_V1_0",
    77: "SEEED_SENSECAP_CARD_TRACKER",
    78: "HELTEC_WIRELESS_TRACKER_V1_0",
    79: "EBYTE_E22_MBL_01",
    80: "HELTEC_WIRELESS_PAPER_V1_1",
    81: "PRIVATE_HW",
    255: "RESERVED",
}


@dataclass
class MQTTConfig:
    """MQTT broker connection configuration."""

    host: str = "mqtt.villagesmesh.com"
    port: int = 1883
    username: Optional[str] = "meshdev"
    password: Optional[str] = "large4cats"
    use_tls: bool = False
    ca_cert: Optional[str] = None


@dataclass
class ChannelConfig:
    """Channel-specific configuration including encryption."""

    name: str
    encryption_key: Optional[str] = None


@dataclass
class DisplayFieldConfig:
    """Display field configuration for a specific packet type."""

    packet_type: str
    fields: List[str] = field(default_factory=list)


@dataclass
class ColorConfig:
    """Color configuration for packet types and keywords."""

    packet_type_colors: Dict[str, str] = field(default_factory=dict)
    keyword_highlights: Dict[str, str] = field(default_factory=dict)


@dataclass
class KeywordConfig:
    """Keyword highlighting configuration."""

    keyword: str
    case_sensitive: bool = False
    color: str = "white"


@dataclass
class MonitorConfig:
    """Complete monitor application configuration."""

    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    topic: str = "msh/US/2/e/#"
    channels: Optional[List[str]] = None
    channel_keys: Dict[str, str] = field(default_factory=dict)
    display_fields: Dict[str, List[str]] = field(default_factory=dict)
    colors: ColorConfig = field(default_factory=ColorConfig)
    keywords: List[KeywordConfig] = field(default_factory=list)
    hardware_models: Dict[int, str] = field(default_factory=lambda: HARDWARE_MODELS.copy())
    filter_type: Optional[str] = None  # Filter to specific packet type
    filter_text: Optional[str] = None  # Filter messages containing text (grep-like)


class ConfigManager:
    """Manages configuration loading, validation, and merging."""

    DEFAULT_CONFIG_PATH = "config.yaml"

    @staticmethod
    def get_default_config() -> MonitorConfig:
        """Generate default configuration with standard values."""
        config = MonitorConfig()
        
        # Set default display fields for common packet types
        config.display_fields = {
            # Position/Location data
            "POSITION": ["latitude", "longitude", "altitude", "timestamp"],
            "POSITION_APP": ["latitude", "longitude", "altitude", "timestamp"],
            
            # Text messaging
            "TEXT_MESSAGE_APP": ["text", "timestamp"],
            
            # Telemetry data
            "TELEMETRY_APP": ["battery_level", "voltage", "temperature", "channel_utilization", "air_util_tx"],
            
            # Node information
            "NODEINFO_APP": ["node_id", "long_name", "short_name", "hardware_model", "role"],
            
            # Routing information
            "ROUTING_APP": ["route_request", "route_reply", "error_reason"],
            
            # Administrative messages
            "ADMIN_APP": ["admin_message"],
            
            # Waypoint data
            "WAYPOINT_APP": ["name", "description", "latitude", "longitude"],
            
            # Neighbor info
            "NEIGHBORINFO_APP": ["node_id", "snr", "node_broadcast_interval_secs"],
            
            # Traceroute
            "TRACEROUTE_APP": ["route"],
            
            # Detection sensor
            "DETECTION_SENSOR_APP": ["name", "timestamp"],
            
            # Range test
            "RANGE_TEST_APP": ["seq", "timestamp"],
            
            # Store and forward
            "STORE_FORWARD_APP": ["rr", "stats", "history", "heartbeat"],
            
            # Remote hardware
            "REMOTE_HARDWARE_APP": ["type", "gpio_pin", "gpio_value"],
            
            # Paxcounter
            "PAXCOUNTER_APP": ["wifi", "ble"],
        }
        
        # Set default colors for packet types
        # Colors chosen to be visible on both light and dark terminals
        config.colors.packet_type_colors = {
            "POSITION": "green",
            "POSITION_APP": "green",
            "TEXT_MESSAGE_APP": "cyan",
            "TELEMETRY_APP": "yellow",
            "NODEINFO_APP": "blue",
            "ROUTING_APP": "magenta",
            "ADMIN_APP": "red",
            "WAYPOINT_APP": "green_bold",
            "NEIGHBORINFO_APP": "blue_bold",
            "TRACEROUTE_APP": "magenta_bold",
            "DETECTION_SENSOR_APP": "yellow_bold",
            "RANGE_TEST_APP": "cyan_bold",
            "STORE_FORWARD_APP": "white_bold",
            "REMOTE_HARDWARE_APP": "red_bold",
            "PAXCOUNTER_APP": "yellow",
            "default": "white",
        }
        
        # Set default keyword highlights (examples - users can add their own)
        # Using bold colors for better visibility on both light and dark terminals
        config.keywords = [
            KeywordConfig(keyword="emergency", case_sensitive=False, color="red_bold"),
            KeywordConfig(keyword="alert", case_sensitive=False, color="yellow_bold"),
            KeywordConfig(keyword="error", case_sensitive=False, color="red"),
            KeywordConfig(keyword="warning", case_sensitive=False, color="yellow"),
        ]
        
        # Build keyword highlights dict from keywords list
        config.colors.keyword_highlights = {kw.keyword: kw.color for kw in config.keywords}
        
        # Set default encryption keys for common channels
        config.channel_keys = {
            "LongFast": "AQ==",  # Default Meshtastic encryption key
        }
        
        return config

    @staticmethod
    def load_config(file_path: str = DEFAULT_CONFIG_PATH) -> MonitorConfig:
        """
        Load configuration from YAML file.
        
        If the file doesn't exist, creates a default configuration file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            MonitorConfig object with loaded configuration
            
        Raises:
            ValueError: If the configuration file is invalid
        """
        if not os.path.exists(file_path):
            # Create default configuration file
            default_config = ConfigManager.get_default_config()
            ConfigManager._save_config(default_config, file_path)
            print(f"Created default configuration file at {file_path}")
            return default_config
        
        try:
            with open(file_path, "r") as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            return ConfigManager._parse_config(config_data)
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")

    @staticmethod
    def _parse_config(config_data: dict) -> MonitorConfig:
        """Parse configuration dictionary into MonitorConfig object."""
        # Parse MQTT configuration
        mqtt_data = config_data.get("mqtt", {})
        mqtt_config = MQTTConfig(
            host=mqtt_data.get("host", "mqtt.villagesmesh.com"),
            port=mqtt_data.get("port", 1883),
            username=mqtt_data.get("username", "meshdev"),
            password=mqtt_data.get("password", "large4cats"),
            use_tls=mqtt_data.get("use_tls", False),
            ca_cert=mqtt_data.get("ca_cert"),
        )
        
        # Parse monitoring configuration
        monitoring_data = config_data.get("monitoring", {})
        topic = monitoring_data.get("topic", "msh/US/2/e/#")
        channels = monitoring_data.get("channels")
        
        # Parse encryption configuration
        encryption_data = config_data.get("encryption", {})
        channel_configs = encryption_data.get("channels", [])
        channel_keys = {}
        for ch in channel_configs:
            if isinstance(ch, dict) and "name" in ch:
                channel_keys[ch["name"]] = ch.get("key", "")
        
        # Parse display configuration
        display_data = config_data.get("display", {})
        display_fields = display_data.get("fields", {})
        
        # Parse color configuration
        colors_data = config_data.get("colors", {})
        packet_type_colors = colors_data.get("packet_types", {})
        
        # Parse keyword configuration
        keywords_data = colors_data.get("keywords", [])
        keywords = []
        for kw in keywords_data:
            if isinstance(kw, dict) and "keyword" in kw:
                keywords.append(
                    KeywordConfig(
                        keyword=kw["keyword"],
                        case_sensitive=kw.get("case_sensitive", False),
                        color=kw.get("color", "white"),
                    )
                )
        
        # Build keyword highlights dict
        keyword_highlights = {kw.keyword: kw.color for kw in keywords}
        
        color_config = ColorConfig(
            packet_type_colors=packet_type_colors,
            keyword_highlights=keyword_highlights,
        )
        
        # Create and return MonitorConfig
        config = MonitorConfig(
            mqtt=mqtt_config,
            topic=topic,
            channels=channels,
            channel_keys=channel_keys,
            display_fields=display_fields,
            colors=color_config,
            keywords=keywords,
        )
        
        # Apply defaults for missing display fields
        default_config = ConfigManager.get_default_config()
        for packet_type, fields in default_config.display_fields.items():
            if packet_type not in config.display_fields:
                config.display_fields[packet_type] = fields
        
        # Apply defaults for missing colors
        for packet_type, color in default_config.colors.packet_type_colors.items():
            if packet_type not in config.colors.packet_type_colors:
                config.colors.packet_type_colors[packet_type] = color
        
        return config

    @staticmethod
    def _save_config(config: MonitorConfig, file_path: str) -> None:
        """Save configuration to YAML file."""
        config_dict = {
            "version": "1.0",
            "mqtt": {
                "host": config.mqtt.host,
                "port": config.mqtt.port,
                "username": config.mqtt.username,
                "password": config.mqtt.password,
                "use_tls": config.mqtt.use_tls,
                "ca_cert": config.mqtt.ca_cert,
            },
            "monitoring": {
                "topic": config.topic,
                "channels": config.channels,
            },
            "encryption": {
                "channels": [
                    {"name": name, "key": key}
                    for name, key in config.channel_keys.items()
                ]
            },
            "display": {
                "fields": config.display_fields,
            },
            "colors": {
                "packet_types": config.colors.packet_type_colors,
                "keywords": [
                    {
                        "keyword": kw.keyword,
                        "case_sensitive": kw.case_sensitive,
                        "color": kw.color,
                    }
                    for kw in config.keywords
                ],
            },
        }
        
        with open(file_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def validate_config(config: MonitorConfig) -> bool:
        """
        Validate configuration for correctness.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate MQTT configuration
        if not config.mqtt.host:
            raise ValueError("MQTT host cannot be empty")
        
        if config.mqtt.port < 1 or config.mqtt.port > 65535:
            raise ValueError(f"Invalid MQTT port: {config.mqtt.port}")
        
        # Validate topic
        if not config.topic:
            raise ValueError("MQTT topic cannot be empty")
        
        # Validate encryption keys (basic check for base64 format)
        for channel_name, key in config.channel_keys.items():
            if key and not isinstance(key, str):
                raise ValueError(f"Invalid encryption key for channel {channel_name}")
        
        return True

    @staticmethod
    def merge_cli_args(config: MonitorConfig, args: argparse.Namespace) -> MonitorConfig:
        """
        Merge command-line arguments into configuration.
        
        CLI arguments override configuration file values.
        
        Args:
            config: Base configuration from file
            args: Parsed command-line arguments
            
        Returns:
            Updated MonitorConfig with CLI overrides applied
        """
        # Override MQTT settings
        if hasattr(args, "host") and args.host:
            config.mqtt.host = args.host
        if hasattr(args, "port") and args.port:
            config.mqtt.port = args.port
        if hasattr(args, "username") and args.username:
            config.mqtt.username = args.username
        if hasattr(args, "password") and args.password:
            config.mqtt.password = args.password
        if hasattr(args, "use_tls") and args.use_tls:
            config.mqtt.use_tls = args.use_tls
        if hasattr(args, "ca_cert") and args.ca_cert:
            config.mqtt.ca_cert = args.ca_cert
        
        # Override monitoring settings
        if hasattr(args, "topic") and args.topic:
            config.topic = args.topic
        if hasattr(args, "channels") and args.channels:
            config.channels = [ch.strip() for ch in args.channels.split(",")]
        
        # Override color settings for specific packet types
        color_mappings = {
            "color_position": "POSITION",
            "color_text_message_app": "TEXT_MESSAGE_APP",
            "color_telemetry_app": "TELEMETRY_APP",
            "color_nodeinfo_app": "NODEINFO_APP",
            "color_routing_app": "ROUTING_APP",
            "color_admin_app": "ADMIN_APP",
        }
        
        for arg_name, packet_type in color_mappings.items():
            if hasattr(args, arg_name):
                color_value = getattr(args, arg_name)
                if color_value:
                    config.colors.packet_type_colors[packet_type] = color_value
        
        # Handle keyword highlighting from --highlight arguments
        if hasattr(args, "highlight") and args.highlight:
            for highlight_spec in args.highlight:
                # Parse format: keyword:color
                if ":" in highlight_spec:
                    keyword, color = highlight_spec.split(":", 1)
                    keyword = keyword.strip()
                    color = color.strip()
                    
                    # Add to keyword highlights
                    config.colors.keyword_highlights[keyword] = color
                    
                    # Add to keywords list if not already present
                    if not any(kw.keyword == keyword for kw in config.keywords):
                        config.keywords.append(
                            KeywordConfig(keyword=keyword, case_sensitive=False, color=color)
                        )
                    else:
                        # Update existing keyword color
                        for kw in config.keywords:
                            if kw.keyword == keyword:
                                kw.color = color
                                break
        
        # Handle filter options
        if hasattr(args, "filter_type") and args.filter_type:
            config.filter_type = args.filter_type
        if hasattr(args, "filter_text") and args.filter_text:
            config.filter_text = args.filter_text
        
        return config

    @staticmethod
    def create_argument_parser() -> argparse.ArgumentParser:
        """
        Create command-line argument parser with all configuration options.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description="Meshtastic MQTT Monitor - Monitor and decode Meshtastic MQTT traffic",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Use default configuration
  meshtastic-monitor
  
  # Override MQTT connection
  meshtastic-monitor --host mqtt.example.com --port 8883 --use-tls
  
  # Monitor specific topic and channels
  meshtastic-monitor --topic "msh/US/#" --channels "LongFast,Primary"
  
  # Override packet type colors
  meshtastic-monitor --color-position red --color-text-message-app green_bold
  
  # Add keyword highlighting
  meshtastic-monitor --highlight emergency:red_bold --highlight test:cyan
  
  # Filter to only show text messages
  meshtastic-monitor --filter-type TEXT_MESSAGE_APP
  
  # Filter to only show messages containing "weather"
  meshtastic-monitor --filter-text weather
  
  # Combine filters: only position messages containing "checkpoint"
  meshtastic-monitor --filter-type POSITION --filter-text checkpoint
            """,
        )
        
        # Version flag
        parser.add_argument(
            "--version",
            "-v",
            action="version",
            version=f"%(prog)s {__import__('src').__version__}",
            help="Show version information and exit",
        )
        
        # Configuration file
        parser.add_argument(
            "--config",
            "-c",
            type=str,
            default="config.yaml",
            help="Path to configuration file (default: config.yaml)",
        )
        
        # MQTT connection parameters
        mqtt_group = parser.add_argument_group("MQTT Connection")
        mqtt_group.add_argument(
            "--host",
            type=str,
            help="MQTT broker host (overrides config file)",
        )
        mqtt_group.add_argument(
            "--port",
            type=int,
            help="MQTT broker port (overrides config file)",
        )
        mqtt_group.add_argument(
            "--username",
            type=str,
            help="MQTT username (overrides config file)",
        )
        mqtt_group.add_argument(
            "--password",
            type=str,
            help="MQTT password (overrides config file)",
        )
        mqtt_group.add_argument(
            "--use-tls",
            action="store_true",
            help="Enable TLS/SSL for MQTT connection",
        )
        mqtt_group.add_argument(
            "--ca-cert",
            type=str,
            help="Path to CA certificate file for TLS",
        )
        
        # Monitoring parameters
        monitor_group = parser.add_argument_group("Monitoring")
        monitor_group.add_argument(
            "--topic",
            type=str,
            help="MQTT topic to monitor (overrides config file)",
        )
        monitor_group.add_argument(
            "--channels",
            type=str,
            help="Comma-separated list of channels to monitor (overrides config file)",
        )
        
        # Color configuration
        color_group = parser.add_argument_group("Color Configuration")
        color_group.add_argument(
            "--color-position",
            type=str,
            metavar="COLOR",
            help="Color for POSITION packet type (e.g., green, red_bold)",
        )
        color_group.add_argument(
            "--color-text-message-app",
            type=str,
            metavar="COLOR",
            help="Color for TEXT_MESSAGE_APP packet type",
        )
        color_group.add_argument(
            "--color-telemetry-app",
            type=str,
            metavar="COLOR",
            help="Color for TELEMETRY_APP packet type",
        )
        color_group.add_argument(
            "--color-nodeinfo-app",
            type=str,
            metavar="COLOR",
            help="Color for NODEINFO_APP packet type",
        )
        color_group.add_argument(
            "--color-routing-app",
            type=str,
            metavar="COLOR",
            help="Color for ROUTING_APP packet type",
        )
        color_group.add_argument(
            "--color-admin-app",
            type=str,
            metavar="COLOR",
            help="Color for ADMIN_APP packet type",
        )
        
        # Keyword highlighting
        color_group.add_argument(
            "--highlight",
            type=str,
            action="append",
            metavar="KEYWORD:COLOR",
            help="Add keyword highlighting (format: keyword:color, e.g., emergency:red_bold). Can be used multiple times.",
        )
        
        # Filtering options
        filter_group = parser.add_argument_group("Filtering")
        filter_group.add_argument(
            "--filter-type",
            type=str,
            metavar="TYPE",
            help="Only show messages of specific packet type (e.g., TEXT_MESSAGE_APP, POSITION, TELEMETRY_APP)",
        )
        filter_group.add_argument(
            "--filter-text",
            type=str,
            metavar="TEXT",
            help="Only show messages containing specific text (case-insensitive grep-like filter)",
        )
        
        return parser
