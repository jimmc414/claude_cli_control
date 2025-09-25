# ClaudeControl Configuration Documentation

## Configuration Hierarchy

ClaudeControl uses a simple configuration hierarchy with minimal required settings:

1. **Command-line arguments** (highest priority)
2. **Session parameters** (Python API)
3. **Configuration files** (`~/.claude-control/config.json`)
4. **Program configurations** (`~/.claude-control/programs/*.json`)
5. **Default values in code** (lowest priority)

## Core Configuration

### Session Management
| Setting | Env Var | Config Key | Default | Required | Description |
|---------|---------|------------|---------|----------|-------------|
| Session Timeout | - | `session_timeout` | 300s | No | Idle timeout before session cleanup |
| Default Timeout | - | `default_timeout` | 30s | No | Default expect() timeout |
| Max Sessions | - | `max_sessions` | 20 | No | Maximum concurrent sessions |
| Auto Cleanup | - | `auto_cleanup` | true | No | Clean dead sessions automatically |
| Buffer Size | - | `output_limit` | 10000 | No | Output buffer lines in memory |
| Max Runtime | - | `max_session_runtime` | 3600s | No | Maximum session lifetime |
| Max Output Size | - | `max_output_size` | 100MB | No | Maximum log file size |

**Example config.json:**
```json
{
    "session_timeout": 300,
    "default_timeout": 30,
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
}
```

### Logging Configuration
| Setting | Env Var | Config Key | Default | Required | Description |
|---------|---------|------------|---------|----------|-------------|
| Log Level | `LOG_LEVEL` | `log_level` | INFO | No | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |
| Log Directory | - | `log_dir` | `~/.claude-control/logs` | No | Log file location |
| Log Rotation | - | `log_rotation_size` | 10MB | No | Rotate logs at this size |
| Keep Logs | - | `keep_log_days` | 7 | No | Days to retain old logs |

### Process Control
| Setting | CLI Flag | API Parameter | Default | Required | Description |
|---------|----------|---------------|---------|----------|-------------|
| Command | `command` | `command` | - | Yes | CLI program to control |
| Timeout | `--timeout` | `timeout` | 30s | No | Operation timeout |
| Working Dir | `--cwd` | `cwd` | Current | No | Process working directory |
| Environment | - | `env` | Inherited | No | Environment variables dict |
| Encoding | - | `encoding` | utf-8 | No | Character encoding |
| Dimensions | - | `dimensions` | (24, 80) | No | Terminal size (rows, cols) |
| Persist | - | `persist` | true | No | Keep session in registry |
| Stream | - | `stream` | false | No | Enable named pipe streaming |

**CLI Example:**
```bash
ccontrol run "npm test" --timeout 60 --cwd /project
```

**Python API Example:**
```python
session = Session(
    command="npm test",
    timeout=60,
    cwd="/project",
    persist=True,
    stream=False
)
```

## Record & Replay Configuration

### Recording Settings
| Setting | CLI Flag | API Parameter | Config Key | Default | Description |
|---------|----------|---------------|------------|---------|-------------|
| Tapes Path | `--tapes` | `tapes_path` | `replay.tapes_path` | `./tapes` | Directory for tape storage |
| Record Mode | `--record` | `record` | `replay.record` | `disabled` | Recording mode (new/overwrite/disabled) |
| Fallback Mode | `--fallback` | `fallback` | `replay.fallback` | `not_found` | Fallback when tape not found |
| Tape Name Generator | - | `tape_name_generator` | - | Auto | Custom naming function |
| Summary | `--summary` | `summary` | `replay.summary` | true | Print tape usage summary |
| Silent | `--silent` | `silent` | `replay.silent` | false | Suppress mid-operation logs |

**CLI Examples:**
```bash
# Record a new session
ccontrol rec sqlite3 -batch --tapes ./my-tapes

# Replay from tape
ccontrol play sqlite3 -batch --tapes ./my-tapes

# Replay with fallback to live
ccontrol proxy sqlite3 -batch --fallback proxy
```

