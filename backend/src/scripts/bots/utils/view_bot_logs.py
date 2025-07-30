#!/usr/bin/env python3
"""
Bot Conversation Log Viewer

This utility script allows viewing and filtering bot conversation logs 
from different sources (database, file logs) with various filtering options.

Example usage:
  # View logs for a specific bot
  python -m scripts.bots.utils.view_bot_logs --bot-id 11111111-1111-1111-1111-111111111111
  
  # Filter by platform and chat ID
  python -m scripts.bots.utils.view_bot_logs --platform telegram --chat-id 12345678
  
  # Show raw JSON logs
  python -m scripts.bots.utils.view_bot_logs --raw
  
  # Filter by log level and event type
  python -m scripts.bots.utils.view_bot_logs --level ERROR --event-type INCOMING
  
  # Time-based filtering
  python -m scripts.bots.utils.view_bot_logs --from-date 2023-07-13 --to-date 2023-07-14
  
  # Content-based filtering
  python -m scripts.bots.utils.view_bot_logs --contains "error"
  
  # Show only the last N logs
  python -m scripts.bots.utils.view_bot_logs --tail 50
"""

import os
import sys
import json
import argparse
import glob
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from uuid import UUID
import re
import colorama
from colorama import Fore, Style
from dataclasses import dataclass
from enum import Enum

# Add project root to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# Import the LogEventType from the conversation logger
try:
    from src.bot_manager.conversation_logger import LogEventType
except ImportError:
    # Fallback definition if unable to import
    class LogEventType(str, Enum):
        INCOMING = "INCOMING"     # Incoming message from user
        PROCESSING = "PROCESSING" # Processing step
        DECISION = "DECISION"     # Decision point
        STATE_CHANGE = "STATE_CHANGE"    # State change
        OUTGOING = "OUTGOING"     # Outgoing message to user
        ERROR = "ERROR"           # Error during processing
        WEBHOOK = "WEBHOOK"       # Webhook event
        VARIABLE = "VARIABLE"     # Variable update
        CONDITION = "CONDITION"   # Condition evaluation
        ADAPTER = "ADAPTER"       # Platform adapter operations
        DIALOG = "DIALOG"         # Dialog operations
        SCENARIO = "SCENARIO"     # Scenario operations
        CACHE = "CACHE"           # Cache operations


