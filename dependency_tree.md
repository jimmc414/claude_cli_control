# ClaudeControl Dependency Tree

## Overview
ClaudeControl maintains minimal external dependencies while providing powerful functionality including Talkback-style record & replay. The project emphasizes simplicity with smart defaults rather than heavy dependency chains, adding only essential dependencies for the record & replay system.

## Core Dependencies

### Process Control & Automation
- **pexpect** (>=4.8.0)
  - Purpose: Core process spawning and PTY control for CLI interaction
  - Used in: `core.py` (Session class), throughout the codebase
  - Critical: **Yes** - Fundamental to all three capabilities (Discover, Test, Automate)
  - Features enabled:
    - Process spawning with pseudo-terminal (PTY)
    - Pattern matching with expect/send operations
    - Timeout handling for unresponsive processes
    - Process lifecycle management

### System & Process Management
- **psutil** (>=5.9.0)
  - Purpose: Process monitoring, resource usage tracking, and zombie cleanup
  - Used in: `core.py` (cleanup), `testing.py` (resource monitoring)
  - Critical: **Yes** - Required for safe process management and testing
  - Features enabled:
    - CPU and memory usage monitoring
    - Process tree management
    - Zombie process detection and cleanup
    - Resource limit enforcement

### Record & Replay System
- **pyjson5** (>=1.6.9)
  - Purpose: JSON5 format support for human-editable tape files
  - Used in: `replay/store.py`, `replay/record.py`, `replay/play.py`
  - Critical: **Yes** - Required for tape persistence and loading
  - Features enabled:
    - Human-readable tape files with comments
    - Trailing comma support in configurations
    - Relaxed JSON syntax for manual editing
    - Cython-optimized parsing performance

- **portalocker** (>=2.8)
  - Purpose: Cross-platform file locking for concurrent tape access
  - Used in: `replay/store.py` for atomic tape writes
  - Critical: **Yes** - Required for data consistency
  - Features enabled:
    - Atomic tape file writes
    - Prevention of concurrent tape modifications
    - Cross-platform lock compatibility
    - Safe multi-process tape access

- **fastjsonschema** (>=2.20) [Optional]
  - Purpose: Tape format validation and schema checking
  - Used in: `replay/store.py` for tape validation
  - Critical: **No** - Graceful fallback without validation
  - Features enabled:
    - Fast tape schema validation
    - Early detection of malformed tapes
    - CI/CD tape integrity checks
    - Migration assistance for tape format changes

## Standard Library Dependencies

### Essential Python Modules
These are part of Python's standard library but are critical to ClaudeControl's operation:

#### Data & Configuration
- **json** (stdlib)
  - Purpose: Configuration files, report generation, data serialization
  - Used in: All modules for config/report handling
  - Critical: **Yes** - Required for persistence and reporting

- **base64** (stdlib)
  - Purpose: Binary-safe encoding for tape chunks
  - Used in: `replay/record.py`, `replay/play.py`
  - Critical: **Yes** - Required for binary data in tapes

- **pathlib** (stdlib)
  - Purpose: Cross-platform file system operations
  - Used in: Throughout for file/directory management
  - Critical: **Yes** - Required for data storage

#### Process & Threading
- **threading** (stdlib)
  - Purpose: Thread-safe session registry, parallel execution, chunk streaming
  - Used in: `core.py` (registry lock), `claude_helpers.py` (parallel_commands), `replay/play.py` (chunk streaming)
  - Critical: **Yes** - Required for concurrent operations and replay

- **subprocess** (stdlib, indirect)
  - Purpose: Used by pexpect for process spawning
  - Used in: Via pexpect
  - Critical: **Yes** - Core process control

#### Pattern Matching
- **re** (stdlib)
  - Purpose: Regular expression pattern matching, normalization, redaction
  - Used in: `patterns.py`, `replay/normalize.py`, `replay/redact.py`
  - Critical: **Yes** - Required for output analysis and tape matching

#### System Operations
- **os** (stdlib)
  - Purpose: Environment variables, file permissions, system operations
  - Used in: `core.py`, `setup.py`
  - Critical: **Yes** - Required for system integration

- **signal** (stdlib)
  - Purpose: Process signal handling (SIGCHLD, SIGTERM)
  - Used in: `core.py` for process management
  - Critical: **Yes** - Required for proper cleanup

- **fcntl** (stdlib)
  - Purpose: File locking for concurrent access safety
  - Used in: `core.py` for session file locks
  - Critical: **Yes** - Required for data consistency

