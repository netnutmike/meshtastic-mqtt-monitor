"""Tests for output formatter."""

import pytest
from datetime import datetime

from src.config import ColorConfig, KeywordConfig
from src.decoder import DecodedMessage
from src.formatter import ANSIColors, OutputFormatter


class TestANSIColors:
    """Tests for ANSI color code utilities."""
    
    def test_get_color_code_valid(self):
        """Test getting valid color codes."""
        assert ANSIColors.get_color_code("red") == "\033[31m"
        assert ANSIColors.get_color_code("green") == "\033[32m"
        assert ANSIColors.get_color_code("blue") == "\033[34m"
    
    def test_get_color_code_bold(self):
        """Test getting bold color codes."""
        assert ANSIColors.get_color_code("red_bold") == "\033[1;31m"
        assert ANSIColors.get_color_code("green_bold") == "\033[1;32m"
    
    def test_get_color_code_case_insensitive(self):
        """Test that color names are case-insensitive."""
        assert ANSIColors.get_color_code("RED") == "\033[31m"
        assert ANSIColors.get_color_code("Green") == "\033[32m"
    
    def test_get_color_code_invalid(self):
        """Test getting invalid color code returns empty string."""
        assert ANSIColors.get_color_code("invalid_color") == ""
        assert ANSIColors.get_color_code("") == ""
    
    def test_apply_color(self):
        """Test applying color to text."""
        result = ANSIColors.apply_color("test", "red")
        assert result == "\033[31mtest\033[0m"
    
    def test_apply_color_invalid(self):
        """Test applying invalid color returns original text."""
        result = ANSIColors.apply_color("test", "invalid")
        assert result == "test"