@dataclass
class LogEntry:
    """Class for representing a single log entry with standardized fields"""
    timestamp: datetime
    level: str
    event_type: str
    message: str
    context: Dict[str, Any]
    data: Dict[str, Any]
    raw: str  # Original raw log entry
    
    @classmethod
    def from_json(cls, json_str: str) -> "LogEntry":
        """Create a LogEntry from a JSON string"""
        try:
            data = json.loads(json_str)
            # Extract standardized fields
            timestamp_str = data.get("timestamp", "")
            timestamp = parse_timestamp(timestamp_str) if timestamp_str else datetime.now()
            level = data.get("level", "INFO")
            
            # Extract event type
            event_type = data.get("event_type", "UNKNOWN")
            
            # Extract message
            message = data.get("message", "")
            
            # Extract context - bot_id, platform, etc.
            context = {
                "bot_id": data.get("bot_id"),
                "platform": data.get("platform"),
                "platform_chat_id": data.get("platform_chat_id"),
                "dialog_id": data.get("dialog_id"),
                "user_id": data.get("user_id")
            }
            # Remove None values
            context = {k: v for k, v in context.items() if v is not None}
            
            # All other fields go into data
            data_fields = {k: v for k, v in data.items() if k not in [
                "timestamp", "level", "event_type", "message", 
                "bot_id", "platform", "platform_chat_id", "dialog_id", "user_id", "logger"
            ]}
            
            return cls(
                timestamp=timestamp,
                level=level,
                event_type=event_type,
                message=message,
                context=context,
                data=data_fields,
                raw=json_str
            )
        except json.JSONDecodeError:
            # Handle non-JSON lines as plain text
            return cls(
                timestamp=datetime.now(),
                level="INFO",
                event_type="TEXT",
                message=json_str.strip(),
                context={},
                data={},
                raw=json_str
            )


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string into datetime object, handling various formats"""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with milliseconds
        "%Y-%m-%dT%H:%M:%SZ",      # ISO format without milliseconds
        "%Y-%m-%d %H:%M:%S.%f",    # Standard format with milliseconds
        "%Y-%m-%d %H:%M:%S",       # Standard format without milliseconds
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    # If all parsing attempts fail, return current time
    return datetime.now()


def read_logs_from_file(file_path: str) -> List[LogEntry]:
    """Read logs from file and parse into LogEntry objects"""
    log_entries = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                log_entries.append(LogEntry.from_json(line))
                
    except FileNotFoundError:
        print(f"Error: Log file {file_path} not found.")
    except Exception as e:
        print(f"Error reading log file: {str(e)}")
        
    return log_entries


def read_logs_from_directory(directory_path: str) -> List[LogEntry]:
    """Read logs from all log files in a directory"""
    log_entries = []
    log_files = glob.glob(os.path.join(directory_path, "bot_conversations_*.log"))
    
    for file_path in sorted(log_files):
        log_entries.extend(read_logs_from_file(file_path))
        
    return log_entries


def filter_logs(
    logs: List[LogEntry],
    bot_id: Optional[str] = None,
    platform: Optional[str] = None,
    chat_id: Optional[str] = None,
    dialog_id: Optional[str] = None,
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    contains: Optional[str] = None,
) -> List[LogEntry]:
    """Filter logs based on criteria"""
    filtered_logs = []
    
    for log in logs:
        # Skip if bot_id doesn't match
        if bot_id and str(log.context.get("bot_id", "")).lower() != str(bot_id).lower():
            continue
        
        # Skip if platform doesn't match
        if platform and log.context.get("platform", "").lower() != platform.lower():
            continue
        
        # Skip if chat_id doesn't match
        if chat_id and str(log.context.get("platform_chat_id", "")) != str(chat_id):
            continue
        
        # Skip if dialog_id doesn't match
        if dialog_id and str(log.context.get("dialog_id", "")).lower() != str(dialog_id).lower():
            continue
        
        # Skip if level doesn't match
        if level and log.level.upper() != level.upper():
            continue
        
        # Skip if event_type doesn't match
        if event_type and log.event_type.upper() != event_type.upper():
            continue
        
        # Skip if timestamp is before from_date
        if from_date and log.timestamp < from_date:
            continue
        
        # Skip if timestamp is after to_date
        if to_date and log.timestamp > to_date:
            continue
        
        # Skip if doesn't contain the specified string (case-insensitive)
        if contains and contains.lower() not in log.raw.lower() and contains.lower() not in log.message.lower():
            continue
        
        filtered_logs.append(log)
    
    return filtered_logs


def format_log_entry_text(log: LogEntry, show_context: bool = True) -> str:
    """Format a log entry as colorized text"""
    # Initialize colorama
    colorama.init()
    
    # Color mapping for log levels
    level_colors = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }
    
    # Color mapping for event types
    event_colors = {
        "INCOMING": Fore.BLUE,
        "OUTGOING": Fore.MAGENTA,
        "ERROR": Fore.RED,
        "STATE_CHANGE": Fore.YELLOW,
        "PROCESSING": Fore.CYAN,
    }
    
    # Get colors
    level_color = level_colors.get(log.level, Fore.WHITE)
    event_color = event_colors.get(log.event_type, Fore.WHITE)
    
    # Format timestamp
    timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Format context string if requested
    context_str = ""
    if show_context and log.context:
        context_items = []
        for key, value in log.context.items():
            if value:  # Only include non-empty values
                context_items.append(f"{key}={value}")
        
        if context_items:
            context_str = " | " + " ".join(context_items)
    
    # Format main log line
    main_line = f"{Fore.WHITE}{timestamp} | {level_color}{log.level} | {event_color}{log.event_type}{Style.RESET_ALL}{context_str} | {log.message}"
    
    # Format data if present and not empty
    data_lines = []
    if log.data and any(log.data.values()):
        for key, value in log.data.items():
            if value:  # Skip empty values
                if isinstance(value, dict):
                    # Format dictionaries nicely
                    data_lines.append(f"  {key}:")
                    for subkey, subvalue in value.items():
                        data_lines.append(f"    {subkey}: {subvalue}")
                else:
                    data_lines.append(f"  {key}: {value}")
    
    # Combine main line with data lines if any
    if data_lines:
        return main_line + "\n" + "\n".join(data_lines)
    else:
        return main_line


def format_logs(logs: List[LogEntry], raw: bool = False, show_context: bool = True) -> List[str]:
    """Format logs as either raw JSON or human-readable text"""
    if raw:
        return [log.raw for log in logs]
    else:
        return [format_log_entry_text(log, show_context) for log in logs]


def find_latest_log_file(directory_path: str = None) -> Optional[str]:
    """Find the most recent bot conversation log file"""
    if directory_path is None:
        directory_path = os.environ.get("BOT_LOG_DIR", "logs")
        
    log_files = glob.glob(os.path.join(directory_path, "bot_conversations_*.log"))
    
    if not log_files:
        return None
        
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return log_files[0]


def parse_date(date_str: str) -> datetime:
    """Parse date string into datetime object"""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Could not parse date: {date_str}. Use format YYYY-MM-DD.")


def main():
    """Main function to process command-line arguments and display logs"""
    parser = argparse.ArgumentParser(description="View and filter bot conversation logs.")
    
    # Log source arguments
    source_group = parser.add_argument_group("Log Source")
    source_group.add_argument("--source", choices=["file", "all"], default="all",
                       help="Log source (default: all)")
    source_group.add_argument("--file", type=str, help="Specific log file to read")
    source_group.add_argument("--dir", type=str, help="Directory containing log files")
    
    # Filtering arguments
    filter_group = parser.add_argument_group("Filtering")
    filter_group.add_argument("--bot-id", type=str, help="Filter by bot ID")
    filter_group.add_argument("--platform", type=str, help="Filter by platform (e.g., telegram)")
    filter_group.add_argument("--chat-id", type=str, help="Filter by platform chat ID")
    filter_group.add_argument("--dialog-id", type=str, help="Filter by dialog ID")
    filter_group.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Filter by log level")
    filter_group.add_argument("--event-type", type=str, help="Filter by event type")
    filter_group.add_argument("--from-date", type=str, help="Filter from date (YYYY-MM-DD)")
    filter_group.add_argument("--to-date", type=str, help="Filter to date (YYYY-MM-DD)")
    filter_group.add_argument("--contains", type=str, help="Filter logs containing text")
    filter_group.add_argument("--tail", type=int, help="Show only the last N logs")
    
    # Display arguments
    display_group = parser.add_argument_group("Display")
    display_group.add_argument("--raw", action="store_true", help="Show raw JSON logs")
    display_group.add_argument("--no-context", action="store_true", help="Hide context in output")
    display_group.add_argument("--output", type=str, help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    # Parse dates if provided
    from_date = None
    to_date = None
    
    if args.from_date:
        try:
            from_date = parse_date(args.from_date)
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    if args.to_date:
        try:
            to_date = parse_date(args.to_date)
            # Set time to end of day
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    # Collect logs from requested sources
    all_logs = []
    
    if args.source in ("file", "all"):
        log_file = args.file
        
        # If no specific file provided, use the latest one
        if not log_file:
            log_file = find_latest_log_file(args.dir)
            if log_file:
                print(f"Using latest log file: {log_file}")
                
        if log_file:
            all_logs.extend(read_logs_from_file(log_file))
    
    if not args.file and args.source == "all":
        # Read from log directory if no specific file
        log_dir = args.dir or os.environ.get("BOT_LOG_DIR", "logs")
        if os.path.isdir(log_dir):
            all_logs.extend(read_logs_from_directory(log_dir))
    
    if not all_logs:
        print("No log entries found.")
        sys.exit(0)
    
    # Sort logs by timestamp
    all_logs.sort(key=lambda x: x.timestamp)
    
    # Apply filters
    filtered_logs = filter_logs(
        all_logs,
        bot_id=args.bot_id,
        platform=args.platform,
        chat_id=args.chat_id,
        dialog_id=args.dialog_id,
        level=args.level,
        event_type=args.event_type,
        from_date=from_date,
        to_date=to_date,
        contains=args.contains,
    )
    
    # Apply tail if requested
    if args.tail and len(filtered_logs) > args.tail:
        filtered_logs = filtered_logs[-args.tail:]
    
    # Format logs
    formatted_logs = format_logs(filtered_logs, raw=args.raw, show_context=not args.no_context)
    
    # Output logs
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                for log in formatted_logs:
                    f.write(log + "\n")
            print(f"Logs written to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {str(e)}")
    else:
        for log in formatted_logs:
            print(log)
    
    # Summary
    print(f"\n{len(filtered_logs)} log entries displayed out of {len(all_logs)} total entries.")


if __name__ == "__main__":
    main()