#### Utilities
- **time** (stdlib)
  - Purpose: Delays, timeouts, timestamps, chunk timing
  - Used in: Throughout for timing operations, `replay/record.py` for chunk timestamps
  - Critical: **Yes** - Required for timeout handling and replay timing

- **hashlib** (stdlib)
  - Purpose: Tape naming, index key generation
  - Used in: `replay/namegen.py`, `replay/store.py`
  - Critical: **Yes** - Required for tape indexing

- **random** (stdlib)
  - Purpose: Error injection, latency simulation
  - Used in: `replay/errors.py`, `replay/latency.py`
  - Critical: **Yes** - Required for probabilistic features

- **enum** (stdlib)
  - Purpose: RecordMode and FallbackMode enumerations
  - Used in: `replay/modes.py`
  - Critical: **Yes** - Required for mode configuration

- **logging** (stdlib)
  - Purpose: Diagnostic output and debugging
  - Used in: All modules for error tracking
  - Critical: **No** - But highly recommended for production

- **dataclasses** (stdlib)
  - Purpose: Structured data models for reports
  - Used in: `investigate.py` for InvestigationReport
  - Critical: **No** - Convenience feature

- **collections** (stdlib)
  - Purpose: deque for output buffering, defaultdict for state tracking
  - Used in: `core.py`, `investigate.py`
  - Critical: **Yes** - Required for efficient buffering

- **contextlib** (stdlib)
  - Purpose: Context managers for resource management
  - Used in: `core.py` for session cleanup
  - Critical: **No** - Convenience feature

- **tempfile** (stdlib)
  - Purpose: Temporary file creation for testing
  - Used in: `testing.py`, `core.py`
  - Critical: **No** - Testing support

- **datetime** (stdlib)
  - Purpose: Timestamps, session timeouts
  - Used in: Throughout for time tracking
  - Critical: **Yes** - Required for session management

- **typing** (stdlib)
  - Purpose: Type hints for better code documentation
  - Used in: All modules
  - Critical: **No** - Development aid only

## Optional Dependencies

### Schema Validation
- **fastjsonschema** (>=2.20)
  - Purpose: Fast JSON schema validation for tapes
  - Used in: `replay/store.py` for tape validation
  - Critical: **No** - Validation skipped if not available
  - Install: `pip install claudecontrol[validate]`
  - Benefits:
    - 10x faster than jsonschema
    - Better error messages
    - Compiled validators

### File Monitoring Enhancement
- **watchdog** (>=2.1.0)
  - Purpose: Efficient file system monitoring for tape hot-reload (future)
  - Used in: Not currently implemented (planned for tape watching)
  - Critical: **No** - Falls back to polling without it
  - Install: `pip install claudecontrol[watch]`

## Development Dependencies

### Testing & Quality
- **pytest** (>=7.0.0)
  - Purpose: Test framework
  - Used in: `tests/*.py`
  - Critical: **No** - Development only
  - Install: `pip install claudecontrol[dev]`

- **pytest-asyncio** (>=0.18.0)
  - Purpose: Async test support
  - Used in: Future async tests
  - Critical: **No** - Development only

- **black** (>=22.0.0)
  - Purpose: Code formatting
  - Used in: Development workflow
  - Critical: **No** - Development only

- **mypy** (>=0.950)
  - Purpose: Static type checking
  - Used in: Development workflow
  - Critical: **No** - Development only

## Version Requirements

### Python Version
- **Python** >=3.9
  - Required for: dataclasses, typing features, pathlib enhancements, dict union operator
  - Tested on: Python 3.9, 3.10, 3.11, 3.12
  - Note: 3.9+ required for type hints used in replay module

### Critical Version Notes
- **pexpect >=4.8.0**: Required for improved Windows support, bug fixes, and logfile_read hook
- **psutil >=5.9.0**: Required for modern process management APIs
- **pyjson5 >=1.6.9**: Required for Cython optimizations and JSON5 spec compliance
- **portalocker >=2.8**: Required for cross-platform file locking
- **Python >=3.9**: Required for modern typing, dict union, and replay features

## Dependency Impact Analysis

### What Happens If Dependencies Are Missing

#### Missing pexpect
- **Impact**: Complete failure - no functionality available
- **Error**: ImportError on module load
- **Mitigation**: None - this is the core dependency

#### Missing psutil
- **Impact**: Degraded functionality
- **Features lost**:
  - Resource monitoring in tests
  - Automatic zombie cleanup
  - Process tree operations
  - Memory/CPU usage tracking
- **Mitigation**: Could theoretically work without it but not recommended

