<!--
  Shared Agent Protocol Definition
  Version: 1.1.0
  Purpose: Ensure consistency across all agent types
  Usage: Reference this file when creating new agent primers
  Changelog:
    1.1.0 - Added coordination protocol, versioning system
    1.0.0 - Initial protocol definition
-->

# Shared Agent Protocol v1.1

## 1. Core Principles

- **Token Efficiency**: Minimize tokens while maintaining clarity
- **Consistency**: Uniform command syntax across all agents
- **Extensibility**: Easy to add new commands without breaking existing ones
- **Stateful**: Support session-based state persistence

### Important: Understanding "Agents" in Claude
- "Agents" are role-based prompting contexts, not persistent services
- Each agent invocation is a fresh Claude instance with no memory
- All state and coordination exists only within the orchestrator's session
- Multiple "agents" = multiple roles within a single conversation
- Context can be exported/imported between sessions for continuity

## 2. Command Syntax

### Format
```
#COMMAND:<param1>:<param2>:...:limit=N
```

### Rules
- Commands start with `#` at beginning of line
- Command names in UPPERCASE
- Parameters separated by `:`
- Parameters are positional, not named
- Optional parameters at end only
- Dynamic limit: `:limit=N` or `:brief/:detailed`

## 2.5 Dual-Mode Operation

### Communication Modes

The protocol supports two interaction modes:

1. **Natural Language Mode** (default for orchestrator)
   - Users speak conversationally
   - System translates to protocol internally
   - Responses in natural language
   - Protocol visible on request

2. **Protocol Mode**
   - Direct protocol commands
   - Immediate protocol responses
   - Maximum efficiency
   - No translation overhead

### Mode Selection

- Commands starting with `#` always use protocol
- Natural language processed by orchestrator
- Users can request mode switches
- Agents always use protocol internally

### Natural Language Processing

When in natural language mode:
- Orchestrator interprets user intent
- Translates to appropriate protocol commands
- Executes commands internally
- Responds in conversational language

Example:
```
User: "Can you check the test results?"
Internal: #REPORT:TestAgent:results
Response: "The tests are passing with 95% coverage."
```

### Protocol Transparency

Users can request to see internal operations:
- "show protocol" - Display commands inline
- "explain protocol" - Educational mode
- "use protocol mode" - Switch to direct protocol

## 3. Universal Commands

All agents MUST support these core commands:

| Command                     | Purpose                 | Response Format      |
| --------------------------- | ----------------------- | -------------------- |
| `#HELP`                     | List available commands | bullets ≤ 10 items   |
| `#HELP:<category>`          | Category-specific help  | bullets ≤ 6 items    |
| `#HELP:<command>`           | Detailed command help   | usage + example ≤ 20 tokens |
| `#STATE:save:<key>:<value>` | Persist session data    | "saved:<key>"        |
| `#STATE:load:<key>`         | Retrieve session data   | value or "not_found" |
| `#STATE:list`               | Show all state keys     | bullets ≤ 5 keys     |
| `#STATE:clear`              | Reset session state     | "cleared"            |
| `#ERROR:<code>:<desc>`      | Report error            | standardized format  |
| `#VERSION`                  | Protocol version        | "v1.1.0"             |
| `#LOCK:<resource>:<timeout>` | Acquire exclusive lock | "locked" or "busy:<owner>" |
| `#UNLOCK:<resource>` | Release lock | "unlocked" or "not_owner" |
| `#WAIT:<condition>:<timeout>` | Wait for condition | "ready" or "timeout" |
| `#SIGNAL:<condition>:<value>` | Signal condition | "signaled:<count>" |
| `#BROADCAST:<channel>:<msg>` | Broadcast to agents | "sent:<count>" |
| `#CHECKPOINT:create:<type>:<name>` | Create checkpoint with git | "checkpoint_id:<id>" |
| `#CHECKPOINT:list` | List available checkpoints | bullets ≤ 5 items |
| `#CHECKPOINT:diff:<id>` | Show changes since checkpoint | summary ≤ 20 tokens |
| `#ROLLBACK:<id>` | Rollback to checkpoint | "rolled_back:<id>" |
| `#ROLLBACK:status` | Current rollback state | status ≤ 10 tokens |
| `#CONTEXT:export:<filepath>[:filter]` | Export session context to file | "exported:<count> items" |
| `#CONTEXT:import:<filepath>[:mode]` | Import context from file | "imported:<count> items" |
| `#CONTEXT:list:<directory>` | List context files | bullets ≤ 10 files |
| `#CONTEXT:validate:<filepath>` | Validate context file | "valid" or error details |

