# ClaudeControl API & Interface Documentation

## Core Session Interface

### Session Class
**Purpose:** Primary interface for controlling CLI processes
**Location:** `src/claudecontrol/core.py`

#### `__init__(command: str, timeout: int = 30, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None, encoding: str = "utf-8", dimensions: tuple = (24, 80), session_id: Optional[str] = None, persist: bool = True, stream: bool = False, tapes_path: str = "./tapes", record: RecordMode = RecordMode.DISABLED, fallback: FallbackMode = FallbackMode.NOT_FOUND, tape_name_generator: Optional[Callable] = None, allow_env: Optional[List[str]] = None, ignore_env: Optional[List[str]] = None, ignore_args: Optional[List[Union[int, str]]] = None, ignore_stdin: bool = False, stdin_matcher: Optional[Callable] = None, command_matcher: Optional[Callable] = None, input_decorator: Optional[Callable] = None, output_decorator: Optional[Callable] = None, tape_decorator: Optional[Callable] = None, latency: Union[int, Tuple[int, int], Callable] = 0, error_rate: Union[int, Callable] = 0, summary: bool = True, silent: bool = False, debug: bool = False)`
**Purpose:** Create a new session to control a CLI process with optional record/replay
**Parameters:**
- `command`: Command to execute (required)
- `timeout`: Default timeout for operations in seconds (default: 30)
- `cwd`: Working directory for the process
- `env`: Environment variables dict
- `encoding`: Character encoding (default: utf-8)
- `dimensions`: Terminal dimensions (rows, cols)
- `session_id`: Explicit session ID (auto-generated if None)
- `persist`: Keep session in global registry for reuse
- `stream`: Enable named pipe streaming
- `tapes_path`: Directory for tape storage (default: "./tapes")
- `record`: Recording mode (NEW, OVERWRITE, DISABLED)
- `fallback`: Fallback mode when tape not found (NOT_FOUND, PROXY)
- `tape_name_generator`: Custom tape naming function
- `allow_env`: Environment variables to include in matching
- `ignore_env`: Environment variables to ignore in matching
- `ignore_args`: Argument positions or values to ignore
- `ignore_stdin`: Ignore stdin in matching
- `stdin_matcher`: Custom stdin matching function
- `command_matcher`: Custom command matching function
- `input_decorator`: Transform input before recording
- `output_decorator`: Transform output before recording
- `tape_decorator`: Transform tape before saving
- `latency`: Replay latency (ms, range, or function)
- `error_rate`: Error injection rate (0-100)
- `summary`: Print tape usage summary on exit
- `silent`: Suppress mid-operation logs
- `debug`: Enable debug logging

**Returns:** Session instance
**Raises:**
- `ProcessError` if command cannot be spawned
- `TapeMissError` if tape not found and fallback=NOT_FOUND
**Side Effects:**
- Spawns external process (unless replaying)
- Creates session directory in `~/.claude-control/sessions/`
- Registers in global session registry if persist=True
- Creates named pipe if stream=True
- Records to tape file if record mode enabled
- Loads tapes on startup if replay mode enabled

#### `expect(patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int`
**Purpose:** Wait for output patterns
**Parameters:**
- `patterns`: String or list of regex patterns to match
- `timeout`: Override default timeout

**Returns:** Index of matched pattern
**Raises:** 
- `TimeoutError` with recent output if pattern not found
- `ProcessError` if process dies unexpectedly
**Side Effects:** Updates last_activity timestamp

#### `send(text: str, delay: float = 0) -> None`
**Purpose:** Send input to the process
**Parameters:**
- `text`: Text to send
- `delay`: Delay between characters (for slow typing simulation)

**Raises:** `SessionError` if session is not alive
**Side Effects:** Writes to process stdin, updates activity timestamp

#### `sendline(line: str = "") -> None`
**Purpose:** Send a line with newline
**Parameters:**
- `line`: Text to send (newline automatically appended)

#### `get_recent_output(lines: int = 100) -> str`
**Purpose:** Get recent output from buffer
**Returns:** String containing last N lines

#### `get_full_output() -> str`
**Purpose:** Get all captured output
**Returns:** Complete output since session start

#### `is_alive() -> bool`
**Purpose:** Check if process is running
**Returns:** True if process is alive

#### `close(force: bool = False) -> Optional[int]`
**Purpose:** Close the session
**Parameters:**
- `force`: Force terminate if process won't exit cleanly