#### Missing pyjson5
- **Impact**: Record & replay completely disabled
- **Features lost**:
  - Cannot read or write tape files
  - No session recording capability
  - No replay functionality
- **Error**: ImportError when replay module loads
- **Mitigation**: None - required for record & replay

#### Missing portalocker
- **Impact**: Unsafe concurrent tape access
- **Features lost**:
  - Atomic tape writes
  - Safe concurrent recording
  - File lock protection
- **Mitigation**: Single-process mode only

#### Missing fastjsonschema (optional)
- **Impact**: No tape validation
- **Features lost**:
  - Schema validation on tape load
  - Early error detection
  - Migration validation
- **Mitigation**: Tapes loaded without validation

#### Missing watchdog (optional)
- **Impact**: Minor performance degradation
- **Features lost**: Efficient file monitoring
- **Mitigation**: Falls back to polling-based monitoring

## Security Considerations

### Dependency Security
- **pexpect**: Handles process I/O - keep updated for security patches
- **psutil**: System access - update regularly for security fixes
- **pyjson5**: Parses external tape files - validate input sources
- **portalocker**: File system access - minimal attack surface
- All dependencies are mature, well-maintained projects with good security track records

### Security Best Practices
- Validate tape sources before loading
- Use redaction features for sensitive data
- Keep pyjson5 updated for parser security
- Restrict tape directory permissions

### Update Schedule
- **Critical updates**: pexpect, psutil, and pyjson5 should be updated quarterly
- **Security updates**: portalocker as needed for security patches
- **Development dependencies**: Update as needed, not security critical
- **Optional dependencies**: Update with feature releases

## Dependency Minimalism Philosophy

ClaudeControl intentionally maintains minimal dependencies because:

1. **Reliability**: Fewer dependencies = fewer breaking changes
2. **Security**: Smaller attack surface
3. **Portability**: Easier to install and deploy
4. **Performance**: Faster installation and startup
5. **Maintenance**: Simpler to debug and maintain

The project philosophy is to:
- Use standard library when possible
- Only add dependencies that provide significant value
- Prefer well-established, stable libraries
- Avoid dependency chains and version conflicts

## Installation Size

### Typical Installation Footprint
```
claudecontrol: ~250 KB (with replay module)
├── pexpect: ~300 KB
│   └── ptyprocess: ~50 KB (transitive)
├── psutil: ~500 KB
├── pyjson5: ~150 KB
└── portalocker: ~40 KB

Total: ~1.29 MB (standard installation with record & replay)
```

### Without Record & Replay
```
claudecontrol (core only): ~200 KB
├── pexpect: ~300 KB
│   └── ptyprocess: ~50 KB (transitive)
└── psutil: ~500 KB

Total: ~1.05 MB (minimal, no record & replay)
```

### With All Optional Dependencies
```
+ fastjsonschema: ~100 KB (validation)
+ watchdog: ~200 KB (future file monitoring)

Total with optional: ~1.59 MB
```

### With Development Dependencies
```
+ pytest: ~2 MB
+ black: ~3 MB
+ mypy: ~15 MB
+ pytest-asyncio: ~100 KB

Total with dev: ~21.59 MB
```

## Record & Replay Dependency Details

### Why pyjson5?
- **Human-editable tapes**: JSON5 allows comments and trailing commas
- **Talkback parity**: Matches Talkback's JSON5 tape format
- **Performance**: Cython-optimized parser (~10x faster than pure Python)
- **Standards compliance**: Full JSON5 spec support
- **Alternative considered**: json5 (pure Python, slower)

### Why portalocker?
- **Cross-platform**: Works on Windows, Linux, macOS
- **Simple API**: Drop-in replacement for fcntl on Windows
- **Atomic operations**: Ensures tape write consistency
- **Lightweight**: Only 40KB overhead
- **Alternative considered**: filelock (heavier, more complex)

### Why fastjsonschema (optional)?
- **Speed**: 10x faster than jsonschema
- **Compilation**: Generates Python code for validation
- **Error messages**: Better error reporting than alternatives
- **Size**: Only 100KB for significant performance gain
- **Alternative considered**: jsonschema (slower, larger)

### Dependencies Not Needed for Record & Replay
These were considered but rejected:
- **aiofiles**: Synchronous I/O sufficient for tapes
- **msgpack**: Binary format loses human editability
- **pickle**: Security concerns, Python-only
- **sqlite**: Overkill for tape storage
- **redis**: Unnecessary complexity for local tapes

## Platform-Specific Notes

### Linux/Unix
- All features fully supported
- Named pipes work natively
- PTY operations are most efficient

