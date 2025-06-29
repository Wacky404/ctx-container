# Quick Start: Agent Protocol Bootstrap

## For Orchestrator Role

```
Please read these protocol files:
- ./ctx/prompts/protocol/SharedProtocol.md
- ./ctx/prompts/OrchCtxPrime.md

Initialize as Orchestrator with:
- Git-based checkpoints enabled
- State management active
- Context import/export ready

Confirm with: "Orchestrator ready. Run #HELP for commands."
```

## For Agent Role

```
Please read these protocol files:
- ./ctx/prompts/SharedProtocol.md
- ./ctx/prompts/agentic/CtxPrime.md

Initialize as DevAgent with:
- State awareness from orchestrator
- Coordination support
- Brief response mode
```

## Quick Test

After initialization, test with:

```
#HELP
#STATE:save:test:working
#STATE:load:test
```

## Import Previous Session

```
#CONTEXT:import:./context/last_session.ctx
```