**Returns:** Exit status code
**Side Effects:** 
- Terminates process
- Removes from global registry
- Cleans up named pipe if exists

---

## High-Level Helper Functions

### `control(command: str, timeout: int = 30, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None, session_id: Optional[str] = None, reuse: bool = True, with_config: Optional[str] = None, stream: bool = False) -> Session`
**Purpose:** Get or create a controlled session with reuse support
**Location:** `src/claudecontrol/core.py`

**Parameters:**
- `command`: Command to execute
- `timeout`: Default timeout
- `cwd`: Working directory
- `env`: Environment variables
- `session_id`: Explicit session ID
- `reuse`: Reuse existing session with same command if available
- `with_config`: Load from saved configuration
- `stream`: Enable streaming via named pipe

**Returns:** Session instance (new or existing)
**Side Effects:** May reuse existing session from registry

### `run(command: str, expect: Optional[Union[str, List[str]]] = None, send: Optional[str] = None, timeout: int = 30, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> str`
**Purpose:** One-liner to run a command and get output
**Location:** `src/claudecontrol/core.py`

**Returns:** Captured output as string
**Raises:** `TimeoutError` if command doesn't complete
**Side Effects:** Process is spawned and terminated

---

## Investigation Interface

### `investigate_program(program: str, timeout: int = 10, safe_mode: bool = True, save_report: bool = True) -> InvestigationReport`
**Purpose:** Automatically investigate an unknown CLI program
**Location:** `src/claudecontrol/investigate.py`

**Parameters:**
- `program`: Program command to investigate
- `timeout`: Timeout for each probe operation
- `safe_mode`: Block potentially dangerous commands
- `save_report`: Save JSON report to disk

**Returns:** `InvestigationReport` object with findings
**Side Effects:**
- Spawns and interacts with target program
- Saves report to `~/.claude-control/investigations/` if save_report=True

### InvestigationReport Structure
```python
{
    "program": "string",
    "started_at": "datetime",
    "completed_at": "datetime",
    "states": {
        "state_name": {
            "name": "string",
            "prompt": "string",
            "commands": ["list"],
            "transitions": {"command": "next_state"}
        }
    },
    "commands": {
        "command": {
            "description": "string",
            "tested": true,
            "output_length": 123
        }
    },
    "prompts": ["detected", "prompts"],
    "help_commands": ["help", "?"],
    "exit_commands": ["quit", "exit"],
    "data_formats": ["JSON", "CSV"],
    "safety_notes": ["warnings"]
}
```

---

## Testing Interface

### `black_box_test(program: str, timeout: int = 10, save_report: bool = True) -> Dict[str, Any]`
**Purpose:** Run comprehensive black-box tests on a CLI program
**Location:** `src/claudecontrol/testing.py`

**Parameters:**
- `program`: Program to test
- `timeout`: Timeout for each test
- `save_report`: Save test report to disk

**Returns:**
```python
{
    "program": "string",
    "results": [
        {
            "test": "startup|help|invalid_input|exit|resource|concurrent|fuzz",
            "passed": true,
            "details": {},
            "error": "string if failed"
        }
    ],
    "report": "Human-readable report string",
    "report_path": "/path/to/saved/report.json"
}
```

**Side Effects:**
- Spawns multiple instances of target program
- Creates various test inputs including fuzz data
- Monitors resource usage
- Saves report to `~/.claude-control/test-reports/`

---

## Record & Replay Interface

### Recording Modes (Enums)
**Location:** `src/claudecontrol/replay/modes.py`

#### `RecordMode`
```python
RecordMode.NEW       # Record only if no existing tape matches
RecordMode.OVERWRITE # Always record, replacing existing tapes
RecordMode.DISABLED  # Never record (replay only)
```

#### `FallbackMode`
```python
FallbackMode.NOT_FOUND # Raise TapeMissError if no tape matches
FallbackMode.PROXY     # Run the real program if no tape matches
```

### TapeStore Class
**Purpose:** Manage tape storage and indexing
**Location:** `src/claudecontrol/replay/store.py`

#### `__init__(root: Path)`
**Purpose:** Initialize tape store with root directory
**Parameters:**
- `root`: Root directory for tape storage

#### `load_all() -> None`
**Purpose:** Load all tapes from disk
**Side Effects:**
- Reads all .json5 files recursively
- Builds index for fast matching
- Validates tape schemas