### macOS
- All features fully supported
- Some process operations may require permissions
- File system monitoring works best with watchdog

### Windows
- Requires Windows 10+ with WSL or native Python
- pexpect works via ConPTY on Windows 10+
- Some Unix-specific features may have limitations
- Named pipes have different paths (\\\\.\\pipe\\)

### Docker/Containers
- Works well in containers
- May need `--init` flag for proper signal handling
- Consider mounting ~/.claude-control as volume

## Installation Profiles

### Minimal Core (No Record & Replay)
```bash
pip install pexpect>=4.8.0 psutil>=5.9.0
```
- Provides: Basic automation, investigation, testing
- Missing: Record & replay functionality
- Size: ~1.05 MB

### Standard (With Record & Replay)
```bash
pip install claudecontrol
# or
pip install pexpect>=4.8.0 psutil>=5.9.0 pyjson5>=1.6.9 portalocker>=2.8
```
- Provides: Full functionality including record & replay
- Size: ~1.29 MB

### Full (With Optional Features)
```bash
pip install claudecontrol[all]
# or
pip install claudecontrol[validate,watch]
```
- Provides: All features plus validation and future file watching
- Size: ~1.59 MB

### Development
```bash
pip install claudecontrol[dev]
```
- Includes: Testing, formatting, type checking tools
- Size: ~21.59 MB

## Dependency Groups in setup.py

```python
install_requires = [
    'pexpect>=4.8.0',
    'psutil>=5.9.0',
    'pyjson5>=1.6.9',      # Record & replay
    'portalocker>=2.8',     # Record & replay
]

extras_require = {
    'validate': ['fastjsonschema>=2.20'],
    'watch': ['watchdog>=2.1.0'],
    'all': ['fastjsonschema>=2.20', 'watchdog>=2.1.0'],
    'dev': [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.18.0',
        'black>=22.0.0',
        'mypy>=0.950',
    ],
}
```

## Future Dependencies Under Consideration

These are not current dependencies but may be added for specific features:

### Potential Additions
- **rich**: For better terminal UI in interactive mode and tape diffs
- **click**: To replace argparse for CLI if it grows complex
- **asyncio**: For async session management (stdlib)
- **aiofiles**: For async tape operations
- **redis**: For distributed session and tape management
- **fastapi**: If REST API is added
- **watchdog**: For tape hot-reload functionality
- **compression**: For tape compression (gzip/brotli)

### Explicitly Avoided
- **numpy/pandas**: Too heavy for current needs
- **requests**: subprocess and pexpect handle our needs
- **docker**: Would add significant complexity
- **kubernetes**: Out of scope for CLI tool

## Dependency Tree Visualization

```
claudecontrol
├── CORE (must have for basic functionality)
│   ├── pexpect >=4.8.0
│   │   └── ptyprocess (transitive)
│   └── psutil >=5.9.0
│
├── RECORD & REPLAY (required for tape functionality)
│   ├── pyjson5 >=1.6.9
│   └── portalocker >=2.8
│
├── STDLIB (included with Python)
│   ├── Essential
│   │   ├── json
│   │   ├── pathlib
│   │   ├── threading
│   │   ├── re
│   │   ├── os
│   │   ├── signal
│   │   ├── fcntl
│   │   └── base64
│   └── Utilities
│       ├── logging
│       ├── time
│       ├── datetime
│       ├── collections
│       ├── dataclasses
│       ├── hashlib
│       ├── random
│       └── enum
│
└── OPTIONAL
    ├── Runtime
    │   ├── fastjsonschema >=2.20 [tape validation]
    │   └── watchdog >=2.1.0 [future: tape hot-reload]
    └── Development
        ├── pytest >=7.0.0
        ├── pytest-asyncio >=0.18.0
        ├── black >=22.0.0
        └── mypy >=0.950
```

## Conclusion

ClaudeControl maintains a lean dependency footprint with four primary external dependencies (pexpect, psutil, pyjson5, portalocker), relying heavily on Python's robust standard library. The record & replay system adds minimal overhead while providing powerful session recording and deterministic replay capabilities.

This design ensures:

- Easy installation and deployment
- Minimal security surface area
- Excellent stability and compatibility
- Fast startup and low resource usage
- Simple debugging and maintenance
- Powerful record & replay with minimal dependencies

The project can run in three modes:
1. **Minimal**: Just pexpect (very limited functionality)
2. **Core**: pexpect + psutil (full automation without record & replay)
3. **Full**: pexpect + psutil + pyjson5 + portalocker (complete functionality)

For production use, the full installation is recommended to enable all capabilities including the Talkback-style record & replay system.