**Python API Example:**
```python
from claudecontrol import Session, RecordMode, FallbackMode

# Recording session
session = Session(
    "sqlite3",
    args=["-batch"],
    tapes_path="./tapes",
    record=RecordMode.NEW,
    summary=True
)

# Replay session
session = Session(
    "sqlite3",
    args=["-batch"],
    record=RecordMode.DISABLED,
    fallback=FallbackMode.NOT_FOUND
)
```

### Matching Configuration
| Setting | API Parameter | Config Key | Default | Description |
|---------|---------------|------------|---------|-------------|
| Allow Env | `allow_env` | `replay.allow_env` | None | Environment vars to include in matching |
| Ignore Env | `ignore_env` | `replay.ignore_env` | ["PWD", "SHLVL"] | Environment vars to ignore |
| Ignore Args | `ignore_args` | `replay.ignore_args` | None | Argument positions/values to ignore |
| Ignore Stdin | `ignore_stdin` | `replay.ignore_stdin` | false | Ignore stdin in matching |
| Stdin Matcher | `stdin_matcher` | - | None | Custom stdin matching function |
| Command Matcher | `command_matcher` | - | None | Custom command matching function |

### Decorator Configuration
| Setting | API Parameter | Description |
|---------|---------------|-------------|
| Input Decorator | `input_decorator` | Transform input before recording |
| Output Decorator | `output_decorator` | Transform output before recording |
| Tape Decorator | `tape_decorator` | Transform tape before saving |

### Simulation Configuration
| Setting | CLI Flag | API Parameter | Config Key | Default | Description |
|---------|----------|---------------|------------|---------|-------------|
| Latency | `--latency` | `latency` | `replay.latency` | 0 | Replay latency (ms, range, or function) |
| Error Rate | `--error-rate` | `error_rate` | `replay.error_rate` | 0 | Error injection rate (0-100) |
| Debug | `--debug` | `debug` | `replay.debug` | false | Enable debug logging |

**Example with simulation:**
```python
# Test with latency and error injection
session = Session(
    "api_tool",
    record=RecordMode.DISABLED,
    latency=(100, 500),  # Random 100-500ms delays
    error_rate=10  # 10% chance of errors
)
```

### Tape Management Settings
| Setting | CLI Command | Description |
|---------|------------|-------------|
| List Tapes | `ccontrol tapes list` | List all tapes |
| List Used | `ccontrol tapes list --used` | Show used tapes |
| List Unused | `ccontrol tapes list --unused` | Show unused tapes |
| Validate | `ccontrol tapes validate` | Check tape integrity |
| Strict Validation | `ccontrol tapes validate --strict` | Strict schema validation |
| Redact | `ccontrol tapes redact` | Remove secrets from tapes |
| In-place Redact | `ccontrol tapes redact --inplace` | Modify tapes directly |

## Investigation Settings

### Program Investigation
| Setting | CLI Flag | API Parameter | Default | Description |
|---------|----------|---------------|---------|-------------|
| Safe Mode | `--unsafe` | `safe_mode` | true | Block dangerous commands |
| Timeout | `--timeout` | `timeout` | 10s | Per-operation timeout |
| Max Depth | - | `max_depth` | 5 | State exploration depth |
| Save Report | `--no-save` | `save_report` | true | Save JSON report |
| Starting Commands | - | `starting_commands` | ["help", "?"] | Initial probes |

**Example:**
```bash
ccontrol investigate mysterious_app --timeout 15 --unsafe
```

```python
report = investigate_program(
    "mysterious_app",
    timeout=15,
    safe_mode=False,
    max_depth=10
)
```

### Dangerous Commands (Safe Mode)
When `safe_mode=true`, these patterns are blocked:
- `rm -rf`
- `format`
- `del /f`
- `drop database`
- `delete from`
- `truncate`
- System shutdown commands
- Network configuration changes

## Testing Configuration

### Black Box Testing
| Setting | CLI Flag | API Parameter | Default | Description |
|---------|----------|---------------|---------|-------------|
| Test Timeout | `--timeout` | `timeout` | 10s | Per-test timeout |
| Save Report | `--no-save` | `save_report` | true | Save test results |
| Max Concurrent | - | `max_concurrent` | 3 | Concurrent test sessions |
| Resource Limits | - | - | - | CPU/Memory thresholds |

