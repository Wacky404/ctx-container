# Natural Language Orchestration Guide

## Overview

You can interact with the orchestrator using natural, conversational language. The system will handle all protocol commands internally while responding to you in plain English.

## Getting Started

Simply describe what you want to accomplish. The orchestrator will:
- Understand your intent
- Coordinate the appropriate agents
- Track progress automatically
- Report back in clear language

## Common Requests

### Development Tasks

**Natural Language** → *Internal Protocol*

"Can you implement user authentication?" → `#DELEGATE:DevAgent:implement_auth:P2`

"Add OAuth support to the login system" → `#DELEGATE:DevAgent:add_oauth_login:P1`

"Fix the critical bug in the payment processor" → `#DELEGATE:DevAgent:fix_payment_bug:P0`

"Refactor the database connection module" → `#DELEGATE:DevAgent:refactor_db_module:P2`

### Testing Requests

"Write tests for the new API endpoints" → `#DELEGATE:TestAgent:test_api_endpoints:P1`

"Can you check test coverage?" → `#EVALUATE:test_coverage`

"Run the integration tests" → `#DELEGATE:TestAgent:run_integration_tests:P2`

### Status & Progress

"What's the current status?" → `#REPORT:all:progress`

"Show me what everyone is working on" → `#REPORT:all:current_tasks`

"Are there any errors?" → `#REPORT:all:errors`

"How's the authentication implementation going?" → `#REPORT:DevAgent:auth_progress`

### State Management

"Save our current progress" → `#CHECKPOINT:create:manual:progress_save`

"Create a backup before we continue" → `#CHECKPOINT:create:manual:pre_continue`

"Go back to before the refactor" → `#ROLLBACK:<latest_refactor_checkpoint>`

"Remember this configuration for later" → `#STATE:save:user_config:<details>`

## Advanced Usage

### Viewing Internal Operations

Add these phrases to see protocol commands:
- "show protocol" - See the internal commands being used
- "with protocol" - Include protocol in responses
- "explain the protocol" - Learn about specific commands

Example:
```
You: "Can you implement login with protocol shown?"

Orchestrator: "[Protocol: #DELEGATE:DevAgent:implement_login:P2]
I'll implement the login functionality. Let me delegate this to the development agent."
```

### Switching Modes

- **To Protocol Mode**: "use protocol mode" or start commands with #
- **To Natural Language**: "use natural language" (default)

### Priority Hints

The orchestrator infers priority from your language:
- "urgent", "critical", "ASAP" → P0 (Critical)
- "important", "high priority" → P1 (High)
- "when you can", "low priority" → P3 (Low)
- Default → P2 (Medium)

## Learning the Protocol

### Progressive Learning

Ask the orchestrator to teach you:
- "Show me how the protocol works"
- "Explain what you're doing internally"
- "Teach me the commands"

### Protocol Basics

The protocol uses structured commands:
- `#DELEGATE` - Assign tasks to agents
- `#REPORT` - Get status updates
- `#STATE` - Save/load information
- `#CHECKPOINT` - Create restore points
- `#ROLLBACK` - Undo changes

## Tips for Effective Communication

1. **Be Clear**: Describe what you want to achieve
2. **Add Context**: Mention relevant details
3. **Specify Priority**: Use words like "urgent" when needed
4. **Ask Questions**: The orchestrator can explain its actions

## Examples

### Simple Task
```
You: "Can you add input validation to the user registration form?"

Orchestrator: "I'll add input validation to the registration form. Let me have the development agent implement this for you."
```

### Complex Request
```
You: "We need to urgently fix the authentication system - users can't log in. After it's fixed, make sure we have tests to prevent this from happening again."

Orchestrator: "I understand this is critical. I'll immediately:
1. Have the dev agent fix the authentication issue (high priority)
2. Once fixed, have the test agent create comprehensive tests
Let me start with the urgent fix."
```

### Status Check
```
You: "How are things going with the payment integration?"

Orchestrator: "Let me check the payment integration progress. The development agent has completed 75% of the implementation. The Stripe webhook handlers are done, and they're currently working on the refund functionality."
```

## Troubleshooting

### If the orchestrator doesn't understand:
- Rephrase your request
- Be more specific about what you want
- Use the protocol directly with # commands

### To see what went wrong:
- Ask "What errors occurred?"
- Say "Show me the protocol log"
- Request "Explain the last failure"

## Protocol Mode

For power users, you can always use protocol commands directly:
```
#DELEGATE:DevAgent:implement_feature:P1
#REPORT:all:progress
#CHECKPOINT:create:manual:backup
```

This gives you precise control while bypassing natural language processing.

---

Remember: The orchestrator is here to help coordinate your development work. Communicate naturally, and it will handle the technical coordination details for you.