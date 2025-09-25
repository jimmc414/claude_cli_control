# ClaudeControl Call Graph Documentation

## Entry Points and Call Chains

### CLI Command Entry Points

```mermaid
graph TD
    subgraph "CLI Entry Points"
        CLI_run[ccontrol run<br/>cmd_run]
        CLI_investigate[ccontrol investigate<br/>cmd_investigate]
        CLI_test[ccontrol test<br/>cmd_test]
        CLI_probe[ccontrol probe<br/>cmd_probe]
        CLI_fuzz[ccontrol fuzz<br/>cmd_fuzz]
        CLI_rec[ccontrol rec<br/>cmd_rec]
        CLI_play[ccontrol play<br/>cmd_play]
        CLI_proxy[ccontrol proxy<br/>cmd_proxy]
        CLI_tapes[ccontrol tapes<br/>cmd_tapes]
        CLI_menu[ccontrol<br/>interactive_menu]
    end
    
    subgraph "Core Control Layer"
        control[control<br/>get/create session]
        Session_init[Session.__init__]
        spawn[pexpect.spawn]
        registry[SESSION_REGISTRY.add]
        transport[Transport<br/>Live/Replay]
    end

    subgraph "Record & Replay Layer"
        Recorder_init[Recorder.__init__]
        ChunkSink[ChunkSink.write]
        TapeStore_init[TapeStore.__init__]
        TapeStore_load[TapeStore.load_all]
        Player_init[ReplayTransport.__init__]
        Player_send[ReplayTransport.send]
        Player_expect[ReplayTransport.expect]
        tape_match[match_exchange]
    end
    
    subgraph "Investigation Layer"
        investigate[investigate_program]
        ProgramInvestigator[ProgramInvestigator.__init__]
        discover[discover_interface]
        probe_commands[probe_commands]
        map_states[map_states]
    end
    
    subgraph "Testing Layer"
        black_box_test[black_box_test]
        BlackBoxTester[BlackBoxTester.__init__]
        test_startup[test_startup]
        test_resources[test_resource_usage]
        run_fuzz[run_fuzz_test]
    end
    
    CLI_run --> control
    control --> Session_init
    Session_init --> transport
    transport -->|live| spawn
    transport -->|replay| Player_init
    Session_init --> registry

    CLI_rec --> control
    control -->|record=NEW| Recorder_init
    Recorder_init --> ChunkSink
    spawn --> ChunkSink

    CLI_play --> TapeStore_init
    TapeStore_init --> TapeStore_load
    CLI_play --> control
    control -->|record=DISABLED| Player_init
    Player_init --> tape_match

    CLI_proxy --> control
    control -->|fallback=PROXY| transport

    CLI_tapes --> TapeStore_init
    TapeStore_init --> TapeStore_load

    CLI_investigate --> investigate
    investigate --> ProgramInvestigator
    ProgramInvestigator --> control
    ProgramInvestigator --> discover
    discover --> probe_commands
    discover --> map_states

    CLI_test --> black_box_test
    black_box_test --> BlackBoxTester
    BlackBoxTester --> control
    BlackBoxTester --> test_startup
    BlackBoxTester --> test_resources
    BlackBoxTester --> run_fuzz

    CLI_menu --> control
    CLI_menu --> investigate
    CLI_menu --> black_box_test
```

### Python API Entry Points

```mermaid
graph TD
    subgraph "High-Level API"
        API_run[run<br/>one-liner]
        API_control[control<br/>persistent session]
        API_investigate[investigate_program]
        API_test[test_command]
        API_parallel[parallel_commands]
    end
    
    subgraph "Session Management"
        Session_new[Session.__init__]
        Session_expect[Session.expect]
        Session_send[Session.send/sendline]
        Session_close[Session.close]
        find_session[find_session]
        register[register_session]
        setup_recorder[setup_recorder]
        setup_player[setup_player]
    end
    
    subgraph "Pattern Matching"
        wait_for_prompt[wait_for_prompt]
        detect_patterns[detect_prompt_pattern]
        classify[classify_output]
        extract_json[extract_json]
    end
    
    subgraph "Process Layer"
        spawn_process[pexpect.spawn]
        read_output[read_nonblocking]
        write_input[process.send]
        kill_process[process.terminate]
    end

    subgraph "Record/Replay Layer"
        recorder[Recorder]
        player[ReplayTransport]
        tapestore[TapeStore]
        matchers[Matchers]
        normalizers[Normalizers]
    end
    
    API_run --> Session_new
    API_run --> Session_expect
    API_run --> Session_close
    
    API_control --> find_session
    find_session -->|not found| Session_new
    find_session -->|found| Session_expect
    Session_new --> register
    Session_new -->|live mode| spawn_process
    Session_new -->|record mode| setup_recorder
    Session_new -->|replay mode| setup_player

    setup_recorder --> recorder
    setup_recorder --> spawn_process
    recorder --> normalizers

    setup_player --> player
    setup_player --> tapestore
    player --> matchers

    Session_expect -->|live| read_output
    Session_expect -->|replay| player
    Session_expect --> wait_for_prompt
    wait_for_prompt --> detect_patterns

    Session_send -->|live| write_input
    Session_send -->|record| recorder
    Session_send -->|replay| player

    Session_close --> kill_process

    API_parallel --> ThreadPoolExecutor
    ThreadPoolExecutor --> API_run
```

