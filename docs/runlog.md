# Runlog

Newest first. One entry per working session: what changed, which issues it touched,
and what comes next. The CHANGELOG records what shipped; this records what happened.

## 2026-10-15 — Gloss review page, round two (#7, #8, #9)

Republished the tutor's "Gloss Check for Learners" page to the same URL, so her
link and the answers saved in her browser keep working. 700 rows refreshed from
the current glosses, ten re-opened with an Updated chip because their text changed
after she rated them, and a new "Your sentences" section with the thirteen examples
she chose or edited, for her to check the English we wrote for them.

Counting against the previous page: 33 rows changed, 10 of them never reviewed and
23 already carrying a verdict. Of those 23, thirteen are her own edits and seven
were already flagged, which leaves three that nobody had noticed — `encontrar`,
`deste` and `pegar`. Issue #8 said eight rows; the real number is ten.

Two small repairs on the way through: the Find box had never filtered anything, and
two offered sentences carried an undecodable byte from the corpus, which would have
shown as a black diamond on a card had she picked one. No published gloss is
affected.

## 2026-10-04 — Decision records, and a label for Jim's own tasks

Wrote the eleven decision records skipped during the adoption, one per paragraph of
the "Decisions" section of `docs/context-from-cowork.md`. Two are not settled and
say so rather than reading as decided: 0006 cannot confirm whether the reviewer was
offered named credit, and 0011 is open because Jim has not decided it (issue #15).
Only 0001 carries a date from the note itself; the rest say they are undated, with a
commit date from git history where one pins the decision.

Added the `jim` label and applied it to the ten issues only he can do — #7, #8, #9,
#12, #18 and the five questions — so `gh issue list --label jim` is his own list.

## 2026-10-04 — Adopted 2nd brain workflow

Added `PROJECT.md`, `CLAUDE.md`, this runlog and `docs/decisions/`, and set up
GitHub Issues for tracking: the seven type and priority labels, and issues #7-#21
covering the next steps and open questions carried over from the Cowork advisor.
Nothing existing was changed apart from four safety lines appended to `.gitignore`.
No decision records written yet; the template is in place for them.

The retired Cowork advisor's handover note was committed first, as
`docs/context-from-cowork.md` (commit `6799387`), with the links to Jim's claude.ai
pages removed because this repository is public.

Next: ask the tutor for her second pass on the 243 remaining top-500 gloss rows,
then fold her answers in before rebuilding the deck with glosses and tagging
v1.1.0.
