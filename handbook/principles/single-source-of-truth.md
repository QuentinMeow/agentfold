# Single source of truth

Every fact, schema, and rule lives in exactly one file. Every other place that needs it
links to that file. When data must exist in two places (a derived index, a vendored
copy), exactly one is canonical and the other is generated or checked against it
mechanically.

## Rules

- **Schemas live in `templates/`.** To document a file format, link its template; never
  restate the field list elsewhere. To change a format: change the template and the
  reconciler check in the same commit.
- **Status is location.** A task's status is the folder it sits in — there is no
  duplicate `status:` field to drift out of sync.
- **Derived data is labeled and regenerable.** `memory/index.md` is generated from the
  memory files; it says so in its header, and `reconcile.py --fix-index` rebuilds it.
  Never hand-edit a generated file — fix the source.
- **Duplication is a declared exception.** A deliberate copy (vendored module, mirror)
  must have a mechanical drift check; an unchecked copy is a bug.
- **No backward-compatibility aliases.** When something is renamed, every reference is
  updated in the same change. Old names don't linger "for safety" — the link check
  catches stragglers.

## Why

Agents forget and make mistakes — that's a design assumption, not a complaint. With one
source of truth, a mistake produces a *detectable inconsistency* (a broken link, a
failed drift check, an index mismatch) instead of two plausible-looking versions of the
truth where nobody can tell which is right. Detection plus the repair loop in
`eventual-consistency.md` turns forgetfulness into a self-healing system.
