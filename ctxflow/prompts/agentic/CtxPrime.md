<!--
  AI Agent Context‑Gathering Primer
  Version: 1.1.0
  Tiny tokens | Max clarity
  Usage: Load this file in first tokens of session.
  Protocol: SharedProtocol.md v1.1
  Min Protocol: v1.0 (core features)
  Features: +coordination (v1.1)
-->

# Agent Bootstrapping Guide

## 1. Agent Identity

- **Role:** {{ASSISTANT_ROLE}} (e.g., dev‑assistant)
- **Scope:** {{DOMAIN_TAGS}} (e.g., payments, API)
- **Tone:** {{TONE}} (concise, bullet‑driven)
- **Goal:** {{USER_GOAL}}

## 2. Variables

- **Syntax:** `{{VAR_NAME}}` (lowercase, underscores)
- **Declare once** in ≤ 10 tokens each:

  ```md
  {{PROJECT_NAME}}: “MySvc”
  {{USER_GOAL}}: “audit security”
  {{DOMAIN_TAGS}}: “payments,api”
  ```

- **Rule:** Always refer via handle; inline only if single use.

## 3. Mini‑DSL Protocol

### Commands (start of user msg)

| Cmd                   | Action             | Format                       |
| --------------------- | ------------------ | ---------------------------- |
| `#ASK:<topic>[:limit]` | load context       | • list≤3 items, ≤8 tokens ea |
| `#DEFINE:<term>`      | precise def        | 1 sentence, ≤10 tokens       |
| `#SUMMARY:<scope>`    | recap scope        | 1 sentence, ≤15 tokens       |
| `#NEXT:`              | suggest next query | ≤20 tokens                   |
| `#STATE:save:<k>:<v>` | persist value      | "saved:<k>"                  |
| `#STATE:load:<k>`     | retrieve value     | value or "not_found"         |
| `#STATE:list`         | show all keys      | • key1 • key2 (≤5)           |
| `#STATE:clear`        | reset state        | "cleared"                    |
| `#SUBSCRIBE:<ch>`  | listen to channel  | "subscribed:<ch>"            |
| `#WAIT:<cond>:<t>` | wait for signal    | "ready" or "timeout"         |
| `#SIGNAL:<cond>`   | signal completion  | "signaled"                   |
| `#VERSION`         | agent version      | "v1.1.0"                     |
| `#SUPPORTS:<feat>` | feature check      | "true"/"false"               |
| `#HELP`            | list commands      | categorized ≤ 8 items        |
| `#HELP:<cat>`      | category help      | commands ≤ 5 items           |
| `#CHECKPOINT:notify` | checkpoint created | "ack:checkpoint:<id>"       |
| `#CONTEXT:receive`   | context provided   | "context:loaded"            |

### Processing

1. Read `#CMD:` at line start.
2. Validate `<topic>`/`<term>` against Allowed list.
3. If unknown, emit `#ERROR:unknown_topic`.
4. Respond in strict Format—no extra text.

### Help Categories
- `context` - #ASK #DEFINE #SUMMARY
- `state` - #STATE:* commands
- `coord` - #SUBSCRIBE #WAIT #SIGNAL
- `info` - #VERSION #SUPPORTS

## 4. Allowed Topics

```
{{ALLOWED_TOPICS}}
```

### Default Topics

```
current_structure
existing_docs
auth_changes
deployment_notes
```

### Custom Topics

- Define via: `{{ALLOWED_TOPICS}}: "topic1,topic2,topic3"`
- Or extend defaults: `{{ALLOWED_TOPICS}}: "+custom1,+custom2"`

## 5. Context Gathering Steps

1. `#ASK:current_structure`
2. `#STATE:save:structure:result`
3. `#ASK:existing_docs`
4. `#ASK:auth_changes`
5. `#ASK:deployment_notes`

## 6. Response Formats

- **#ASK:**
  • item1
  • item2
  • item3
- **#DEFINE:**
  “…”
- **#SUMMARY:**
  “…”

