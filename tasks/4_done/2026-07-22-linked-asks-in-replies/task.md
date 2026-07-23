# Surface needs-human items as clickable links plus context, never bare names

**Claimed-by:** claude (chat session)
**Mode:** async
**Filed:** 2026-07-22, by the repo owner (chat request, transcribed here — chat leaves no trace)
**Parent:** none
**Repository scope:** core

## Goal

Chat-given rule from the owner: when a handover or a session's final reply surfaces a
pending `needs-human/` item, never write a bare name ("pending decision: ABC"). Write a
clickable link to the queue file plus a few sentences of context, so the human can act
without hunting; the linked file then links onward to the deeper sources. The existing
texts (`templates/handover.md`, root `AGENTS.md` ritual step 4, the session-handover
skill) say "with links" but never pin this format, so a bare mention currently passes.

## Acceptance criteria

- [x] `templates/handover.md` "Needs your attention" specifies the format: clickable
      markdown link + 2–3 sentences of context, bare names banned
- [x] Root `AGENTS.md` ritual step 4 requires link + context and points at the
      template as the format's single source
- [x] `skills/session-handover/SKILL.md` step 6 matches
- [x] `automation/reconcile/reconcile.py --check` and `automation/run_tests.py` pass

## Links

- Chat request (this file is the transcription; chat leaves no trace)
- Format's canonical home after this task: `templates/handover.md`
