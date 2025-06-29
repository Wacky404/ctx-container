# Agent Protocol Summary v1.1

## Overview

A comprehensive protocol for orchestrating Claude-based agents with role-specific contexts, enabling complex software engineering workflows within Claude's session-based architecture.

## Core Concepts

- **Agents as Roles**: Each "agent" is a Claude invocation with specific prompting
- **Session-Based**: All state/coordination exists within orchestrator's conversation
- **Token-Efficient**: Every command optimized for minimal token usage
- **Git-Integrated**: Checkpoints and rollbacks use git for file safety

## Feature Categories

### 1. State Management

- `#STATE:save/load/list/clear` - Session-based key-value storage
- 20 keys max, 30 tokens per value
- Persistent marking for export: `:persistent`

### 2. Error Handling & Recovery

- `#ERROR` - Standardized error reporting
- `#RETRY` - Retry failed tasks with tracking
- `#ROLLBACK` - Git-based file restoration
- `#ESCALATE` - Critical issue escalation

### 3. Task Management

- `#DELEGATE` - Assign tasks with priorities (P0-P3)
- `#REPORT` - Status updates with token limits
- `#EVALUATE` - Assess metrics and progress
- Dynamic limits: `:brief/:detailed/:limit=N`

### 4. Multi-Agent Coordination

- `#LOCK/UNLOCK` - Resource exclusivity
- `#BROADCAST` - Event notifications
- `#WAIT/SIGNAL` - Dependency management
- `#COORDINATE` - Multi-role orchestration

### 5. Checkpoints & Rollback

- `#CHECKPOINT:create` - Git commit + state snapshot
- `#CHECKPOINT:list/diff` - View available checkpoints
- `#ROLLBACK` - Restore files and state
- Auto-checkpoint for risky operations

### 6. Version Management

- `#VERSION` - Protocol version checking
- `#SUPPORTS` - Feature detection
- Graceful degradation for older protocols
- Compatibility matrix included

### 7. Help System

- `#HELP` - Command discovery
- `#HELP:<category>` - Grouped commands
- `#HELP:<command>` - Detailed usage
- Context-aware suggestions

### 8. Session Health

- `#HEALTH:session` - Overall session metrics
- `#HEALTH:context` - Token usage monitoring
- Auto-export triggers at thresholds
- Guidance for session management

### 9. Context Export/Import

- `#CONTEXT:export` - Save session to file
- `#CONTEXT:import` - Resume from file
- YAML format for readability
- Filters: critical/tasks/state/all

### 10. Dynamic Responses

- `:brief` - 50% of default tokens
- `:detailed` - 200% of default tokens
- `:limit=N` - Custom token limit
- Smart defaults for different scenarios

## Protocol Files

### SharedProtocol.md

- Universal command definitions
- Core principles and syntax
- Version compatibility rules
- Best practices

### OrchCtxPrime.md

- Orchestrator-specific commands
- Multi-agent coordination
- Checkpoint strategies
- Session continuity

### CtxPrime.md

- Agent role context
- Lightweight command set
- State awareness
- Coordination support

## Key Innovations

1. **Session-Aware Design**: Built for Claude's ephemeral nature
2. **Git Integration**: Reliable file recovery without storing in memory
3. **Token Optimization**: Every response has defined limits
4. **Role-Based Architecture**: Clear separation of concerns
5. **Context Portability**: Work continues across sessions

## Usage Example

```md
# Start session with context

#CONTEXT:import:./context/project.ctx

# Check health

#HEALTH:session
→ Context: 15k/100k, State: 5/20

# Create checkpoint before risky operation

#CHECKPOINT:create:manual:pre_refactor

# Coordinate multi-role task

#LOCK:src/auth.js:600
#DELEGATE:DevAgent:refactor_auth:P0
#STATE:save:refactor_status:in_progress:persistent

# Handle failure

#ERROR:DevAgent:timeout
#ROLLBACK:pre_refactor
#RETRY:DevAgent:refactor_auth

# Export before ending

#CONTEXT:export:./context/session_final.ctx
```

## Benefits

- **Reliability**: Git-backed recovery, comprehensive error handling
- **Efficiency**: Token limits, smart brevity, context export
- **Scalability**: Handles complex multi-file projects
- **Continuity**: Work persists across sessions
- **Clarity**: Self-documenting with help system

## Limitations

- Coordination only within single orchestrator session
- No cross-conversation communication
- Context window still applies (100k tokens)
- State limited to 20 keys per session

This protocol enables sophisticated software engineering workflows while respecting Claude's architecture and constraints.