## 4. Variable System

### Syntax

- Declaration: `{{VARIABLE_NAME}}`
- Naming: UPPERCASE with underscores
- Assignment: `{{VAR}}: "value"`

### Rules

- Declare variables in dedicated section
- Reference by handle throughout document
- Values limited to 50 tokens
- Support default values

## 5. Response Constraints

### Token Limits by Command Type
- Acknowledgments: ≤ 5 tokens (fixed)
- Status reports: ≤ 10 tokens (default)
- Summaries: ≤ 15 tokens (default)
- Lists: ≤ 4 items, ≤ 8 tokens each (default)
- Errors: ≤ 10 tokens (default)

### Dynamic Limit Modifiers
- `:brief` - 50% of default limit
- `:standard` - Default limit (can omit)
- `:detailed` - 200% of default limit
- `:limit=N` - Custom limit (max 100)

### Examples
```md
#ASK:topic:brief          → ≤ 4 tokens/item
#ASK:topic:detailed       → ≤ 16 tokens/item
#REPORT:agent:status:limit=25  → ≤ 25 tokens total
#ERROR:code:desc:detailed → ≤ 20 tokens
```

### Formatting
- Use bullets (`•`) for lists
- Use arrows (`→`) for flows
- Omit articles when clear
- Prefer symbols over words

## 6. State Management

### Session State
- Scope: Current session only
- Keys: Alphanumeric + underscore
- Values: ≤ 30 tokens
- Limit: 20 keys per session

### Persistence Rules
1. State cleared on session end (unless exported)
2. Keys are case-sensitive
3. Overwriting allowed
4. No nested structures

### Persistent State Marking
```md
#STATE:save:key:value:persistent
→ This key will be included in context exports

#STATE:save:temp:value
→ This key is session-only
```

## 7. Error Handling

### Error Codes

- `E001`: Unknown command
- `E002`: Invalid parameters
- `E003`: State limit exceeded
- `E004`: Token limit exceeded
- `E005`: Permission denied

### Error Response Format

```
#ERROR:<code>:<description>
```

## 8. Agent Types (Role-Based Contexts)

### Orchestrator
- Primary conversation context
- Maintains all shared state
- Delegates tasks by invoking Claude with different role prompts
- All coordination happens here

### Worker Agents (Roles)
- Temporary Claude invocations with specific prompts
- No memory between invocations
- Receive context from orchestrator
- Return results to orchestrator

### Communication Flow
```
Orchestrator Session
├── Maintains all state
├── Invokes DevAgent role → Gets response → Stores result
├── Invokes TestAgent role → Gets response → Stores result
└── Coordinates based on results
```

Note: "Multi-agent" means multiple role-based invocations within one orchestrator session, not parallel independent agents.

## 9. Extension Guidelines

When adding new commands:

1. Check for conflicts with existing commands
2. Follow naming convention (VERB:NOUN)
3. Document parameters clearly
4. Define response format with token limits
5. Add to agent's command table

## 10. Compatibility

### Version Format

`major.minor.patch`

### Breaking Changes

- Major version for incompatible changes
- Minor version for new features
- Patch version for fixes

### Backward Compatibility

- Maintain old commands for 1 major version
- Mark deprecated with `[DEPRECATED]`
- Provide migration path

### Version Negotiation

```md
Agent> #VERSION
Orchestrator> v1.1.0

Agent> #VERSION:check:1.0.0
Orchestrator> compatible

Agent> #VERSION:features
Orchestrator>
• coordination: v1.1+
• state: v1.0+
• error_codes: v1.0+
```

### Compatibility Matrix

| Protocol Version | Core Commands | State Mgmt | Coordination |
|------------------|---------------|------------|--------------|
| v1.0             | ✓ Full        | ✓ Full     | ✗ None       |
| v1.1             | ✓ Full        | ✓ Full     | ✓ Full       |

Note: Compatibility refers to protocol features, not Claude model versions. All features work with Claude 3.0+.

### Feature Detection

```md
Agent> #SUPPORTS:coordination
Orchestrator> true

Agent> #SUPPORTS:quantum_computing
Orchestrator> false
```

## 11. Help System

### Help Categories
- `core` - Basic commands (v1.0+)
- `state` - State management
- `error` - Error handling
- `coordination` - Multi-agent (v1.1+)
- `version` - Version/compatibility

### Help Response Format
```md
User> #HELP
Agent>
Core: #ASK #DEFINE #SUMMARY
State: #STATE:* (save/load/list)
Coord: #WAIT #SIGNAL [v1.1+]
[#HELP:<cat> for details]

User> #HELP:#STATE:save
Agent>
Usage: #STATE:save:<key>:<value>
Saves value (≤30 tokens) to session
Ex: #STATE:save:user:alice
```