### Fuzz Testing
| Setting | CLI Flag | API Parameter | Default | Description |
|---------|----------|---------------|---------|-------------|
| Max Inputs | `--max-inputs` | `max_inputs` | 50 | Fuzz input count |
| Timeout | `--timeout` | `timeout` | 5s | Per-input timeout |
| Input Types | - | - | Built-in | Fuzz patterns to use |

**Example:**
```bash
ccontrol fuzz target_app --max-inputs 100 --timeout 3
```

## Parallel Execution

### Parallel Commands
| Setting | CLI Flag | API Parameter | Default | Description |
|---------|----------|---------------|---------|-------------|
| Max Workers | - | `max_concurrent` | 10 | Thread pool size |
| Timeout | `--timeout` | `timeout` | 30s | Per-command timeout |

**Example:**
```python
results = parallel_commands(
    ["test1", "test2", "test3"],
    timeout=60,
    max_concurrent=3
)
```

## File System Paths

### Data Storage Locations
| Data Type | Location | Configurable | Description |
|-----------|----------|--------------|-------------|
| Base Directory | `~/.claude-control/` | No | Main config directory |
| Session Logs | `~/.claude-control/sessions/{id}/` | No | Session output logs |
| Configurations | `~/.claude-control/config.json` | No | Global settings |
| Program Configs | `~/.claude-control/programs/` | No | Saved program templates |
| Investigation Reports | `~/.claude-control/investigations/` | No | Discovery reports |
| Test Reports | `~/.claude-control/test-reports/` | No | Test results |
| Tape Storage | `./tapes/` or configured path | Yes | Recorded session tapes |
| Named Pipes | `/tmp/claudecontrol/{id}.pipe` | No | Stream output pipes |

### Directory Permissions
All directories are created with mode `0700` (user-only access) for security.

## Program Configurations

Saved program configurations for reuse:

```json
{
    "name": "mysql_dev",
    "command_template": "mysql -u {user} -p{password}",
    "typical_timeout": 30,
    "expect_sequences": [
        {"pattern": "password:", "response": "{password}"},
        {"pattern": "mysql>", "response": null}
    ],
    "success_indicators": ["Query OK", "rows affected"],
    "ready_indicators": ["mysql>"],
    "notes": "Development MySQL instance",
    "sample_output": []
}
```

### Using Saved Configurations
```python
# Save configuration
session.save_program_config("mysql_dev", include_output=True)

# Load configuration
session = Session.from_config("mysql_dev", 
    user="root", 
    password="secret"
)
```

## Performance Tuning

### Resource Limits
| Setting | Config Key | Default | Impact |
|---------|------------|---------|--------|
| Output Buffer | `output_limit` | 10000 lines | Memory usage per session |
| Log Rotation | `log_rotation_size` | 10MB | Disk I/O frequency |
| Max Sessions | `max_sessions` | 20 | System resource usage |
| Session Timeout | `session_timeout` | 300s | Cleanup frequency |
| Max Runtime | `max_session_runtime` | 3600s | Prevents runaway sessions |
| Tape Index Size | - | Unlimited | Memory for tape matching |
| Chunk Buffer Size | - | 10KB | Recording chunk size |

### Optimization Settings
| Setting | When to Adjust | Impact |
|---------|---------------|--------|
| Buffer Size | Large outputs | Increase for data-heavy programs |
| Timeout | Slow programs | Increase for unresponsive CLIs |
| Max Sessions | Many parallel ops | Increase for automation scripts |
| Log Rotation | High volume | Decrease to save disk space |
| Tapes Path | Many tapes | Use fast SSD for better performance |
| Latency | Testing timing | Add realistic delays for testing |

## Configuration Validation

### Startup Checks
ClaudeControl validates configuration on initialization:

1. **Directory Creation**: Creates missing directories with proper permissions
2. **Config File**: Creates default config if missing
3. **Type Validation**: Ensures numeric values are valid
4. **Permission Checks**: Validates directory write access
5. **Resource Limits**: Warns if limits seem too high/low