#### `mark_used(path: Path) -> None`
**Purpose:** Mark a tape as used (for summary)

#### `mark_new(path: Path) -> None`
**Purpose:** Mark a tape as newly created

#### `build_index(normalizer) -> Dict[tuple, Tuple[int, int]]`
**Purpose:** Build normalized key index for fast matching
**Returns:** Dict mapping normalized keys to (tape_idx, exchange_idx)

### Recorder Class
**Purpose:** Record CLI sessions to tapes
**Location:** `src/claudecontrol/replay/record.py`

#### `__init__(session: Session, tapes_path: Path, mode: RecordMode, namegen: TapeNameGenerator)`
**Purpose:** Initialize recorder for a session

#### `start() -> None`
**Purpose:** Attach recording to session
**Side Effects:** Installs ChunkSink as pexpect logfile_read

#### `on_send(data: bytes, kind: str, ctx, pre_prompt: str) -> None`
**Purpose:** Record input sent to process

#### `on_exchange_end(exit_info: Optional[Dict] = None) -> None`
**Purpose:** Finalize and save exchange to tape

### ReplayTransport Class
**Purpose:** Replay recorded tapes instead of running process
**Location:** `src/claudecontrol/replay/play.py`

#### `send(b: bytes) -> int`
**Purpose:** Match input and stream recorded output
**Returns:** Number of bytes "sent"
**Raises:** `TapeMissError` if no matching tape

#### `expect(pattern, timeout=None)`
**Purpose:** Wait for pattern in replayed output
**Returns:** Match index (0 on success)
**Raises:** `TimeoutError` if pattern not found

### Tape Data Model
**Location:** `src/claudecontrol/replay/model.py`

#### Tape Structure
```python
@dataclass
class Tape:
    meta: TapeMeta        # Metadata about recording
    session: Dict         # Session information
    exchanges: List[Exchange]  # Recorded interactions

@dataclass
class Exchange:
    pre: Dict            # Pre-state (prompt, etc)
    input: IOInput       # Input sent
    output: IOOutput     # Output received (chunked)
    exit: Optional[Dict] # Exit status if process ended
    dur_ms: int         # Duration in milliseconds

@dataclass
class Chunk:
    delay_ms: int       # Delay before this chunk
    data_b64: str       # Base64 encoded data
    is_utf8: bool       # UTF-8 decodable flag
```

### Matchers
**Purpose:** Custom matching for dynamic values
**Location:** `src/claudecontrol/replay/matchers.py`

#### `CommandMatcher`
**Signature:** `(actual_args: List[str], expected_args: List[str], ctx: MatchingContext) -> bool`

#### `StdinMatcher`
**Signature:** `(actual: bytes, expected: bytes, ctx: MatchingContext) -> bool`

#### `MatchingContext`
```python
@dataclass
class MatchingContext:
    program: str
    args: List[str]
    env: Dict[str, str]
    cwd: str
    prompt: str
```

### Decorators
**Purpose:** Transform data during record/replay
**Location:** `src/claudecontrol/replay/decorators.py`

#### `InputDecorator`
**Signature:** `(ctx: MatchingContext, data: bytes) -> bytes`

#### `OutputDecorator`
**Signature:** `(ctx: MatchingContext, data: bytes) -> bytes`

#### `TapeDecorator`
**Signature:** `(ctx: MatchingContext, tape: dict) -> dict`

### Exceptions
**Location:** `src/claudecontrol/replay/exceptions.py`

#### `TapeMissError`
**When:** No tape matches the current input/context
**Message includes:** Expected context and available tapes

#### `SchemaError`
**When:** Tape format is invalid or corrupted
**Message includes:** Schema validation errors

#### `RedactionError`
**When:** Secret redaction fails
**Message includes:** Redaction pattern that failed

### Normalization Utilities
**Location:** `src/claudecontrol/replay/normalize.py`

#### `strip_ansi(text: str) -> str`
**Purpose:** Remove ANSI escape sequences from text

#### `collapse_ws(text: str) -> str`
**Purpose:** Normalize whitespace (collapse runs to single space)

#### `scrub(text: str) -> str`
**Purpose:** Replace timestamps, PIDs, UUIDs with placeholders

### Redaction Utilities
**Location:** `src/claudecontrol/replay/redact.py`

