# Process feedback

## 2026-05-01 — Scope of "blank line between bullet points" rule in MAP-GUIDANCE.md

> blank gaps are only for sentences that are likely to wrap and otherwise be hard to separate clearly.

Context: mid-map-build, drafting the **System (apt)** node. Just converted the apt inventory into a bullet list of single-token package names; observed that the blank-line-between-bullets convention (MAP-GUIDANCE.md content principles) makes short-item lists feel unnecessarily sparse.

Affects: MAP-GUIDANCE.md content principle currently reading "Blank line between bullet points for readability." Proposed scoping: blank gaps only when the bullets are sentence-shaped and likely to wrap; short-item lists (terms, names, single-word labels) sit tighter without gaps.

Captured retroactively — the observation predated the agent dir bump to 2026-05-01 (which introduced KEYWORDS.md formalising this protocol). Original handling was a direct edit to MAP-GUIDANCE.md, reverted at user request.