### Configuration Errors
Common configuration issues and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `PermissionError: ~/.claude-control` | No write access | Check directory permissions |
| `ValueError: timeout must be positive` | Invalid timeout | Use positive integer |
| `ResourceWarning: max_sessions > 100` | Too many sessions | Reduce max_sessions |
| `ConfigNotFoundError` | Missing program config | Check config name |

## Environment-Specific Settings

### Development Mode
```json
{
    "log_level": "DEBUG",
    "auto_cleanup": true,
    "session_timeout": 60,
    "safe_mode": true,
    "replay": {
        "tapes_path": "./dev-tapes",
        "record": "new",
        "fallback": "proxy",
        "summary": true,
        "debug": true
    }
}
```

### Production/Automation Mode
```json
{
    "log_level": "WARNING",
    "auto_cleanup": true,
    "session_timeout": 300,
    "safe_mode": false,
    "max_sessions": 50,
    "max_output_size": 524288000,
    "replay": {
        "tapes_path": "/var/lib/claude-control/tapes",
        "record": "disabled",
        "fallback": "not_found",
        "summary": false,
        "silent": true
    }
}
```

### CI/Testing Mode
```json
{
    "log_level": "INFO",
    "auto_cleanup": true,
    "session_timeout": 30,
    "safe_mode": true,
    "max_sessions": 5,
    "replay": {
        "tapes_path": "./test-tapes",
        "record": "disabled",
        "fallback": "not_found",
        "summary": true,
        "error_rate": 5,
        "latency": 100
    }
}
```

## Security Configuration

### Safety Features
| Feature | Config Key | Default | Description |
|---------|------------|---------|-------------|
| Safe Mode | `safe_mode` | true | Block dangerous commands |
| Command Whitelist | - | None | Optional allowed commands only |
| Max Output Size | `max_output_size` | 100MB | Prevent disk exhaustion |
| Session Isolation | - | Always | Each session has own PTY |

### Sensitive Data Handling
- Passwords are never logged
- Session logs are user-only readable (mode 0600)
- Named pipes are user-only accessible
- No network operations by default
- Tapes automatically redact secrets (passwords, tokens, API keys)
- Redaction can be disabled with `CLAUDECONTROL_REDACT=0` for debugging
- Tape files are user-readable (mode 0600) by default

## CLI Configuration Management

### Managing Configurations
```bash
# List saved configurations
ccontrol config list

# Show configuration details
ccontrol config show mysql_dev

# Delete configuration
ccontrol config delete old_config

# Use saved configuration
ccontrol run --config mysql_dev
```

## Default Values Reference

### Timeouts (seconds)
- Default operation timeout: 30
- Session idle timeout: 300
- Investigation timeout: 10
- Fuzz test timeout: 5
- SSH connection timeout: 30
- Watch process timeout: 300

### Limits
- Max concurrent sessions: 20
- Output buffer lines: 10,000
- Max session runtime: 3600 seconds
- Log rotation size: 10MB
- Max fuzz inputs: 50
- Parallel command workers: 10
- Tape index load: ≤200ms per 1000 exchanges
- Tape match time: ≤2ms with normalized keys

### Dimensions
- Default terminal: 24 rows × 80 columns
- Minimum terminal: 10 rows × 40 columns

### Record & Replay Defaults
- Record mode: DISABLED (no recording by default)
- Fallback mode: NOT_FOUND (fail on missing tape)
- Tapes path: ./tapes
- Latency: 0 (no artificial delay)
- Error rate: 0 (no error injection)
- Summary: true (show tape usage)
- Ignore env: ["PWD", "SHLVL", "RANDOM", "_"]
- Chunk size: 4KB
- Max tape size: 100MB

## Configuration Best Practices

1. **Keep defaults for most cases** - They're tuned for typical usage
2. **Adjust timeouts for slow programs** - Some CLIs need more time
3. **Use safe mode in production** - Prevent accidental damage
4. **Enable streaming for monitoring** - Real-time output for long processes
5. **Save program configs for reuse** - Consistency across runs
6. **Set appropriate resource limits** - Prevent resource exhaustion
7. **Use session reuse wisely** - Great for servers, not for tests
8. **Record in development, replay in CI** - Build tapes locally, test in CI
9. **Use strict fallback in CI** - Fail fast when tapes are missing
10. **Redact tapes before sharing** - Remove sensitive data from recordings
11. **Version control your tapes** - Track test data alongside code
12. **Use matchers for dynamic values** - Handle timestamps and IDs gracefully

