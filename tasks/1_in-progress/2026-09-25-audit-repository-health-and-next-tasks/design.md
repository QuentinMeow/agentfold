# Design notes — Repository health and next-task assessment

**Status:** decided

## Problem

The repository's active roadmap and task status folders still describe merged work as pending. At the same time, the highest-priority multi-agent workflow has designed behavior that has not been demonstrated by its five required acceptance experiments. A maintenance pass needs to distinguish those facts from new implementation.

## Options considered

### Option A — Bounded factual repair with an evidence-based next sequence

Correct non-owner descriptive status, close only semantically completed tasks backed by merged code and real verification, and place the remaining work behind canonical queue actions. Existing safety defects receive focused future tasks with positive and negative controls.

### Option B — Fold the remaining workflow redesign into this audit

Implement continuity, publication, coordination and recovery changes together. These touch shared Git evidence and admission rules; combining them would hide which change actually fixes each failure and make independent verification harder.

## Chosen

Option A keeps the owner's goals and priority order intact. Four independent research contexts informed the selection; two isolated writers own roadmap correction and task closeout. Main owns this task, future-work records, generated indexes and the handover. No production code, schema, dependency, provider settings or principle changes are included. Reversal is an ordinary Git revert of the corresponding maintenance commit.

Historical test transcripts remain historical. Current validation includes the whole repository suite, reconciliation and three fresh-context reviews of the final diff. Provider status is evidence of landing, not a substitute for acceptance criteria.

## Scope and known limits

The continuity mutation defect remains owned by task `2026-09-04-judge-inherited-queue-mutations-on-their-real-edges`. The architecture reader found no recorded evidence for the five owner acceptance experiments or an operations manual. The test suite does not substitute for those experiments. Frozen human questions and the external-review authorization remain live and unchanged.

The task claim is published on this task branch. Automatic approval review rejected the repository convention's direct push of lifecycle commits to main; this run uses a pull request instead and does not bypass that rejection.