## 11. Examples

### Basic Interaction

```md
User> #HELP
Agent>
• #ASK:<topic>
• #STATE:save:<k>:<v>
• #ERROR:<code>:<desc>

User> #STATE:save:context:auth_service
Agent>
saved:context

User> #VERSION
Agent>
v1.0.0

User> #HELP
Agent>
• #ASK:<topic> - load context
• #STATE:save:<k>:<v> - persist
• #HELP:<category> - category help
• #VERSION - check version
[Use #HELP:all for complete list]

User> #HELP:state
Agent>
• save:<k>:<v> - store value
• load:<k> - retrieve value  
• list - show all keys
• clear - reset state
```

### Orchestrator-Mediated Communication

```md
# Orchestrator maintains all state and coordination
Orchestrator> #LOCK:src/auth.js:600
Orchestrator> locked

# Orchestrator invokes Claude with DevAgent role
Orchestrator> #DELEGATE:DevAgent:implement_auth:P1
[Claude responds as DevAgent]
DevAgent> ack:task_id_123
[Response stored in orchestrator's context]

# Orchestrator records completion
Orchestrator> #STATE:save:auth_complete:true
Orchestrator> #BROADCAST:file_changes:auth_complete
Orchestrator> sent:3 [notional - actually just saved in state]

# Orchestrator invokes Claude with TestAgent role
Orchestrator> #DELEGATE:TestAgent:test_auth:P1
[Claude sees auth_complete in context]
TestAgent> ready

Orchestrator> #UNLOCK:src/auth.js
Orchestrator> unlocked
```

Note: All "communication" happens through orchestrator's session state. Agents cannot directly message each other.

## 12. Coordination Protocol

### Important: Session Scope
All coordination mechanisms (locks, broadcasts, signals) exist only within the orchestrator's session. They cannot coordinate across different Claude conversations or parallel sessions.

### Resource Locking
- Resources: files, services, state keys
- Timeout: seconds (default 300)
- Scope: Current orchestrator session only
- Auto-release on session end

### Lock Examples
```md
DevAgent> #LOCK:src/auth.js:600
Orchestrator> locked

TestAgent> #LOCK:src/auth.js:60
Orchestrator> busy:DevAgent

DevAgent> #UNLOCK:src/auth.js
Orchestrator> unlocked
```

### Dependency Management
```md
TestAgent> #WAIT:dev_complete:300
DevAgent> #SIGNAL:dev_complete:true
TestAgent> ready
```

### Broadcast Channels
- `file_changes`: File modifications
- `deploy_status`: Deployment events  
- `test_results`: Test outcomes
- `priority_alert`: Urgent updates

### Conflict Resolution Rules
1. **Priority-based**: Higher priority (P0-P3) wins
2. **First-come**: Equal priority, first lock wins
3. **Timeout**: Locks auto-expire
4. **Deadlock**: Orchestrator can force unlock

### Coordination Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `#DEPENDS:<agent>:<task>` | Declare dependency | `#DEPENDS:DevAgent:auth_impl` |
| `#SUBSCRIBE:<channel>` | Listen to broadcasts | `#SUBSCRIBE:file_changes` |
| `#UNSUBSCRIBE:<channel>` | Stop listening | `#UNSUBSCRIBE:test_results` |
| `#DIRECT:<agent>:<msg>` | Direct message | `#DIRECT:TestAgent:auth_ready` |

## 13. Checkpoint & Rollback Protocol

### Checkpoint Creation
```md
#CHECKPOINT:create:manual:before_refactor
→ git add -A
→ git commit -m "Checkpoint: before_refactor [cp_001]"
→ checkpoint_id:cp_001
```

### Checkpoint Types
- `manual` - User/orchestrator initiated
- `auto` - Before risky operations
- `milestone` - Major task completion

### Rollback Safety
```md
#ROLLBACK:cp_001
→ Check uncommitted changes
→ Stash if needed
→ git reset --hard <commit>
→ Restore state memory
→ rolled_back:cp_001
```

### Rollback Options
- `#ROLLBACK:<id>` - Safe rollback with checks
- `#ROLLBACK:<id>:force` - Skip safety checks
- `#ROLLBACK:dry-run:<id>` - Preview changes

