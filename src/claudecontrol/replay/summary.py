"""
Exit summary reporting for tape usage
Shows new and unused tapes at process exit
"""

from pathlib import Path
from typing import Set, Optional


def print_summary(store: Optional['TapeStore']) -> None:
    """
    Print exit summary showing new and unused tapes.
    Mirrors Talkback's summary output format.
    """
    if not store:
        return

    print("\n===== SUMMARY (claude_control) =====")

    # Show new tapes created in this session
    if store.new:
        print("New tapes:")
        for tape_path in sorted(store.new):
            if isinstance(tape_path, Path):
                print(f"- {tape_path.name}")
            else:
                print(f"- {tape_path}")

    # Show unused tapes (loaded but never matched)
    if hasattr(store, 'paths') and hasattr(store, 'used'):
        unused = set(store.paths) - store.used
        if unused:
            print("Unused tapes:")
            for tape_path in sorted(unused):
                if isinstance(tape_path, Path):
                    print(f"- {tape_path.name}")
                else:
                    print(f"- {tape_path}")

    if not store.new and not (hasattr(store, 'paths') and hasattr(store, 'used')):
        print("No tape activity in this session")

    print("=" * 37)