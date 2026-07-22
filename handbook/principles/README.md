# Design principles (the constitution)

One file per principle. Each is self-contained — you can read any one alone. Together
they are the non-negotiable core of AgentFold; everything else in the repo is an
implementation detail that can change without touching these.

| Principle | One line |
|-----------|----------|
| [folder-as-a-service.md](folder-as-a-service.md) | Every folder is an independent service; its `AGENTS.md` is its API |
| [files-as-messages.md](files-as-messages.md) | All coordination is written to files; chat leaves no trace |
| [single-source-of-truth.md](single-source-of-truth.md) | Every fact has exactly one home; everything else links |
| [systems-over-instructions.md](systems-over-instructions.md) | Instructions are wishes; hooks, tests, and checks are guarantees |
| [eventual-consistency.md](eventual-consistency.md) | Assume agents are 50% reliable; design loops that converge anyway |
| [majority-over-single-agent.md](majority-over-single-agent.md) | Important judgments come from independent agents voting, not one agent asserting |
| [progressive-disclosure.md](progressive-disclosure.md) | Short core contracts, deep references loaded on demand |
| [design-for-forgetting.md](design-for-forgetting.md) | Memory that can't expire becomes noise; every entry has a review date |

Changing a principle: file a decision in `message-queue/needs-human/decisions/`, get a
human answer, record a superseding ADR in `memory/decisions/`, then edit.
