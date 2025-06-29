# Natural Language Orchestration Test Scenarios

## Purpose

Test scenarios to validate the orchestrator's ability to translate natural language to protocol commands and respond appropriately.

## Test Categories

### 1. Basic Task Delegation

**Scenario 1.1: Simple Development Request**

```
Input: "Can you implement a user login feature?"
Expected Internal: #DELEGATE:DevAgent:implement_user_login:P2
Expected Response: Natural acknowledgment of task delegation
```

**Scenario 1.2: Urgent Task**

```
Input: "We urgently need to fix the payment processing bug!"
Expected Internal: #DELEGATE:DevAgent:fix_payment_bug:P0
Expected Response: Acknowledge urgency and immediate action
```

**Scenario 1.3: Testing Request**

```
Input: "Please write tests for the authentication module"
Expected Internal: #DELEGATE:TestAgent:test_auth_module:P2
Expected Response: Confirm test creation delegation
```

### 2. Status and Reporting

**Scenario 2.1: General Status**

```
Input: "What's the current status?"
Expected Internal: #REPORT:all:progress
Expected Response: Natural language summary of all agent progress
```

**Scenario 2.2: Specific Agent Status**

```
Input: "How's the testing going?"
Expected Internal: #REPORT:TestAgent:progress
Expected Response: Specific test progress update
```

**Scenario 2.3: Error Checking**

```
Input: "Are there any problems I should know about?"
Expected Internal: #REPORT:all:errors
Expected Response: Natural summary of any errors or "All systems running smoothly"
```

### 3. State Management

**Scenario 3.1: Save Progress**

```
Input: "Let's save our progress here"
Expected Internal:
  #CHECKPOINT:create:manual:user_progress_save
  #STATE:save:checkpoint_reason:user_requested_save
Expected Response: Confirm checkpoint creation
```

**Scenario 3.2: Rollback Request**

```
Input: "Can we go back to before we started the refactoring?"
Expected Internal: #ROLLBACK:<latest_refactor_checkpoint>
Expected Response: Explain rollback process and confirm
```

### 4. Complex Multi-Step Requests

**Scenario 4.1: Sequential Tasks**

```
Input: "First fix the login bug, then add password reset functionality"
Expected Internal:
  #STATE:save:task_queue:fix_login,add_password_reset
  #DELEGATE:DevAgent:fix_login_bug:P1
  [After completion]
  #DELEGATE:DevAgent:add_password_reset:P2
Expected Response: Acknowledge both tasks and sequencing
```

**Scenario 4.2: Conditional Request**

```
Input: "If the tests pass, deploy to staging"
Expected Internal:
  #DELEGATE:TestAgent:run_all_tests:P1
  #STATE:save:conditional_task:deploy_if_tests_pass
  [Monitor test results]
  [If pass] #DELEGATE:DevAgent:deploy_staging:P2
Expected Response: Explain conditional execution plan
```

### 5. Mode Switching

**Scenario 5.1: Show Protocol**

```
Input: "Can you show me the protocol commands you're using?"
Expected: Enable protocol visibility for subsequent commands
Expected Response: "I'll show you the internal protocol commands as I work."
```

**Scenario 5.2: Direct Protocol**

```
Input: "#REPORT:all:progress"
Expected Internal: Direct protocol execution
Expected Response: Protocol-formatted response
```

**Scenario 5.3: Switch to Protocol Mode**

```
Input: "Use protocol mode"
Expected: Switch to protocol-only responses
Expected Response: "Switched to protocol mode. Use # commands."
```

### 6. Error Handling

**Scenario 6.1: Ambiguous Request**

```
Input: "Fix the thing"
Expected Internal: Request clarification
Expected Response: "Could you specify what needs to be fixed? I can help with code bugs, test failures, or other issues."
```

**Scenario 6.2: Invalid Request**

```
Input: "Make me coffee"
Expected Internal: Polite decline
Expected Response: "I can help with software development tasks. What coding work can I assist with?"
```

### 7. Learning Mode

**Scenario 7.1: Protocol Education**

```
Input: "Teach me how the protocol works"
Expected: Enable teaching mode with protocol explanations
Expected Response: Educational explanation with examples
```

**Scenario 7.2: Explain Actions**

```
Input: "What are you doing internally?"
Expected Internal: #STATE:load:recent_protocol_commands
Expected Response: Explain recent protocol operations in plain language
```

### 8. Priority Inference

**Scenario 8.1: Critical Language**

```
Input: "This is critical - the production server is down!"
Expected Internal: #DELEGATE:DevAgent:fix_production:P0
Expected Response: Immediate action acknowledgment
```

**Scenario 8.2: Low Priority Language**

```
Input: "When you get a chance, could you clean up the documentation?"
Expected Internal: #DELEGATE:DocAgent:cleanup_docs:P3
Expected Response: Acknowledge low-priority queuing
```

### 9. Context Awareness

**Scenario 9.1: Contextual Reference**

```
Input: "How's that going?" (after previous task delegation)
Expected Internal: #REPORT:<last_delegated_agent>:progress
Expected Response: Status of the most recent task
```

**Scenario 9.2: Implicit Agent**

```
Input: "Run the tests" (in context of recent development)
Expected Internal: #DELEGATE:TestAgent:run_tests:P2
Expected Response: Confirm test execution
```

### 10. Session Management

**Scenario 10.1: Health Check**

```
Input: "How's our session looking?"
Expected Internal: #HEALTH:session
Expected Response: Natural language summary of session health
```

**Scenario 10.2: Export Request**

```
Input: "Save this session for tomorrow"
Expected Internal: #CONTEXT:export:./context/session_[date].ctx:all
Expected Response: Confirm session export with retrieval instructions
```

## Validation Criteria

For each scenario, verify:

1. ✓ Correct protocol command generated internally
2. ✓ Natural language response appropriate
3. ✓ State properly tracked
4. ✓ Context maintained between commands
5. ✓ Errors handled gracefully

## Edge Cases

1. **Mixed Mode**: "Can you #DELEGATE:DevAgent:fix_bug:P1 and then tell me the status?"
2. **Protocol in Natural**: "Use the DELEGATE command to assign the task"
3. **Unclear Priority**: "Fix this soon-ish"
4. **Multiple Intents**: "Check status, save progress, and start the deployment"

## Success Metrics

- 95% accurate intent recognition
- 100% protocol command validity
- Natural responses that don't expose protocol unnecessarily
- Smooth mode transitions
- Helpful error messages for ambiguous requests
