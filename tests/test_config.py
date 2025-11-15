"""Unit tests for configuration management."""

import argparse
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import (
    ChannelConfig,
    ColorConfig,
    ConfigManager,
    DisplayFieldConfig,
    KeywordConfig,
    MonitorConfig,
    MQTTConfig,
)


class TestMQTTConfig:
    """Tests for MQTTConfig dataclass."""

    def test_default_values(self):
        """Test that MQTTConfig has correct default values."""
        config = MQTTConfig()
        assert config.host == "mqtt.thevillages.com"
        assert config.port == 1883
        assert config.username == "meshdev"
        assert config.password == "large4cats"
        assert config.use_tls is False
        assert config.ca_cert is None

    def test_custom_values(self):
        """Test MQTTConfig with custom values."""
        config = MQTTConfig(
            host="custom.mqtt.com",
            port=8883,
            username="testuser",
            password="testpass",
            use_tls=True,
            ca_cert="/path/to/cert",
        )
        assert config.host == "custom.mqtt.com"
        assert config.port == 8883
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.use_tls is True
        assert config.ca_cert == "/path/to/cert"


class TestChannelConfig:
    """Tests for ChannelConfig dataclass."""

    def test_channel_with_key(self):
        """Test ChannelConfig with encryption key."""
        config = ChannelConfig(name="LongFast", encryption_key="AQ==")
        assert config.name == "LongFast"
        assert config.encryption_key == "AQ=="

    def test_channel_without_key(self):
        """Test ChannelConfig without encryption key."""
        config = ChannelConfig(name="Public")
        assert config.name == "Public"
        assert config.encryption_key is None


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_get_default_config(self):
        """Test that default configuration is generated correctly."""
        config = ConfigManager.get_default_config()
        
        assert isinstance(config, MonitorConfig)
        assert config.mqtt.host == "mqtt.thevillages.com"
        assert config.mqtt.username == "meshdev"
        assert config.mqtt.password == "large4cats"
        assert config.topic == "msh/US/2/e/#"
        
        # Check default display fields
        assert "POSITION" in config.display_fields
        assert "TEXT_MESSAGE_APP" in config.display_fields
        assert "TELEMETRY_APP" in config.display_fields
        assert "NODEINFO_APP" in config.display_fields
        
        # Check default colors
        assert "POSITION" in config.colors.packet_type_colors
        assert config.colors.packet_type_colors["POSITION"] == "green"

    def test_load_config_creates_default_when_missing(self):
        """Test that load_config creates default file when missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            config = ConfigManager.load_config(config_path)
            
            # Verify config was created
            assert os.path.exists(config_path)
            assert isinstance(config, MonitorConfig)
            assert config.mqtt.host == "mqtt.thevillages.com"

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            # Create a valid config file
            config_data = {
                "mqtt": {
                    "host": "test.mqtt.com",
                    "port": 8883,
                    "username": "testuser",
                    "password": "testpass",
                    "use_tls": True,
                },
                "monitoring": {
                    "topic": "test/topic/#",
                    "channels": ["Channel1", "Channel2"],
                },
                "encryption": {
                    "channels": [
                        {"name": "Channel1", "key": "key1"},
                        {"name": "Channel2", "key": "key2"},
                    ]
                },
                "display": {
                    "fields": {
                        "POSITION": ["latitude", "longitude"],
                    }
                },
                "colors": {
                    "packet_types": {
                        "POSITION": "blue",
                    },
                    "keywords": [
                        {"keyword": "test", "case_sensitive": True, "color": "red"},
                    ],
                },
            }
            
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)
            
            config = ConfigManager.load_config(config_path)
            
            assert config.mqtt.host == "test.mqtt.com"
            assert config.mqtt.port == 8883
            assert config.mqtt.username == "testuser"
            assert config.mqtt.password == "testpass"
            assert config.mqtt.use_tls is True
            assert config.topic == "test/topic/#"
            assert config.channels == ["Channel1", "Channel2"]
            assert config.channel_keys["Channel1"] == "key1"
            assert config.channel_keys["Channel2"] == "key2"
            assert "POSITION" in config.display_fields
            assert config.display_fields["POSITION"] == ["latitude", "longitude"]
            assert config.colors.packet_type_colors["POSITION"] == "blue"
            assert len(config.keywords) == 1
            assert config.keywords[0].keyword == "test"
            assert config.keywords[0].case_sensitive is True
            assert config.keywords[0].color == "red"

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            # Create invalid YAML
            with open(config_path, "w") as f:
                f.write("invalid: yaml: content: [")
            
            with pytest.raises(ValueError, match="Invalid YAML"):
                ConfigManager.load_config(config_path)

    def test_load_config_empty_file(self):
        """Test loading empty YAML file uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            
            # Create empty file
            with open(config_path, "w") as f:
                f.write("")
            
            config = ConfigManager.load_config(config_path)
            
            # Should use defaults
            assert config.mqtt.host == "mqtt.thevillages.com"
            assert config.mqtt.username == "meshdev"
            assert config.mqtt.password == "large4cats"

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = ConfigManager.get_default_config()
        assert ConfigManager.validate_config(config) is True

    def test_validate_config_empty_host(self):
        """Test validation fails with empty host."""
        config = ConfigManager.get_default_config()
        config.mqtt.host = ""
        
        with pytest.raises(ValueError, match="MQTT host cannot be empty"):
            ConfigManager.validate_config(config)

    def test_validate_config_invalid_port(self):
        """Test validation fails with invalid port."""
        config = ConfigManager.get_default_config()
        config.mqtt.port = 0
        
        with pytest.raises(ValueError, match="Invalid MQTT port"):
            ConfigManager.validate_config(config)
        
        config.mqtt.port = 70000
        with pytest.raises(ValueError, match="Invalid MQTT port"):
            ConfigManager.validate_config(config)

    def test_validate_config_empty_topic(self):
        """Test validation fails with empty topic."""
        config = ConfigManager.get_default_config()
        config.topic = ""
        
        with pytest.raises(ValueError, match="MQTT topic cannot be empty"):
            ConfigManager.validate_config(config)

    def test_merge_cli_args_mqtt_overrides(self):
        """Test merging CLI arguments for MQTT settings."""
        config = ConfigManager.get_default_config()
        
        args = argparse.Namespace(
            host="cli.mqtt.com",
            port=8883,
            username="cliuser",
            password="clipass",
            use_tls=True,
        )
        
        merged = ConfigManager.merge_cli_args(config, args)
        
        assert merged.mqtt.host == "cli.mqtt.com"
        assert merged.mqtt.port == 8883
        assert merged.mqtt.username == "cliuser"
        assert merged.mqtt.password == "clipass"
        assert merged.mqtt.use_tls is True

    def test_merge_cli_args_monitoring_overrides(self):
        """Test merging CLI arguments for monitoring settings."""
        config = ConfigManager.get_default_config()
        
        args = argparse.Namespace(
            topic="cli/topic/#",
            channels="Channel1,Channel2,Channel3",
        )
        
        merged = ConfigManager.merge_cli_args(config, args)
        
        assert merged.topic == "cli/topic/#"
        assert merged.channels == ["Channel1", "Channel2", "Channel3"]

    def test_merge_cli_args_no_overrides(self):
        """Test merging with no CLI overrides preserves config."""
        config = ConfigManager.get_default_config()
        original_host = config.mqtt.host
        
        args = argparse.Namespace()
        
        merged = ConfigManager.merge_cli_args(config, args)
        
        assert merged.mqtt.host == original_host

    def test_merge_cli_args_color_overrides(self):
        """Test merging CLI arguments for color settings."""
        config = ConfigManager.get_default_config()
        
        args = argparse.Namespace(
            color_position="red",
            color_text_message_app="blue",
        )
        
        merged = ConfigManager.merge_cli_args(config, args)
        
        assert merged.colors.packet_type_colors["POSITION"] == "red"
        assert merged.colors.packet_type_colors["TEXT_MESSAGE_APP"] == "blue"

    def test_merge_cli_args_keyword_highlights(self):
        """Test merging CLI arguments for keyword highlights."""
        config = ConfigManager.get_default_config()
        
        # Test with new --highlight format (keyword:color)
        args = argparse.Namespace(
            highlight=["emergency:red_bold", "alert:yellow", "test:cyan"],
        )
        
        merged = ConfigManager.merge_cli_args(config, args)
        
        # Check that CLI arguments override defaults
        assert merged.colors.keyword_highlights["emergency"] == "red_bold"
        assert merged.colors.keyword_highlights["alert"] == "yellow"  # Overrides default yellow_bold
        assert merged.colors.keyword_highlights["test"] == "cyan"  # New keyword
        
        # Check that keywords are in the keywords list
        assert any(kw.keyword == "emergency" and kw.color == "red_bold" for kw in merged.keywords)
        assert any(kw.keyword == "alert" and kw.color == "yellow" for kw in merged.keywords)
        assert any(kw.keyword == "test" and kw.color == "cyan" for kw in merged.keywords)

    def test_create_argument_parser(self):
        """Test that argument parser is created with expected arguments."""
        parser = ConfigManager.create_argument_parser()
        
        # Parse empty args to check defaults
        args = parser.parse_args([])
        
        assert hasattr(args, "config")
        assert args.config == "config.yaml"
        
        # Test parsing some arguments
        args = parser.parse_args([
            "--host", "test.com",
            "--port", "8883",
            "--username", "user",
            "--topic", "test/#",
        ])
        
        assert args.host == "test.com"
        assert args.port == 8883
        assert args.username == "user"
        assert args.topic == "test/#"

    def test_create_argument_parser_version(self):
        """Test that version flag is present."""
        parser = ConfigManager.create_argument_parser()
        
        # Version flag should cause SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])