class TestOutputFormatter:
    """Tests for output formatter."""
    
    @pytest.fixture
    def basic_color_config(self):
        """Create basic color configuration."""
        return ColorConfig(
            packet_type_colors={
                "POSITION": "green",
                "TEXT_MESSAGE_APP": "cyan",
                "TELEMETRY_APP": "yellow",
                "default": "white",
            },
            keyword_highlights={},
        )
    
    @pytest.fixture
    def basic_display_fields(self):
        """Create basic display field configuration."""
        return {
            "POSITION": ["latitude", "longitude", "altitude"],
            "TEXT_MESSAGE_APP": ["text"],
            "TELEMETRY_APP": ["battery_level", "voltage"],
        }
    
    @pytest.fixture
    def formatter(self, basic_color_config, basic_display_fields):
        """Create formatter instance."""
        return OutputFormatter(
            color_config=basic_color_config,
            display_fields=basic_display_fields,
            keywords=[],
        )
    
    def test_format_timestamp(self, formatter):
        """Test timestamp formatting."""
        dt = datetime(2024, 11, 15, 14, 23, 45)
        result = formatter._format_timestamp(dt)
        assert result == "[2024-11-15 14:23:45]"
    
    def test_format_packet_type(self, formatter):
        """Test packet type formatting with color."""
        result = formatter._format_packet_type("POSITION")
        assert "[POSITION]" in result
        assert "\033[32m" in result  # green color code
        assert "\033[0m" in result  # reset code
    
    def test_format_packet_type_default_color(self, formatter):
        """Test packet type with default color."""
        result = formatter._format_packet_type("UNKNOWN")
        assert "[UNKNOWN]" in result
        assert "\033[37m" in result  # white color code (default)
    
    def test_format_field_value_float(self, formatter):
        """Test formatting float values."""
        # Latitude/longitude
        result = formatter._format_field_value("latitude", 37.774929)
        assert result == "37.774929"
        
        # Voltage
        result = formatter._format_field_value("voltage", 3.85)
        assert result == "3.85V"
        
        # Temperature
        result = formatter._format_field_value("temperature", 22.5)
        assert result == "22.5°C"
        
        # Generic float
        result = formatter._format_field_value("value", 123.456)
        assert result == "123.46"
    
    def test_format_field_value_datetime(self, formatter):
        """Test formatting datetime values."""
        dt = datetime(2024, 11, 15, 14, 23, 45)
        result = formatter._format_field_value("time", dt)
        assert result == "14:23:45"
    
    def test_format_field_value_string(self, formatter):
        """Test formatting string values."""
        result = formatter._format_field_value("text", "Hello World")
        assert result == '"Hello World"'
    
    def test_format_field_value_long_string(self, formatter):
        """Test formatting long string values."""
        long_text = "a" * 150
        result = formatter._format_field_value("text", long_text)
        assert result.startswith('"aaa')
        assert result.endswith('..."')
        assert len(result) <= 105  # 100 chars + quotes + ellipsis
    
    def test_format_fields_configured(self, formatter):
        """Test formatting fields with configuration."""
        fields = {
            "latitude": 37.774929,
            "longitude": -122.419416,
            "altitude": 15,
            "extra_field": "should not appear",
        }
        result = formatter._format_fields(fields, "POSITION")
        
        assert "latitude: 37.774929" in result
        assert "longitude: -122.419416" in result
        assert "altitude: 15" in result
        assert "extra_field" not in result
    
    def test_format_fields_no_config(self, formatter):
        """Test formatting fields without configuration shows all fields."""
        fields = {
            "field1": "value1",
            "field2": "value2",
        }
        result = formatter._format_fields(fields, "UNKNOWN_TYPE")
        
        assert "field1: " in result
        assert "field2: " in result
    
    def test_format_message_basic(self, formatter):
        """Test basic message formatting."""
        message = DecodedMessage(
            packet_type="TEXT_MESSAGE_APP",
            channel="LongFast",
            from_node="!a1b2c3d4",
            to_node="broadcast",
            timestamp=datetime(2024, 11, 15, 14, 23, 45),
            fields={"text": "Hello World"},
        )
        
        result = formatter.format_message(message)
        
        assert "[2024-11-15 14:23:45]" in result
        assert "[TEXT_MESSAGE_APP]" in result
        assert "Channel: LongFast" in result
        assert "From: !a1b2c3d4" in result
        assert 'text: "Hello World"' in result
        # Should not include "To: broadcast" for broadcast messages
        assert "To: broadcast" not in result
    
    def test_format_message_with_to_node(self, formatter):
        """Test message formatting with specific to node."""
        message = DecodedMessage(
            packet_type="TEXT_MESSAGE_APP",
            channel="LongFast",
            from_node="!a1b2c3d4",
            to_node="!e5f6g7h8",
            timestamp=datetime(2024, 11, 15, 14, 23, 45),
            fields={"text": "Private message"},
        )
        
        result = formatter.format_message(message)
        
        assert "To: !e5f6g7h8" in result
    
    def test_keyword_highlighting_case_insensitive(self):
        """Test case-insensitive keyword highlighting."""
        color_config = ColorConfig(
            packet_type_colors={"default": "white"},
            keyword_highlights={"emergency": "red_bold"},
        )
        keywords = [
            KeywordConfig(keyword="emergency", case_sensitive=False, color="red_bold")
        ]
        formatter = OutputFormatter(
            color_config=color_config,
            display_fields={},
            keywords=keywords,
        )
        
        text = "This is an EMERGENCY situation"
        result = formatter._apply_keyword_highlighting(text)
        
        assert "\033[1;31m" in result  # red_bold color code
        assert "EMERGENCY" in result
    
    def test_keyword_highlighting_case_sensitive(self):
        """Test case-sensitive keyword highlighting."""
        color_config = ColorConfig(
            packet_type_colors={"default": "white"},
            keyword_highlights={"Alert": "yellow_bold"},
        )
        keywords = [
            KeywordConfig(keyword="Alert", case_sensitive=True, color="yellow_bold")
        ]
        formatter = OutputFormatter(
            color_config=color_config,
            display_fields={},
            keywords=keywords,
        )
        
        text = "Alert: this is an alert message"
        result = formatter._apply_keyword_highlighting(text)
        
        # "Alert" should be highlighted
        assert result.count("\033[1;33m") == 1  # yellow_bold, only once
        
        # Test that case matters
        text2 = "ALERT: this is an alert message"
        result2 = formatter._apply_keyword_highlighting(text2)
        assert "\033[1;33m" not in result2  # Should not highlight "ALERT"
    
    def test_keyword_highlighting_multiple_keywords(self):
        """Test highlighting multiple different keywords."""
        color_config = ColorConfig(
            packet_type_colors={"default": "white"},
            keyword_highlights={"error": "red", "warning": "yellow"},
        )
        keywords = [
            KeywordConfig(keyword="error", case_sensitive=False, color="red"),
            KeywordConfig(keyword="warning", case_sensitive=False, color="yellow"),
        ]
        formatter = OutputFormatter(
            color_config=color_config,
            display_fields={},
            keywords=keywords,
        )
        
        text = "error occurred, warning issued"
        result = formatter._apply_keyword_highlighting(text)
        
        assert "\033[31m" in result  # red for error
        assert "\033[33m" in result  # yellow for warning
    
    def test_keyword_highlighting_no_keywords(self, formatter):
        """Test that highlighting works with no keywords configured."""
        text = "This is a test message"
        result = formatter._apply_keyword_highlighting(text)
        assert result == text  # Should return unchanged
