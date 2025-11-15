"""Output formatter for Meshtastic MQTT Monitor."""

import re
from datetime import datetime
from typing import Dict, List, Optional

from src.config import ColorConfig, KeywordConfig
from src.decoder import DecodedMessage


class ANSIColors:
    """ANSI color code constants for terminal output."""
    
    # Reset
    RESET = "\033[0m"
    
    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bold colors
    BLACK_BOLD = "\033[1;30m"
    RED_BOLD = "\033[1;31m"
    GREEN_BOLD = "\033[1;32m"
    YELLOW_BOLD = "\033[1;33m"
    BLUE_BOLD = "\033[1;34m"
    MAGENTA_BOLD = "\033[1;35m"
    CYAN_BOLD = "\033[1;36m"
    WHITE_BOLD = "\033[1;37m"
    
    # Color name mapping
    COLOR_MAP = {
        "black": BLACK,
        "red": RED,
        "green": GREEN,
        "yellow": YELLOW,
        "blue": BLUE,
        "magenta": MAGENTA,
        "cyan": CYAN,
        "white": WHITE,
        "black_bold": BLACK_BOLD,
        "red_bold": RED_BOLD,
        "green_bold": GREEN_BOLD,
        "yellow_bold": YELLOW_BOLD,
        "blue_bold": BLUE_BOLD,
        "magenta_bold": MAGENTA_BOLD,
        "cyan_bold": CYAN_BOLD,
        "white_bold": WHITE_BOLD,
    }
    
    @staticmethod
    def get_color_code(color_name: str) -> str:
        """
        Get ANSI color code from color name.
        
        Args:
            color_name: Color name (e.g., "red", "green_bold")
            
        Returns:
            ANSI color code string, or empty string if not found
        """
        return ANSIColors.COLOR_MAP.get(color_name.lower(), "")
    
    @staticmethod
    def apply_color(text: str, color_name: str) -> str:
        """
        Apply color to text.
        
        Args:
            text: Text to colorize
            color_name: Color name to apply
            
        Returns:
            Colorized text with ANSI codes
        """
        color_code = ANSIColors.get_color_code(color_name)
        if color_code:
            return f"{color_code}{text}{ANSIColors.RESET}"
        return text



class OutputFormatter:
    """
    Formats decoded Meshtastic messages for console output.
    
    Applies color coding, keyword highlighting, and consistent formatting
    to make messages easy to read and analyze.
    """
    
    def __init__(
        self,
        color_config: ColorConfig,
        display_fields: Dict[str, List[str]],
        keywords: List[KeywordConfig],
    ):
        """
        Initialize output formatter.
        
        Args:
            color_config: Color configuration for packet types and keywords
            display_fields: Field display configuration per packet type
            keywords: Keyword highlighting configuration
        """
        self.color_config = color_config
        self.display_fields = display_fields
        self.keywords = keywords
    
    def format_message(self, message: DecodedMessage) -> str:
        """
        Format a decoded message for display.
        
        Args:
            message: Decoded message to format
            
        Returns:
            Formatted string ready for console output
        """
        # Format timestamp
        timestamp_str = self._format_timestamp(message.timestamp)
        
        # Format packet type with color
        packet_type_str = self._format_packet_type(message.packet_type)
        
        # Format basic info
        channel_str = f"Channel: {message.channel}"
        from_str = f"From: {message.from_node}"
        to_str = f"To: {message.to_node}"
        
        # Format fields based on packet type
        fields_str = self._format_fields(message.fields, message.packet_type)
        
        # Build output line
        parts = [timestamp_str, packet_type_str, channel_str, from_str]
        
        # Only add "To" if it's not broadcast
        if message.to_node != "broadcast":
            parts.append(to_str)
        
        # Add fields if present
        if fields_str:
            parts.append(fields_str)
        
        output = " | ".join(parts)
        
        # Apply keyword highlighting (this should be done last)
        output = self._apply_keyword_highlighting(output)
        
        return output
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """
        Format timestamp consistently.
        
        Args:
            timestamp: Datetime object to format
            
        Returns:
            Formatted timestamp string
        """
        return f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}]"
    
    def _format_packet_type(self, packet_type: str) -> str:
        """
        Format packet type indicator with color.
        
        Args:
            packet_type: Packet type string
            
        Returns:
            Colored packet type string
        """
        # Get color for this packet type
        color = self.color_config.packet_type_colors.get(
            packet_type,
            self.color_config.packet_type_colors.get("default", "white")
        )
        
        # Apply color
        colored_type = ANSIColors.apply_color(f"[{packet_type}]", color)
        
        return colored_type
    
    def _format_fields(self, fields: Dict[str, any], packet_type: str) -> str:
        """
        Format message fields based on display configuration.
        
        Args:
            fields: Dictionary of field names to values
            packet_type: Type of packet (determines which fields to display)
            
        Returns:
            Formatted fields string
        """
        if not fields:
            return ""
        
        # Get configured fields for this packet type
        configured_fields = self.display_fields.get(packet_type, [])
        
        # If no configuration, display all fields
        if not configured_fields:
            configured_fields = list(fields.keys())
        
        # Format each configured field that exists in the message
        formatted_parts = []
        for field_name in configured_fields:
            if field_name in fields:
                value = fields[field_name]
                formatted_value = self._format_field_value(field_name, value)
                formatted_parts.append(f"{field_name}: {formatted_value}")
        
        return " | ".join(formatted_parts)
    
    def _format_field_value(self, field_name: str, value: any) -> str:
        """
        Format a single field value.
        
        Args:
            field_name: Name of the field
            value: Value to format
            
        Returns:
            Formatted value string
        """
        # Handle different value types
        if isinstance(value, float):
            # Format floats with reasonable precision
            if "latitude" in field_name.lower() or "longitude" in field_name.lower():
                return f"{value:.6f}"
            elif "voltage" in field_name.lower():
                return f"{value:.2f}V"
            elif "temperature" in field_name.lower():
                return f"{value:.1f}°C"
            else:
                return f"{value:.2f}"
        elif isinstance(value, datetime):
            # Format datetime values
            return value.strftime('%H:%M:%S')
        elif isinstance(value, str):
            # Strings - truncate if too long
            if len(value) > 100:
                return f'"{value[:97]}..."'
            return f'"{value}"'
        else:
            # Default string conversion
            return str(value)

    
    def _apply_keyword_highlighting(self, text: str) -> str:
        """
        Apply keyword highlighting to text.
        
        Searches for configured keywords and applies color highlighting.
        Supports both case-sensitive and case-insensitive matching.
        
        Args:
            text: Text to apply highlighting to
            
        Returns:
            Text with keyword highlighting applied
        """
        if not self.keywords:
            return text
        
        # Process each keyword
        for keyword_config in self.keywords:
            keyword = keyword_config.keyword
            color = keyword_config.color
            case_sensitive = keyword_config.case_sensitive
            
            # Create regex pattern
            if case_sensitive:
                pattern = re.compile(re.escape(keyword))
            else:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            # Find all matches
            matches = list(pattern.finditer(text))
            
            # Apply highlighting in reverse order to preserve positions
            for match in reversed(matches):
                start, end = match.span()
                matched_text = text[start:end]
                highlighted_text = ANSIColors.apply_color(matched_text, color)
                text = text[:start] + highlighted_text + text[end:]
        
        return text
