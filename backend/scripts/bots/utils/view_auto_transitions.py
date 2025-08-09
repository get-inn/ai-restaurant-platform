#!/usr/bin/env python
"""
Utility for viewing and analyzing auto-transition chains in bot conversations.

This tool extracts and displays auto-transition information from conversation logs,
allowing easy visualization and debugging of auto-transition chains.

Usage examples:
- Show all auto-transition chains:
  python -m scripts.bots.utils.view_auto_transitions

- Show auto-transitions for a specific bot:
  python -m scripts.bots.utils.view_auto_transitions --bot-id BOT_ID

- Show auto-transitions for a specific platform chat:
  python -m scripts.bots.utils.view_auto_transitions --platform telegram --chat-id CHAT_ID

- Show auto-transitions from a specific log file:
  python -m scripts.bots.utils.view_auto_transitions --file logs/bot_conversations_20250809.log

- Show only auto-transition chains that had errors:
  python -m scripts.bots.utils.view_auto_transitions --with-errors

- Show detailed timing information:
  python -m scripts.bots.utils.view_auto_transitions --timing
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set
import colorama
from colorama import Fore, Back, Style


def setup_args():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(
        description="View and analyze auto-transition chains in bot conversations"
    )
    parser.add_argument(
        "--bot-id", 
        help="Filter by bot ID"
    )
    parser.add_argument(
        "--platform", 
        help="Filter by platform (e.g., telegram, whatsapp)"
    )
    parser.add_argument(
        "--chat-id", 
        help="Filter by chat ID"
    )
    parser.add_argument(
        "--dialog-id", 
        help="Filter by dialog ID"
    )
    parser.add_argument(
        "--transition-id", 
        help="Filter by a specific transition ID"
    )
    parser.add_argument(
        "--from-date", 
        help="Filter from date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to-date", 
        help="Filter to date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--file", 
        help="Path to log file (defaults to latest in logs directory)"
    )
    parser.add_argument(
        "--with-errors", 
        action="store_true",
        help="Show only auto-transition chains with errors"
    )
    parser.add_argument(
        "--timing", 
        action="store_true",
        help="Show detailed timing information"
    )
    parser.add_argument(
        "--raw", 
        action="store_true",
        help="Show raw log entries"
    )
    return parser.parse_args()


def find_log_file(args):
    """Find the log file to use"""
    if args.file:
        return args.file
        
    # Find the latest log file in the logs directory
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
        
    if not os.path.exists(logs_dir):
        print("Could not find logs directory")
        sys.exit(1)
        
    log_files = [f for f in os.listdir(logs_dir) if f.startswith("bot_conversations_") and f.endswith(".log")]
    if not log_files:
        print("No log files found")
        sys.exit(1)
        
    log_files.sort(reverse=True)
    return os.path.join(logs_dir, log_files[0])


def parse_log_file(file_path, args):
    """Parse the log file and return relevant entries"""
    entries = []
    
    date_filters = []
    if args.from_date:
        date_filters.append(
            lambda dt: dt.date() >= datetime.strptime(args.from_date, "%Y-%m-%d").date()
        )
    if args.to_date:
        date_filters.append(
            lambda dt: dt.date() <= datetime.strptime(args.to_date, "%Y-%m-%d").date()
        )
    
    with open(file_path, "r") as f:
        for line in f:
            try:
                # Skip lines that don't look like JSON
                if not line.strip().startswith("{"):
                    continue
                    
                entry = json.loads(line.strip())
                
                # Check for event type AUTO_TRANSITION
                if entry.get("event_type") != "AUTO_TRANSITION":
                    continue
                    
                # Apply context filters
                context = entry.get("context", {})
                if args.bot_id and context.get("bot_id") != args.bot_id:
                    continue
                if args.platform and context.get("platform") != args.platform:
                    continue
                if args.chat_id and context.get("platform_chat_id") != args.chat_id:
                    continue
                if args.dialog_id and context.get("dialog_id") != args.dialog_id:
                    continue
                    
                # Apply transition ID filter
                data = entry.get("data", {})
                if args.transition_id and data.get("transition_id") != args.transition_id:
                    continue
                    
                # Apply date filters
                timestamp = entry.get("timestamp")
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if not all(f(dt) for f in date_filters):
                        continue
                
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue
    
    return entries


def group_entries_by_transition_chain(entries):
    """Group entries by transition chain"""
    chains = defaultdict(list)
    for entry in entries:
        data = entry.get("data", {})
        transition_id = data.get("transition_id")
        if transition_id:
            chains[transition_id].append(entry)
    
    # Sort entries in each chain by timestamp
    for chain_id in chains:
        chains[chain_id].sort(key=lambda e: e.get("timestamp", ""))
        
    return chains


def get_chain_summary(chain_entries):
    """Get a summary of a transition chain"""
    if not chain_entries:
        return None
        
    first_entry = chain_entries[0]
    last_entry = chain_entries[-1]
    
    # Get start time from the first entry
    start_time = datetime.fromisoformat(first_entry.get("timestamp", "").replace("Z", "+00:00"))
    
    # Get end time from the last entry
    end_time = datetime.fromisoformat(last_entry.get("timestamp", "").replace("Z", "+00:00"))
    
    # Calculate duration
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    # Count steps
    start_entries = [e for e in chain_entries if "Starting auto-transition" in e.get("message", "")]
    complete_entries = [e for e in chain_entries if "Auto-transition completed" in e.get("message", "")]
    error_entries = [e for e in chain_entries if e.get("level") == "ERROR"]
    
    # Get step sequence
    steps = []
    current_step = None
    next_step = None
    
    for entry in chain_entries:
        data = entry.get("data", {})
        message = entry.get("message", "")
        
        if "Starting auto-transition" in message:
            next_step = data.get("next_step")
        elif "Auto-transition completed" in message:
            current_step = data.get("step_id")
            next_step = data.get("next_step")
            execution_time = data.get("execution_time_ms", 0)
            
            if current_step and next_step:
                steps.append({
                    "from": current_step,
                    "to": next_step,
                    "execution_time": execution_time
                })
    
    # Get context information from the first entry
    context = first_entry.get("context", {})
    
    return {
        "transition_id": first_entry.get("data", {}).get("transition_id"),
        "bot_id": context.get("bot_id"),
        "platform": context.get("platform"),
        "platform_chat_id": context.get("platform_chat_id"),
        "dialog_id": context.get("dialog_id"),
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": duration_ms,
        "step_count": len(steps),
        "steps": steps,
        "has_errors": bool(error_entries),
        "errors": [e.get("message") for e in error_entries]
    }


def print_chain_summaries(chain_summaries, args):
    """Print chain summaries in a readable format"""
    colorama.init()
    
    # Count total chains and chains with errors
    total_chains = len(chain_summaries)
    error_chains = len([c for c in chain_summaries if c["has_errors"]])
    
    print(f"\n{Style.BRIGHT}Auto-Transition Chain Summary{Style.RESET_ALL}")
    print(f"Total chains: {total_chains}")
    if error_chains:
        print(f"Chains with errors: {Fore.RED}{error_chains}{Style.RESET_ALL}")
    print()
    
    for i, summary in enumerate(chain_summaries):
        # Skip chains without errors if --with-errors is specified
        if args.with_errors and not summary["has_errors"]:
            continue
            
        # Print chain header
        transition_id = summary["transition_id"]
        start_time = summary["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        duration = f"{summary['duration_ms']:.1f}ms"
        step_count = summary["step_count"]
        
        # Color based on errors
        header_color = Fore.RED if summary["has_errors"] else Fore.GREEN
        print(f"{header_color}{Style.BRIGHT}Chain {i+1}: {transition_id}{Style.RESET_ALL}")
        print(f"  Start time: {start_time}")
        print(f"  Duration: {duration}")
        print(f"  Steps: {step_count}")
        print(f"  Bot ID: {summary['bot_id']}")
        print(f"  Platform: {summary['platform']}")
        print(f"  Chat ID: {summary['platform_chat_id']}")
        
        # Print steps
        print(f"\n  {Style.BRIGHT}Step Sequence:{Style.RESET_ALL}")
        for j, step in enumerate(summary["steps"]):
            delay = 1.5  # Default delay
            from_step = step["from"]
            to_step = step["to"]
            execution_time = f"{step['execution_time']:.1f}ms" if step['execution_time'] else "N/A"
            
            if args.timing:
                print(f"    {j+1}. {from_step} → {to_step} (execution: {execution_time})")
            else:
                print(f"    {j+1}. {from_step} → {to_step}")
        
        # Print errors if any
        if summary["has_errors"]:
            print(f"\n  {Fore.RED}{Style.BRIGHT}Errors:{Style.RESET_ALL}")
            for error in summary["errors"]:
                print(f"    {Fore.RED}• {error}{Style.RESET_ALL}")
        
        print("\n" + "-" * 50 + "\n")


def print_raw_entries(entries):
    """Print raw log entries"""
    for entry in entries:
        print(json.dumps(entry, indent=2))
        print("-" * 50)


def main():
    args = setup_args()
    log_file = find_log_file(args)
    
    print(f"Reading log file: {log_file}")
    entries = parse_log_file(log_file, args)
    
    if not entries:
        print("No auto-transition logs found matching criteria")
        return
        
    print(f"Found {len(entries)} auto-transition log entries")
    
    if args.raw:
        print_raw_entries(entries)
        return
        
    chains = group_entries_by_transition_chain(entries)
    print(f"Found {len(chains)} auto-transition chains")
    
    chain_summaries = []
    for chain_id, chain_entries in chains.items():
        summary = get_chain_summary(chain_entries)
        if summary:
            chain_summaries.append(summary)
    
    # Sort chain summaries by start time
    chain_summaries.sort(key=lambda s: s["start_time"])
    
    print_chain_summaries(chain_summaries, args)


if __name__ == "__main__":
    main()