#### `redact_bytes(data: bytes) -> bytes`
**Purpose:** Remove passwords, tokens, and secrets from data
**Patterns:** API keys, passwords, AWS keys, tokens
**Environment:** Set `CLAUDECONTROL_REDACT=0` to disable

### Summary Utilities
**Location:** `src/claudecontrol/replay/summary.py`

#### `print_summary(store: TapeStore) -> None`
**Purpose:** Print new and unused tapes at exit
**Format:**
```
===== SUMMARY (claude_control) =====
New tapes:
- program/tape-name.json5
Unused tapes:
- program/unused-tape.json5
```

---

## Helper Function Interfaces

### `test_command(command: str, expected_output: Union[str, List[str]], timeout: int = 30, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]`
**Purpose:** Test if a command produces expected output
**Location:** `src/claudecontrol/claude_helpers.py`

**Returns:** Tuple of `(success, error_message)` where `error_message` is `None` when all expected outputs are found
**Error Handling:** Returns `(False, str(e))` on any exception

### `interactive_command(command: str, interactions: List[Dict[str, str]], timeout: int = 30, cwd: Optional[str] = None) -> str`
**Purpose:** Run command with scripted interactions

**Parameters:**
- `interactions`: List of dicts with "expect" and "send" keys
  ```python
  [
      {"expect": "login:", "send": "admin"},
      {"expect": "password:", "send": "secret", "delay": 0.5}
  ]
  ```

**Returns:** Full output from session

### `parallel_commands(commands: List[str], timeout: int = 30, max_concurrent: int = 10) -> Dict[str, Dict[str, Any]]`
**Purpose:** Execute multiple commands in parallel

**Returns:**
```python
{
    "command1": {
        "success": true,
        "output": "string",
        "error": null
    },
    "command2": {
        "success": false,
        "output": null,
        "error": "error message"
    }
}
```

### `watch_process(command: str, watch_for: Union[str, List[str]], callback: Optional[callable] = None, timeout: int = 300, cwd: Optional[str] = None) -> List[str]`
**Purpose:** Monitor process for specific patterns

**Parameters:**
- `callback`: Function called with (session, pattern) when pattern found

**Returns:** List of matched patterns
**Side Effects:** Callback execution on pattern match

---

## Pattern Matching Interface

### `extract_json(output: str) -> Optional[Union[dict, list]]`
**Purpose:** Extract and parse JSON from text
**Location:** `src/claudecontrol/patterns.py`

**Returns:** Parsed JSON object or None

### `detect_prompt_pattern(output: str) -> Optional[str]`
**Purpose:** Detect command prompt pattern
**Returns:** Prompt pattern or None

### `is_error_output(output: str) -> bool`
**Purpose:** Check if output contains error indicators
**Returns:** True if errors detected

### `classify_output(output: str) -> Dict[str, Any]`
**Purpose:** Classify output characteristics

**Returns:**
```python
{
    "is_error": bool,
    "data_formats": ["JSON", "XML"],
    "has_prompt": bool,
    "state_transition": "state_name or None",
    "line_count": int,
    "has_table": bool,
    "has_json": bool
}
```

---

## Command Chain Interface

### CommandChain Class
**Location:** `src/claudecontrol/claude_helpers.py`

#### `add(command: str, expect: Optional[str] = None, send: Optional[str] = None, condition: Optional[callable] = None, on_success: bool = False, on_failure: bool = False)`
**Purpose:** Add command to chain

**Parameters:**
- `condition`: Function(results) -> bool to determine if command should run
- `on_success`: Only run if previous command succeeded
- `on_failure`: Only run if previous command failed

#### `run() -> List[Dict[str, Any]]`
**Purpose:** Execute the command chain

**Returns:**
```python
[
    {
        "command": "string",
        "output": "string",
        "success": true,
        "error": null
    }
]
```

---

## CLI Interface

### Command Line Tools
**Entry Point:** `ccontrol` or `claude-control`

#### Interactive Menu
```bash
ccontrol  # Opens interactive menu
```