## Troubleshooting Configuration

### Debug Configuration Loading
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show config loading details
session = Session("app")
```

### Check Active Configuration
```python
from claudecontrol import status

info = status()
print(f"Config path: {info['config_path']}")
print(f"Active sessions: {info['active_sessions']}")
print(f"Session limit: {info['max_sessions']}")
```

### Reset to Defaults
```bash
# Remove custom configuration
rm ~/.claude-control/config.json

# Reinstall to recreate defaults
pip install -e .
```

## Configuration File Examples

### Minimal config.json
```json
{
    "log_level": "INFO"
}
```

### Full config.json
```json
{
    "session_timeout": 300,
    "default_timeout": 30,
    "max_sessions": 20,
    "auto_cleanup": true,
    "log_level": "INFO",
    "output_limit": 10000,
    "max_session_runtime": 3600,
    "max_output_size": 104857600,
    "log_rotation_size": 10485760,
    "keep_log_days": 7,
    "safe_mode": true,
    "replay": {
        "tapes_path": "~/.claude-control/tapes",
        "record": "disabled",
        "fallback": "not_found",
        "latency": 0,
        "error_rate": 0,
        "summary": true,
        "silent": false,
        "debug": false,
        "ignore_env": ["PWD", "SHLVL", "RANDOM", "_"],
        "allow_env": null,
        "ignore_args": null,
        "ignore_stdin": false
    }
}
```

### Program-specific configuration
```json
{
    "name": "npm_dev_server",
    "command_template": "npm run dev",
    "typical_timeout": 60,
    "expect_sequences": [
        {"pattern": "Server running at", "response": null}
    ],
    "success_indicators": ["✓", "Server running"],
    "ready_indicators": ["Listening on"],
    "notes": "Development server with hot reload",
    "sample_output": ["Server running at http://localhost:3000"]
}
```

## Tape File Format Configuration

### Tape Structure
Tapes are stored as JSON5 files with the following structure:

```json5
{
    meta: {
        createdAt: "2024-01-20T10:30:00Z",
        program: "sqlite3",
        args: ["-batch"],
        env: {LANG: "en_US.UTF-8"},  // Filtered by ignore_env
        cwd: "/home/user/project",
        pty: {rows: 24, cols: 80},
        tag: "test-query",  // Optional user tag
        latency: 0,
        errorRate: 0,
        seed: 12345  // For deterministic randomness
    },
    session: {
        version: "claudecontrol 0.1.0",
        platform: "linux-x64"
    },
    exchanges: [
        {
            pre: {prompt: "sqlite> ", stateHash: "abc123"},
            input: {type: "line", dataText: "SELECT 1;"},
            output: {
                chunks: [
                    {delay_ms: 10, dataB64: "MQo=", isUtf8: true}
                ]
            },
            exit: null,
            dur_ms: 15,
            annotations: {redacted: ["password"]}
        }
    ]
}
```

### Tape Configuration Options
| Setting | Description | Default |
|---------|-------------|---------|
| Format | File format | JSON5 |
| Extension | File extension | .json5 |
| Encoding | Character encoding | UTF-8 |
| Pretty Print | Human-readable formatting | true |
| Compression | Gzip compression (future) | false |
| Max Size | Maximum tape file size | 100MB |
| Binary Encoding | Binary data encoding | base64 |

### Tape Naming Configuration
| Pattern | Example | Description |
|---------|---------|-------------|
| Default | `unnamed-{timestamp}-{hash}.json5` | Auto-generated name |
| Program-based | `{program}/session-{date}.json5` | Organized by program |
| Custom | User function | Full control over naming |

### Tape Management Commands
```bash
# Validate tape format
ccontrol tapes validate ./tapes/sqlite3/*.json5

# Redact sensitive data
ccontrol tapes redact --inplace ./tapes/**/*.json5

# List tape statistics
ccontrol tapes list --stats

# Export tapes to different format (future)
ccontrol tapes export --format yaml ./tapes/**/*.json5
```