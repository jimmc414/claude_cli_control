# ClaudeControl - Multi-Purpose CLI Tool with Record & Replay

## 🎯 One Library, Four Essential Capabilities

ClaudeControl is not just another CLI automation library. It's a comprehensive toolkit that solves four fundamental challenges when working with command-line programs:

### 1. Discovery Challenge 🔍
**"I have this CLI tool but no idea how to use it"**

Traditional approach:
- Try random commands hoping something works
- Search for documentation that may not exist
- Read source code if available
- Ask colleagues who might know

ClaudeControl approach:
```python
report = investigate_program("mystery_tool")
# Automatically discovers:
# - All available commands
# - Help system
# - Input/output formats
# - State transitions
# - Error patterns
```

### 2. Testing Challenge 🧪
**"How do I know this CLI tool is reliable?"**

Traditional approach:
- Write custom test scripts
- Manual testing with various inputs
- Hope you covered all edge cases
- No standardized testing approach

ClaudeControl approach:
```python
results = black_box_test("cli_tool")
# Automatically tests:
# - Startup/shutdown behavior
# - Error handling
# - Resource usage
# - Concurrent usage
# - Fuzz testing
# - Performance limits
```

### 3. Automation Challenge 🤖
**"I need to automate this complex CLI workflow"**

Traditional approach:
- Fragile shell scripts
- No error recovery
- Can't handle interactive prompts
- Difficult parallel execution
- No session persistence

ClaudeControl approach:
```python
with Session("cli_tool") as s:
    s.expect("login:")
    s.sendline("user")
    s.expect("password:")
    s.sendline("pass")
    # Robust automation with full control
```

### 4. Reproducibility Challenge 📼
**"I need to record CLI sessions and replay them reliably"**

Traditional approach:
- Script recording tools that break easily
- No way to handle dynamic values
- Can't mock CLI tools for testing
- Manual session documentation
- No CI/CD integration

ClaudeControl approach:
```python
# Record a session to a human-editable tape
with Session("sqlite3", record=RecordMode.NEW, tapes_path="./tapes") as s:
    s.expect("sqlite>")
    s.sendline("SELECT * FROM users;")
    s.expect("sqlite>")
    # Session automatically saved as JSON5 tape

# Replay without running the actual program
with Session("sqlite3", record=RecordMode.DISABLED,
             fallback=FallbackMode.NOT_FOUND) as s:
    s.expect("sqlite>")
    s.sendline("SELECT * FROM users;")
    s.expect("sqlite>")
    # Plays back from tape - perfect for CI/CD

# Or use the CLI for quick recording
$ ccontrol rec sqlite3 -batch  # Record session
$ ccontrol play sqlite3 -batch  # Replay session
$ ccontrol proxy sqlite3 -batch  # Replay with fallback to live
```

## 💡 Why This Matters

Most CLI tools and libraries focus on just one aspect:
- **pexpect** - Low-level automation (aspect 3 only)
- **pytest** - Testing framework (aspect 2 only)
- **argparse** - Building CLIs (not using them)
- **subprocess** - Basic execution (limited interaction)
- **script/ttyrec** - Basic recording (no intelligent replay)
- **VCR.py** - HTTP mocking (not CLI sessions)

ClaudeControl is unique because it handles **all four aspects** in an integrated way:
- First, **discover** what the tool can do
- Then, **test** that it works reliably
- Next, **record** real sessions as reusable tapes
- Finally, **automate** it with confidence and **replay** for testing

## 🚀 Perfect For

### Developers & DevOps
- Quickly understand new CLI tools
- Create reliable deployment automation
- Test CLI tools before production
- Record deployment sessions for documentation
- Mock CLI tools in CI/CD pipelines

### Security Professionals
- Black-box testing of CLI applications
- Fuzzing for vulnerability discovery
- Automated security tool orchestration
- Record and replay attack scenarios
- Create reproducible security test suites

### QA Engineers
- Comprehensive CLI testing
- Automated regression testing
- Performance benchmarking
- Record bug reproduction steps
- Create deterministic test environments

### System Administrators
- Legacy system automation
- Multi-tool workflow orchestration
- Monitoring and alerting
- Document complex procedures as tapes
- Train new staff with recorded sessions

### Data Engineers
- Database CLI automation
- ETL tool orchestration
- Data pipeline testing
- Record data migration procedures
- Test pipelines without production access

## 🎨 The ClaudeControl Philosophy

1. **Zero Configuration** - Works out of the box
2. **Smart Defaults** - Intelligent behavior without setup
3. **Safety First** - Protection against dangerous operations
4. **Complete Coverage** - From discovery to testing to automation to replay
5. **Elegant API** - Simple for simple tasks, powerful when needed
6. **Human-Editable Tapes** - JSON5 format for easy modification
7. **Deterministic Replay** - Perfect reproduction for testing

## 📈 Impact

Before ClaudeControl:
- 🕐 Hours spent figuring out CLI tools
- 🐛 Fragile automation scripts
- ❌ Incomplete testing
- 📚 Dependency on documentation
- 🔄 Cannot reproduce issues reliably
- 🚫 No way to test without real systems

After ClaudeControl:
- ⚡ Minutes to understand any CLI
- 💪 Robust automation
- ✅ Comprehensive testing
- 🔍 Self-discovering interfaces
- 📼 Perfect session reproduction
- 🎭 Mock CLI tools for testing

## 🌟 Summary

ClaudeControl transforms how you interact with CLI programs by providing:

1. **Investigation capabilities** that eliminate the need for documentation
2. **Testing framework** that ensures reliability
3. **Automation tools** that handle any complexity
4. **Record & Replay system** that enables perfect reproduction

It's not just about automating CLIs - it's about understanding them, testing them, recording real-world usage, and replaying sessions with complete determinism.

### Key Features of Record & Replay

- **📝 Human-Editable Tapes** - JSON5 format with comments for easy modification
- **🎯 Intelligent Matching** - Handles dynamic values like timestamps and IDs
- **🔒 Secret Redaction** - Automatically removes passwords and tokens
- **⏱️ Latency Simulation** - Reproduce timing for realistic playback
- **🎲 Error Injection** - Test error handling with controlled failures
- **📊 Exit Summaries** - Track new and unused tapes automatically
- **🔄 Multiple Modes** - Record new, overwrite existing, or replay-only
- **🏗️ CI/CD Ready** - Perfect for testing without real systems

**One library. Four capabilities. Complete CLI mastery.**