### Core Session Lifecycle

```mermaid
graph TD
    subgraph "Session Creation"
        control_func[control()]
        find[find_session]
        new[Session.__init__]
        spawn[pexpect.spawn]
        setup[setup_directories]
        register[register_session]
        init_recorder[init_recorder]
        init_player[init_replay]
        load_tapes[load_tapes]
    end
    
    subgraph "Session Operations"
        expect[expect]
        send[send/sendline]
        read[get_output]
        check[is_alive]
    end
    
    subgraph "Session Cleanup"
        close[close]
        terminate[terminate_process]
        cleanup[cleanup_resources]
        unregister[unregister_session]
    end
    
    control_func --> find
    find -->|miss| new
    new -->|live| spawn
    new -->|record| init_recorder
    new -->|replay| init_player
    new --> setup
    new --> register

    init_recorder --> spawn
    init_player --> load_tapes

    register --> expect
    register --> send

    expect --> read
    send --> check

    close --> terminate
    terminate --> cleanup
    cleanup --> unregister
```

## Record & Replay Call Flow

### Recording Flow
```mermaid
graph TD
    subgraph "Recording Session"
        rec_session[Session with record=NEW]
        recorder[Recorder.__init__]
        chunk_sink[ChunkSink]
        pexpect_hook[logfile_read hook]
        on_send[on_send]
        on_exchange[on_exchange_end]
        save_tape[save_tape]
    end

    subgraph "Data Processing"
        normalize[normalize_text]
        redact[redact_secrets]
        decorator[apply_decorators]
        encode[base64_encode]
    end

    rec_session --> recorder
    recorder --> chunk_sink
    chunk_sink --> pexpect_hook
    Session.send --> on_send
    on_send --> normalize
    Session.expect --> on_exchange
    on_exchange --> redact
    on_exchange --> decorator
    on_exchange --> encode
    on_exchange --> save_tape
```

### Replay Flow
```mermaid
graph TD
    subgraph "Replay Session"
        play_session[Session with record=DISABLED]
        tapestore[TapeStore.load_all]
        player[ReplayTransport]
        match_input[match_input]
        find_tape[find_matching_tape]
        stream_output[stream_chunks]
    end

    subgraph "Matching Logic"
        normalize_input[normalize_input]
        apply_matchers[apply_matchers]
        check_env[check_environment]
        check_args[check_arguments]
    end

    play_session --> tapestore
    tapestore --> player
    Session.send --> match_input
    match_input --> normalize_input
    normalize_input --> apply_matchers
    apply_matchers --> check_env
    check_env --> check_args
    check_args --> find_tape
    find_tape --> stream_output
    stream_output --> Session.expect
```

## Call Frequency Analysis

### High-Traffic Paths

| Function | Called By | Frequency | Performance Impact |
|----------|-----------|-----------|-------------------|
| `Session.expect()` | All automation | Every interaction | Critical - blocks until pattern |
| `Session.is_alive()` | Session operations | Before every operation | Low - process poll |
| `read_nonblocking()` | expect, monitoring | Continuous during wait | Medium - I/O bound |
| `SESSION_REGISTRY.get()` | control with reuse | Every reuse request | Low - dict lookup |
| `detect_prompt_pattern()` | Investigation | Per output chunk | Medium - regex matching |
| `classify_output()` | Investigation/Testing | Per command response | Medium - multiple patterns |
| `ChunkSink.write()` | Recording mode | Every output chunk | Low - memory append |
| `TapeStore.load_all()` | Replay init | Once at startup | High - disk I/O |
| `match_exchange()` | Replay mode | Every send/expect | Low - hash lookup |
| `stream_chunks()` | Replay mode | Per expect | Low - memory read |

### Performance-Critical Paths

#### Session Creation Path
```
control(command, reuse=True)  [~10ms if reused, ~100ms if new]
  └── SESSION_REGISTRY.get()  [<1ms]
      └── Session.is_alive()  [~1ms]
          └── process.poll()  [<1ms]
  OR
  └── Session.__init__()  [~50-250ms depending on mode]
      └── Live Mode:
          └── pexpect.spawn()  [~45ms]
          └── create_directories()  [~5ms]
      └── Record Mode:
          └── pexpect.spawn()  [~45ms]
          └── Recorder.__init__()  [~5ms]
          └── ChunkSink setup  [<1ms]
      └── Replay Mode:
          └── TapeStore.load_all()  [~200ms for 1000 exchanges]
          └── build_index()  [~10ms]
          └── ReplayTransport.__init__()  [<1ms]
```

