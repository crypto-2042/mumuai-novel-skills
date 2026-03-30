# OpenClaw Single-Book Team Guide

Chinese version: [openclaw-multi-agent-guide.zh-CN.md](openclaw-multi-agent-guide.zh-CN.md)

For exact operator procedures, use:

- [OpenClaw operations runbook](openclaw-operations-runbook.md)
- [OpenClaw operations runbook (Chinese)](openclaw-operations-runbook.zh-CN.md)

This guide describes how to run MuMuAINovel through OpenClaw with a dedicated agent team for one book. The default recommendation is:

- one team manages one `project_id`
- one agent owns one clearly scoped role
- one `MUMU_OWNER_ID` belongs to one agent session

Do not use one shared team to rotate across multiple books. It increases the risk of wrong-project actions, mixed reader feedback, and initialization state conflicts.

## Recommended Team Shapes

### Lite Team

Use this when release speed matters more than deep review specialization.

- `Showrunner`
- `Writer`
- `Chief Editor`
- `Reader`

### Standard Team

Use this when the book is already stable and you want stronger quality control without giving up cadence.

- `Showrunner`
- `Writer`
- `Chief Editor`
- `Lore Editor`
- `Pacing Editor`
- `Reader Panel`

## Runtime Rules

Every agent in the team should receive:

```bash
export MUMU_API_URL="https://your-mumu-host"
export MUMU_USERNAME="your-account"
export MUMU_PASSWORD="your-password"
export MUMU_OWNER_ID="book-a-showrunner"
```

Replace `MUMU_OWNER_ID` per agent. Example:

- `book-a-showrunner`
- `book-a-writer`
- `book-a-chief-editor`
- `book-a-reader`

These IDs are used to avoid accidental takeover of `.mumu_runtime/` progress files when multiple OpenClaw agents share one checkout.

## Single-Book Workflow

### 1. Showrunner Initializes the Book

The `Showrunner` creates or binds the book, then drives initialization until the project is ready.

Recommended commands:

```bash
python scripts/bind_project.py --action create \
  --title "<Title>" \
  --description "<Plot>" \
  --theme "<Theme>" \
  --genre "<Genre>"
```

```bash
python scripts/bind_project.py --action advance --project_id <PROJECT_ID> --budget-seconds 90 --json
```

Use `advance` as the default initializer. It gives structured progress, approximate wait hints, and can return before a long-running stage is fully done.

### 2. Writer Extends Runway and Generates Chapters

Once the project is `ready`, the `Writer` is responsible for forward production:

```bash
python scripts/generate_outline.py --project_id <PROJECT_ID> --count 5
python scripts/materialize_outlines.py --project_id <PROJECT_ID>
python scripts/trigger_batch.py --project_id <PROJECT_ID> --style_id <STYLE_ID> --count 5
```

Important constraints:

- `generate_outline.py` extends the outline runway
- `materialize_outlines.py` generates chapter plans from outlines, then calls `create-chapters-from-plans` to create chapter slots
- `trigger_batch.py` only works when empty chapter slots already exist in the project

The `Writer` should not approve publication quality or final chapter rewrites unless the team is deliberately collapsing roles.

### 3. Editors Review Drafts

The `Chief Editor` owns the final quality gate:

```bash
python scripts/fetch_unaudited.py --project_id <PROJECT_ID>
python scripts/analyze_chapter.py --project_id <PROJECT_ID> --chapter_id <CHAPTER_ID>
python scripts/review_chapter.py --project_id <PROJECT_ID> --action approve --chapter_id <CHAPTER_ID>
python scripts/review_chapter.py --project_id <PROJECT_ID> --action rewrite --chapter_id <CHAPTER_ID> --content "<Full rewritten chapter text>"
```

`fetch_unaudited.py` currently reads the full chapter list and highlights likely review candidates. It is not a strict server-side unaudited inbox.

In the standard team:

- `Lore Editor` focuses on continuity, setting consistency, unresolved foreshadows, and system RAG findings
- `Pacing Editor` focuses on chapter hooks, momentum, exposition weight, and chapter-end conversion pressure

### 4. Readers Provide Audience Feedback

Reader agents must behave like real readers:

- only read known published or draft chapter content
- do not read hidden system state as if they were ordinary readers
- report confusion, boredom, excitement, character attachment, and drop-off points

In the lite team, a single `Reader` is enough. In the standard team, `Reader Panel` represents multiple reader personas and returns a merged readout for the editors.

## Role Boundaries

### Showrunner