#### Direct Commands
```bash
# Run command
ccontrol run "command" [--expect "pattern"] [--timeout 30]

# Investigate program
ccontrol investigate program_name [--timeout 10] [--no-save]

# Probe interface
ccontrol probe program_name [--json] [--timeout 5]

# Fuzz test
ccontrol fuzz program_name [--max-inputs 50] [--timeout 5]

# Record & Replay
ccontrol rec program [args...]  # Record new session
ccontrol play program [args...]  # Replay from tape
ccontrol proxy program [args...]  # Replay with fallback

# Tape management
ccontrol tapes list [--used | --unused]  # List tapes
ccontrol tapes validate [--strict]  # Validate tape format
ccontrol tapes redact [--inplace]  # Remove secrets

# Session management
ccontrol list  # List active sessions
ccontrol status  # System status
ccontrol attach session_id  # Attach to session
ccontrol clean [--force]  # Clean up sessions

# Configuration
ccontrol config list
ccontrol config show config_name
ccontrol config delete config_name
```

---

## Configuration Interface

### Session Configuration
**Location:** `~/.claude-control/config.json`

```json
{
    "session_timeout": 300,
    "max_sessions": 20,
    "auto_cleanup": true,
    "log_level": "INFO",
    "output_limit": 10000,
    "max_session_runtime": 3600,
    "max_output_size": 104857600,
    "replay": {
        "tapes_path": "~/.claude-control/tapes",
        "record": "new",
        "fallback": "not_found",
        "latency": 0,
        "error_rate": 0,
        "summary": true
    }
```

### Program Configuration
**Save:** `Session.save_program_config(name: str, include_output: bool = False)`
**Load:** `Session.from_config(name: str, **kwargs)`

**Structure:**
```json
{
    "name": "string",
    "command_template": "string",
    "expect_sequences": [],
    "success_indicators": [],
    "ready_indicators": [],
    "typical_timeout": 30,
    "notes": "string",
    "sample_output": []
}
```

---

## Error Handling

### Exception Types

#### `SessionError`
**When:** Session-related errors (not alive, not found, etc.)
**Message includes:** Session ID and state

#### `TimeoutError`
**When:** Pattern not found within timeout
**Message includes:** Expected patterns and recent output (last 50 lines)

#### `ProcessError`
**When:** Process spawn failure or unexpected death
**Message includes:** Command and exit status

#### `ConfigNotFoundError`
**When:** Requested configuration doesn't exist
**Message includes:** Config name and path

#### `TapeMissError`
**When:** No tape matches current input/context in replay mode
**Message includes:** Expected context and available tapes

#### `SchemaError`
**When:** Tape format is invalid or corrupted
**Message includes:** Schema validation errors

#### `RedactionError`
**When:** Secret redaction fails during recording
**Message includes:** Redaction pattern that failed

---

## State Management

### Session Registry
- **Global registry:** In-memory dict of active sessions
- **Thread-safe:** Protected by threading lock
- **Automatic cleanup:** On program exit if auto_cleanup=True
- **Reuse logic:** Matches by command string and alive status

### Session Persistence
- **Session logs:** `~/.claude-control/sessions/{id}/output.log`
- **Rotation:** Automatic at 10MB
- **State file:** `~/.claude-control/sessions/{id}/state.json`

### Named Pipes (Streaming)
- **Location:** `/tmp/claudecontrol/{session_id}.pipe`
- **Format:** `[timestamp][TYPE] data\n`
- **Types:** MTX (metadata), OUT (output), ERR (error), IN (input)
- **Cleanup:** Automatic on session close

### Tape Storage
- **Location:** `./tapes/` or configured path
- **Format:** JSON5 files with `.json5` extension
- **Structure:** `{program}/{tape-name}.json5`
- **Naming:** `unnamed-{timestamp}-{hash}.json5` by default
- **Index:** Built on startup, held in memory
- **Hot-reload:** Not supported (requires restart)

---

## Performance Considerations

### Limits & Defaults
- **Max concurrent sessions:** 20 (configurable)
- **Output buffer:** 10,000 lines in memory
- **Session timeout:** 300 seconds of inactivity
- **Operation timeout:** 30 seconds default
- **Max runtime:** 3600 seconds per session
- **Log rotation:** 10MB per file
- **Tape index load:** ≤200ms per 1,000 exchanges
- **Tape match time:** ≤2ms with normalized keys
- **Replay latency jitter:** ≤50ms per chunk

### Threading
- **Parallel execution:** ThreadPoolExecutor for parallel_commands
- **Thread safety:** Global registry protected by lock
- **Blocking operations:** expect() blocks until pattern or timeout

### Resource Management
- **Zombie cleanup:** Automatic via psutil
- **Memory limits:** Configurable output buffer size
- **File handles:** Automatic cleanup on session close
- **Process limits:** Enforced by max_sessions config