#### Pattern Matching Path
```
Session.expect(patterns, timeout=30)  [0-30000ms]
  └── read_nonblocking()  [~1ms per call]
      └── pattern.search()  [<1ms per pattern]
          └── store_match()  [<1ms]
  OR timeout
      └── TimeoutError with output  [~10ms to format]
```

#### Record/Replay Path
```
Recording Flow:
Session.send(data)  [~1-5ms]
  └── Recorder.on_send()  [<1ms]
      └── normalize_text()  [<1ms]
  └── pexpect.send()  [~1ms]
  └── ChunkSink.write()  [<1ms per chunk]
      └── base64_encode()  [<1ms]

Session.expect()  [varies]
  └── pexpect.expect()  [0-timeout]
  └── Recorder.on_exchange_end()  [~5-10ms]
      └── redact_secrets()  [~2ms]
      └── apply_decorators()  [~1ms]
      └── save_tape()  [~5ms disk I/O]

Replay Flow:
Session.send(data)  [~2ms]
  └── ReplayTransport.send()  [~2ms]
      └── match_exchange()  [<2ms]
          └── normalize_input()  [<1ms]
          └── hash_lookup()  [<1ms]
      └── stream_chunks()  [<1ms]

Session.expect()  [deterministic based on tape]
  └── ReplayTransport.expect()  [~1ms per chunk]
      └── apply_latency()  [configurable delay]
      └── pattern_match()  [<1ms]
```

#### Investigation Path
```
investigate_program(program)  [5-60 seconds]
  └── ProgramInvestigator.__init__()  [~100ms]
      └── Session.__init__()  [~100ms]
  └── discover_interface()  [5-60s]
      └── probe_commands()  [~1s per command]
          └── Session.sendline()  [<1ms]
          └── Session.expect()  [0-timeout]
      └── map_states()  [~2s per state]
          └── detect_state_transition()  [~10ms]
```

## Recursive and Complex Patterns

### State Exploration (Recursive)
```python
def explore_state(state_name, depth=0):
    """Recursively explore program states"""
    if depth >= MAX_DEPTH:  # Base case
        return
    
    for command in get_commands(state_name):
        new_state = send_and_detect(command)
        if new_state and new_state not in visited:
            explore_state(new_state, depth + 1)  # Recursive call
```

### Command Chain Execution
```python
CommandChain.run()
  └── for each command:
      └── check_condition(previous_results)
          └── Session.sendline(command)
              └── Session.expect(pattern)
                  └── store_result()
                      └── continue or break
```

### Parallel Execution Pattern
```python
parallel_commands(commands)
  └── ThreadPoolExecutor(max_workers=10)
      └── for each command (parallel):
          └── run(command)
              └── Session.__init__()
              └── Session.expect()
              └── Session.close()
      └── gather_results()
```

## Cross-Module Dependencies

### Module Interaction Matrix

| Caller → | core | patterns | investigate | testing | helpers | replay | cli |
|----------|------|----------|-------------|---------|---------|--------|-----|
| **core** | - | ✓ | - | - | - | ✓ | - |
| **patterns** | Weak | - | - | - | - | - | - |
| **investigate** | ✓ | ✓ | - | - | - | - | - |
| **testing** | ✓ | ✓ | ✓ | - | ✓ | - | - |
| **helpers** | ✓ | ✓ | ✓ | - | - | - | - |
| **replay** | Weak | ✓ | - | - | - | - | - |
| **cli** | ✓ | - | ✓ | ✓ | ✓ | ✓ | - |

✓ = Direct function calls between modules
Weak = Optional/conditional usage

### Dependency Flow
```mermaid
graph LR
    CLI --> Helpers
    CLI --> Core
    CLI --> Investigate
    CLI --> Testing
    CLI --> Replay

    Helpers --> Core
    Helpers --> Patterns
    Helpers --> Investigate

    Investigate --> Core
    Investigate --> Patterns

    Testing --> Core
    Testing --> Patterns
    Testing --> Helpers
    Testing --> Investigate

    Core --> Patterns
    Core --> Replay

    Replay --> Patterns
    Replay -.-> Core

    Patterns -.-> Core
```

## Critical Function Dependencies

### Most Depended Upon Functions

1. **`Session.__init__`**
   - Called by: All entry points
   - Critical for: Process spawning, transport selection
   - Change impact: **Very High**
   - Dependencies: pexpect, psutil, replay.Transport