### Example Recovery Flow
```md
Orchestrator> #CHECKPOINT:create:manual:pre_deploy
→ checkpoint_id:cp_001

DevAgent> [Modifies files, then fails]

Orchestrator> #CHECKPOINT:diff:cp_001
→ Files changed: 5, Lines: +120 -45

Orchestrator> #ROLLBACK:cp_001
→ Stashing uncommitted changes
→ Rolling back to cp_001
→ Files restored: 5
→ State restored: 8 keys
→ rolled_back:cp_001
```

### Git Integration Rules
1. Each checkpoint creates a git commit
2. Checkpoint ID maps to commit hash
3. Rollback uses git reset --hard
4. Uncommitted work auto-stashed
5. State memory synced with files

## 14. Dynamic Token Limits

### When to Use
- **Brief**: Quick status checks, confirmations
- **Standard**: Normal operations (default)
- **Detailed**: Debugging, audits, complex explanations
- **Custom**: Special cases with specific needs

### Smart Defaults
Certain scenarios auto-adjust limits:
- Error with P0 task: auto-detailed
- Routine progress: auto-brief
- Security/audit: auto-detailed
- Checkpoint diff: scales with changes

### Examples
```md
# Quick check
User> #REPORT:DevAgent:progress:brief
DevAgent>
• Auth: 80%
• Tests: pending

# Detailed audit
User> #REPORT:DevAgent:security:detailed  
DevAgent>
• SQL injection: sanitized all inputs
• XSS: escaped user content in views
• CSRF: tokens on all forms
• Auth: JWT with 15min expiry
• Audit log: enabled for all endpoints

# Custom limit for special case
User> #ASK:dependencies:limit=50
Agent>
[Up to 50 tokens of dependency info]
```

### Limit Negotiation
```md
User> #ASK:complex_topic:limit=200
Agent> #ERROR:E004:max_limit_100

User> #ASK:complex_topic:limit=100
Agent>
[100 tokens of response]
```

## 15. Session Management

### Context Window Limits
- Claude context: ~100k tokens
- Monitor usage with #HEALTH:context
- Checkpoint before 80% full
- Start fresh session if needed

### State Management
- Max 20 state keys per session
- Each value ≤ 30 tokens
- Clear unused state regularly
- Checkpoint important state

### Session Health Monitoring
```md
#HEALTH:session
• Context: 45k/100k tokens (45%)
• State: 12/20 keys (60%)
• Errors: 2 in last 10 commands
• Uptime: 2h 15m
• Status: healthy
```

### When to Start New Session
- Context >80% full
- State keys exhausted
- Error rate increasing
- Performance degrading
- Major phase transition

## 16. Context Export/Import

### Export Filters
- `:all` - Everything including temporary state
- `:critical` - Only persistent state & config
- `:tasks` - Task progress and status
- `:state` - State values only
- `:incremental` - Changes since last export

### File Format (YAML)
```yaml
version: 1.1.0
exported: 2024-01-15T14:30:00Z
session_id: ctx_789
git_checkpoint: abc123

state:
  persistent:
    key: value
  temporary:
    key: value

tasks:
  completed: [task1, task2]
  in_progress:
    task3: 80%
  pending: [task4, task5]

configuration:
  PROJECT_NAME: MyProject
  TECH_STACK: Node,React
```

### Export Examples
```md
# Manual export before ending session
#CONTEXT:export:./context/session_final.ctx
→ exported:45 items (8.2k)
→ git_ref:abc123
→ file:./context/session_final.ctx

# Auto-export on context pressure
#HEALTH:context
→ 92k/100k tokens
→ auto-exporting...
#CONTEXT:export:./context/auto_20240115_1430.ctx:critical
→ exported:25 critical items
```

### Import Examples
```md
# Start new session with previous context
#CONTEXT:import:./context/session_final.ctx
→ validated:git_ref:abc123
→ imported:45 items
→ tasks:1 active, 2 pending
→ ready to resume

# Merge additional context
#CONTEXT:import:./context/security_audit.ctx:merge
→ merged:12 new items
→ updated:3 existing items
```

### Context Management
```md
#CONTEXT:list:./context/
• session_final.ctx (2h ago, 8.2k)
• auto_20240115_1430.ctx (30m ago, 4.1k)
• security_audit.ctx (1d ago, 2.3k)

#CONTEXT:validate:./context/session_final.ctx
→ valid:protocol v1.1
→ git_checkpoint:found
→ items:45 compatible
```

## 17. Best Practices

1. **Always validate** command syntax before processing
2. **Fail fast** with clear error codes
3. **Log state changes** for debugging
4. **Respect token limits** strictly
5. **Use state** to avoid repetition
6. **Document extensions** in agent primer

---

_This protocol ensures all agents speak the same language, making the system predictable and maintainable._
