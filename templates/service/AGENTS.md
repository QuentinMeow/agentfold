# <service-name>/ — agent contract

<One paragraph: what this service does and for whom. This file is the service's API
for agents — a stranger's agent should be able to work here from this file alone.>

## Verify changes

```bash
<the one command that proves this service still works, e.g. python3 -m pytest services/<name>/>
```

## Boundaries

- <what this service owns (files, data, decisions)>
- <what it must never do — imports across service lines, side effects, etc.>

## Depends on

- <other service> — <what for>; read `<link to that service's AGENTS.md>` and use only
  its declared interface.

## Endpoints (subfolders)

| Subfolder | What it is | Enter when |
|-----------|------------|------------|
| `<sub>/` | <one line> | <one line> |

## Local conventions

<Only rules specific to this service that an ancestor contract doesn't already state —
additive, never contradicting (`handbook/principles/folder-as-a-service.md`).>