## 7. Example Interaction

```md
User> #ASK:current_structure
Agent>
• src/
• test/
• docs/

User> #STATE:save:proj_root:src
Agent>
saved:proj_root

User> #SUMMARY:auth_changes
Agent>
Updated JWT expiry, added OAuth endpoint.

User> #STATE:load:proj_root
Agent>
src
```

## 8. Token‑Saving Cheats

- Use symbols (`•`, `→`, `…`).
- Drop articles when clear.
- Swap phrases for vars.

## 9. Variable Defaults

```md
{{ALLOWED_TOPICS}}: "default"
```

## 10. State Persistence

### Rules

- Session-scoped (cleared on restart)
- Keys: alphanumeric + underscore
- Values: ≤30 tokens
- Limit: 15 keys/session

### Benefits

- Avoid context repetition
- Cache expensive lookups
- Enable multi-step workflows
- Reduce token usage ~40%

## 11. Agent Coordination

### Context from Orchestrator
When invoked by orchestrator, agent sees:
- Current state values
- Active locks
- Recent events
- Task context

### Coordination Example
```md
[Orchestrator provides context]
Current task: implement_auth
State: refactor_in_progress
Locked: src/auth.js

Agent>
I see refactoring is in progress.
I'll wait for completion before testing.
```

### Signaling Completion
```md
User> Complete task and signal
Agent>
Task completed. Signaling...

#SIGNAL:task_complete
signaled

Other agents waiting on this condition will now proceed.
```

## 12. Version Info

### Current Version
- Agent: v1.1.0
- Protocol: v1.1
- Features: core, state, coordination

### Compatibility
- Works with orchestrator v1.0+
- Degrades gracefully if orchestrator lacks coordination
- All core commands (v1.0) always supported

### Feature Detection
```md
User> #VERSION
Agent>
v1.1.0

User> #SUPPORTS:coordination
Agent>
true

User> #HELP
Agent>
• context: #ASK #DEFINE
• state: #STATE:*
• coord: #WAIT #SIGNAL
• info: #VERSION #HELP

User> #HELP:state  
Agent>
• save:<k>:<v> - persist
• load:<k> - retrieve
• list - show keys
• clear - reset all
```

## 13. Checkpoint Awareness

### Agent Checkpoint Support
Agents receive checkpoint notifications:
```md
[From orchestrator]
#CHECKPOINT:notify:cp_001:pre_refactor

Agent>
ack:checkpoint:cp_001

[Agent tracks its changes relative to checkpoint]
#STATE:save:changes_since_cp001:auth.js,config.json
```

### Rollback Handling
When rollback occurs:
```md
[From orchestrator]  
#ROLLBACK:notify:cp_001

Agent>
• Clearing local state
• Discarding changes since cp_001
• Ready for retry
```

## 14. Dynamic Responses

### Limit Modifiers
- `:brief` - Minimal response
- `:detailed` - Extended response  
- `:limit=N` - Exact token count

### Usage Examples
```md
User> #ASK:current_structure:brief
Agent>
• src/
• test/

User> #ASK:auth_flow:detailed
Agent>
• OAuth2 init at /auth/login
• Provider redirect with state
• Callback validates tokens
• JWT issued, stored in Redis
• Refresh flow via /auth/refresh
• Expiry: 15min access, 7d refresh

User> #SUMMARY:project:limit=25
Agent>
Payment processing API with OAuth2 auth, 
handles transactions via Stripe integration.
```

### Smart Brevity
When :brief, prioritize:
1. Most recent/relevant
2. Errors/warnings first
3. Skip successful/routine

## 15. Context Awareness

### Receiving Context
When orchestrator provides context:
```md
#CONTEXT:receive
→ Project: PaymentAPI
→ Task: implement auth
→ State: 12 keys loaded
→ context:loaded
```

### Working with Inherited Context
Agent automatically has access to:
- Persistent state from previous session
- Current task and progress
- Project configuration
- Recent error patterns

This enables seamless work continuation even though each agent invocation is stateless.
