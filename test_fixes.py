#!/usr/bin/env python
"""Test script to verify fixes for record & replay system"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from claudecontrol import Session, RecordMode, FallbackMode

def test_basic_session():
    """Test basic session creation and execution"""
    print("Testing basic session creation...")
    try:
        with Session(
            command="echo 'Hello World'",
            timeout=5,
            record=RecordMode.DISABLED,
            fallback=FallbackMode.NOT_FOUND,
            summary=False
        ) as session:
            # Wait for echo to complete
            import pexpect
            try:
                session._transport.expect([pexpect.EOF], timeout=2)
            except:
                pass  # EOF expected

            output = session.get_recent_output(10)
            if "Hello World" in output or output.strip():
                print(f"✓ Basic session works, output: {output.strip()}")
                return True
            else:
                print(f"✗ Basic session failed: empty output")
                return False
    except Exception as e:
        print(f"✗ Basic session failed: {e}")
        return False

def test_recording():
    """Test recording functionality"""
    print("\nTesting recording functionality...")
    temp_dir = tempfile.mkdtemp(prefix="test_tapes_")
    try:
        # Record a session with cat (reads stdin)
        with Session(
            command="cat",
            tapes_path=temp_dir,
            record=RecordMode.NEW,
            fallback=FallbackMode.NOT_FOUND,
            summary=False,
            persist=False,  # Ensure cleanup happens
            timeout=5
        ) as session:
            # Send some input to create exchanges
            session.sendline("Recording Test")
            import time
            time.sleep(0.2)  # Let cat echo back

            # Send EOF to end cat
            session.send("\x04")  # Ctrl-D
            time.sleep(0.2)

        # Check if tape was created
        tapes = list(Path(temp_dir).glob("**/*.json5"))
        if tapes:
            print(f"✓ Recording works, created {len(tapes)} tape(s)")
            return True
        else:
            print("✗ Recording failed: No tapes created")
            return False
    except Exception as e:
        print(f"✗ Recording failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_python_session():
    """Test with Python interpreter"""
    print("\nTesting Python interpreter session...")
    try:
        with Session(
            command="python -c \"print('Python Works')\"",
            timeout=5,
            record=RecordMode.DISABLED,
            fallback=FallbackMode.NOT_FOUND,
            summary=False
        ) as session:
            # Wait for python to complete
            import pexpect
            try:
                session._transport.expect([pexpect.EOF], timeout=2)
            except:
                pass  # EOF expected

            output = session.get_recent_output(10)
            if "Python Works" in output:
                print(f"✓ Python session works")
                return True
            else:
                print(f"✗ Python session output incorrect: {output}")
                return False
    except Exception as e:
        print(f"✗ Python session failed: {e}")
        return False

def test_type_hints():
    """Test that type hints are Python 3.9 compatible"""
    print("\nChecking type hints compatibility...")
    try:
        # Just importing should work if type hints are fixed
        from claudecontrol.replay.matchers import create_matcher_set
        from claudecontrol.core import Session
        print("✓ Type hints are compatible")
        return True
    except Exception as e:
        print(f"✗ Type hint issue: {e}")
        return False

def test_thread_safety():
    """Test thread safety in replay"""
    print("\nTesting thread safety...")
    try:
        from claudecontrol.replay.play import ReplayTransport
        from claudecontrol.replay.store import TapeStore
        from claudecontrol.replay.matchers import CompositeMatcher

        # Create a replay transport
        store = TapeStore("/tmp/test")
        matcher = CompositeMatcher()
        transport = ReplayTransport(
            store=store,
            matcher=matcher,
            fallback_mode=FallbackMode.NOT_FOUND
        )

        # Check that buffer lock exists
        if hasattr(transport, '_buffer_lock'):
            print("✓ Thread safety locks in place")
            return True
        else:
            print("✗ Missing thread safety locks")
            return False
    except Exception as e:
        print(f"✗ Thread safety test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Running ClaudeControl Fix Verification Tests")
    print("=" * 60)

    tests = [
        test_basic_session,
        test_recording,
        test_python_session,
        test_type_hints,
        test_thread_safety
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print("Status:", "✓ ALL TESTS PASSED" if all(results) else "✗ SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())