- owns project creation, initialization, task routing, and quality escalation
- may inspect status anywhere in the pipeline
- should not become the default chapter rewriter for every chapter

### Writer

- owns outline expansion and batch generation
- should not publish chapters without editorial review
- should not change team-wide policy or project scope

### Chief Editor

- owns approve/rewrite decisions
- consolidates writer output, reader feedback, and specialist review
- can request rewrite loops before publication

### Lore Editor

- only in the standard team
- focuses on canon consistency and foreshadow integrity
- should not spend its time on generic pacing notes

### Pacing Editor

- only in the standard team
- focuses on chapter velocity, payoff spacing, cliffhangers, and readability under serial release pressure
- should not turn every review into worldbuilding debate

### Reader / Reader Panel

- provides user-side reading feedback, not system-side policy
- should not trigger generation scripts or final approval scripts

## Recommended Handoff Order

### Lite Team

1. `Showrunner` initializes and declares the project ready
2. `Writer` expands outlines and triggers chapter generation
3. `Chief Editor` fetches drafts and performs approve/rewrite decisions
4. `Reader` reports audience-side feedback for the next cycle

### Standard Team

1. `Showrunner` initializes and routes work
2. `Writer` generates runway and chapters
3. `Lore Editor` checks continuity risks
4. `Pacing Editor` checks serial readability risks
5. `Reader Panel` reports audience response
6. `Chief Editor` makes the final publish/rewrite call

## Task-Based Scheduling with OpenClaw Cron

The recommended OpenClaw operating model is task-based, not long-lived staffed agents. Use cron jobs to wake up the right role, let it perform bounded work, then exit.

Recommended jobs:

### 1. `showrunner-scan`

- suggested cadence: every 30 minutes
- owner identity: `book-a-showrunner`
- purpose:
  - confirm the project is still `ready`
  - decide whether the book should keep serializing
  - decide whether to wake `Writer`, `Chief Editor`, or `Reader Panel`

This should be the only scheduling job that makes high-level continuation decisions.

### 2. `writer-run`

- owner identity: `book-a-writer`
- trigger conditions:
  - outline runway is low
  - there are not too many unaudited chapters waiting
  - recent reader feedback is not clearly negative
- allowed actions:
  - `generate_outline.py`
  - `materialize_outlines.py`
  - `trigger_batch.py`

### 3. `editor-run`

- owner identity: `book-a-chief-editor`
- trigger conditions:
  - review candidates exist in the chapter list
- allowed actions:
  - `fetch_unaudited.py`
  - `analyze_chapter.py`
  - `review_chapter.py`

### 4. `reader-panel-run`

- owner identity: `book-a-reader` or `book-a-reader-panel`
- trigger conditions:
  - new readable chapters exist
  - retention quality appears to be weakening
- allowed actions:
  - read known chapter content
  - report whether serialization should continue, slow down, or pause for fixes

### Serialization Decision States

`Showrunner` should treat the book as being in one of these states:

- `continue`
  - feedback is healthy enough to keep current release cadence
- `slow_down`
  - feedback is mixed, quality is unstable, or editorial backlog is growing
- `pause_and_fix`
  - feedback is clearly negative or quality regressions are repeating

Do not configure cron to blindly publish on a fixed rhythm. Cron should wake the team up to inspect state, then the team should decide whether to continue production.

Additional notes:

- `check_foreshadows.py` reads the `pending-resolve` queue, not the full set of stored foreshadows
- a newly added foreshadow may not appear there immediately if it is not yet pending resolution in the current chapter context

## OpenClaw Deployment Notes

- Start from `clawhub install mumuai-novel-skills`
- Treat the skill as one shared toolbox, but treat each agent identity as distinct through `MUMU_OWNER_ID`
- Keep one OpenClaw team directory or config block per book when possible
- If you must share one checkout, never reuse the same `MUMU_OWNER_ID` across agents
- Prefer the provided team templates under `examples/openclaw/` instead of inventing role prompts from scratch

## Template Entry Points

- [Lite SOUL (EN)](../examples/openclaw/single-book-team-lite/en/SOUL.md)
- [Lite SOUL (ZH)](../examples/openclaw/single-book-team-lite/zh-CN/SOUL.md)
- [Standard SOUL (EN)](../examples/openclaw/single-book-team-standard/en/SOUL.md)
- [Standard SOUL (ZH)](../examples/openclaw/single-book-team-standard/zh-CN/SOUL.md)
- [Cron scheduling example (EN)](../examples/openclaw/cron/README.md)
- [Cron scheduling example (ZH)](../examples/openclaw/cron/README.zh-CN.md)