2. **`Session.expect`**
   - Called by: All automation code
   - Critical for: Pattern matching
   - Change impact: **Very High**
   - Dependencies: patterns module, pexpect, ReplayTransport

3. **`control`**
   - Called by: All high-level functions
   - Critical for: Session management
   - Change impact: **High**
   - Dependencies: SESSION_REGISTRY, Session

4. **`Transport` (new)**
   - Called by: Session for all I/O
   - Critical for: Live/Replay abstraction
   - Change impact: **High**
   - Dependencies: pexpect, ReplayTransport

5. **`TapeStore.load_all`** (new)
   - Called by: Replay mode init
   - Critical for: Tape indexing
   - Change impact: **Medium**
   - Dependencies: pyjson5, filesystem

6. **`detect_prompt_pattern`**
   - Called by: Investigation, helpers
   - Critical for: Interface discovery
   - Change impact: **Medium**
   - Dependencies: COMMON_PROMPTS, regex

7. **`classify_output`**
   - Called by: Investigation, testing
   - Critical for: Output analysis
   - Change impact: **Medium**
   - Dependencies: Pattern library

8. **`SESSION_REGISTRY`**
   - Used by: control, cleanup, status
   - Critical for: Session reuse
   - Change impact: **High**
   - Dependencies: threading.Lock

## Call Chain Examples

### Example 1: Interactive Command
```
success, error = test_command("npm test", "passing")
  └── run("npm test", expect="passing")
      └── Session.__init__("npm test")
          └── pexpect.spawn("npm test")
      └── Session.expect("passing")
          └── read_nonblocking()
          └── pattern.search()
      └── Session.get_output()
      └── Session.close()
          └── process.terminate()
```

### Example 2: Investigation Flow
```
investigate_program("mystery_app")
  └── ProgramInvestigator("mystery_app")
      └── Session.__init__("mystery_app")
  └── discover_interface()
      └── detect_prompt_pattern(initial_output)
      └── probe_commands(["help", "?", "--help"])
          └── Session.sendline("help")
          └── Session.expect(prompt, timeout=10)
          └── extract_commands_from_help(output)
      └── map_states(discovered_commands)
          └── explore_state("main", depth=0)
              └── detect_state_transition(output)
  └── generate_report()
      └── save_json(report_path)
```

### Example 3: Parallel Testing
```
black_box_test("app")
  └── BlackBoxTester("app")
  └── test_startup()
      └── Session.__init__("app")
      └── Session.expect(prompt, timeout=5)
  └── test_concurrent_sessions()
      └── parallel_commands(["app"] * 3)
          └── ThreadPoolExecutor.submit(run, "app")
              └── Session.__init__("app")
              └── Session.close()
  └── run_fuzz_test()
      └── fuzz_program("app", max_inputs=50)
          └── generate_fuzz_inputs()
          └── Session.sendline(fuzz_input)
  └── generate_report()
```

## Hotspot Analysis

### Functions with Highest Impact if Changed

| Function | Impact | Reason |
|----------|--------|--------|
| `pexpect.spawn` | Critical | All process control depends on it |
| `Session.__init__` | Critical | Central to all operations |
| `Session.expect` | Critical | Core pattern matching |
| `SESSION_REGISTRY` | High | Session reuse mechanism |
| `control()` | High | Main entry point |
| `detect_patterns` | Medium | Investigation accuracy |
| `classify_output` | Medium | Testing/investigation |
| `TimeoutError.__init__` | Low | Just error formatting |

### Performance Bottlenecks

1. **Pattern Matching in expect()** - Can block for full timeout
2. **Process Spawning** - ~50-100ms per new session
3. **State Exploration** - Exponential with depth
4. **Fuzz Testing** - Linear with input count
5. **Parallel Execution** - Limited by thread pool size

## Optimization Opportunities

### Current Bottlenecks
- `expect()` polls output in a loop - could use select()
- Pattern matching done sequentially - could parallelize
- Session creation synchronous - could pre-spawn
- Investigation single-threaded - could parallelize probes

### Caching Opportunities
- Compiled regex patterns (currently cached)
- Session reuse (currently implemented)
- Investigation reports (currently saved)
- Program configurations (currently saved)

## Summary

The call graph reveals ClaudeControl's architecture:

1. **Clear separation of concerns** - CLI, Core, Investigation, Testing layers
2. **Central Session class** - All operations flow through it
3. **Pattern-based architecture** - Heavy use of pattern matching throughout
4. **Session reuse optimization** - Registry prevents redundant spawning
5. **Parallel execution support** - ThreadPoolExecutor for concurrent operations
6. **Defensive error handling** - Multiple catch points in call chains

Critical paths are:
- Session creation and management
- Pattern matching in expect()
- Investigation's recursive state exploration
- Parallel command execution

The most impactful changes would be to Session class, expect() method, or the SESSION_REGISTRY, as these are used by virtually all functionality.