# Clawhub Runtime Compatibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the runtime assumptions that make this skill package fragile on clawhub-style platforms.

**Architecture:** Keep the existing script surface area intact where possible, but make the runtime stateless by default, accept rewrite content without requiring a temporary file, and harden network flows with explicit HTTP error handling and bounded polling. This minimizes user-facing churn while reducing platform-specific failures.

**Tech Stack:** Python 3, argparse, requests

---

### Task 1: Make authentication state platform-safe

**Files:**
- Modify: `scripts/client.py`

**Step 1: Write the failing test**

There is no test harness in this repository today. Use a manual red check instead:

1. Read `scripts/client.py`
2. Confirm session persistence writes to `.mumu_session.json` in the repo root
3. Confirm client initialization always attempts to read/write that file

**Step 2: Run the red check to verify the problem exists**

Run: `nl -ba scripts/client.py | sed -n '1,140p'`
Expected: `SESSION_FILE = Path(__file__).parent.parent / '.mumu_session.json'` plus file reads/writes.

**Step 3: Write minimal implementation**

Update `scripts/client.py` so that:
- Session-file persistence is opt-in, not default
- The default behavior keeps cookies only in-process
- `MUMU_SESSION_FILE` can enable a custom writable path when the runtime allows it

**Step 4: Run verification**

Run: `nl -ba scripts/client.py | sed -n '1,180p'`
Expected: no unconditional repo-root session-file writes remain.

### Task 2: Remove rewrite file dependency

**Files:**
- Modify: `scripts/review_chapter.py`
- Modify: `SKILL.md`

**Step 1: Write the failing test**

Manual red check:

1. Read `scripts/review_chapter.py`
2. Confirm rewrite mode requires `--file`
3. Read `SKILL.md`
4. Confirm the documented rewrite flow instructs the agent to create `rewrite.md`

**Step 2: Run the red check to verify the problem exists**

Run: `nl -ba scripts/review_chapter.py | sed -n '1,220p'`
Expected: rewrite path depends on `--file`.

Run: `nl -ba SKILL.md | sed -n '55,72p'`
Expected: rewrite instructions require `rewrite.md`.

**Step 3: Write minimal implementation**

Update `scripts/review_chapter.py` so that rewrite mode supports:
- `--content "<text>"`
- `--file <path>` as a fallback
- stdin when neither option is provided but input is piped

Update `SKILL.md` to recommend direct content input first and keep file-based usage as optional fallback.

**Step 4: Run verification**

Run: `python3 scripts/review_chapter.py --help`
Expected: rewrite help shows `--content` and `--file`.

### Task 3: Harden stream requests and polling

**Files:**
- Modify: `scripts/client.py`
- Modify: `scripts/generate_outline.py`
- Modify: `scripts/bind_project.py`
- Modify: `scripts/analyze_chapter.py`

**Step 1: Write the failing test**

Manual red check:

1. Read `scripts/client.py`
2. Confirm `post(..., stream=True)` returns before calling `raise_for_status()`
3. Read `scripts/analyze_chapter.py`
4. Confirm polling loop has no timeout

**Step 2: Run the red check to verify the problem exists**

Run: `nl -ba scripts/client.py | sed -n '75,110p'`
Expected: stream responses return without status validation.

Run: `nl -ba scripts/analyze_chapter.py | sed -n '19,40p'`
Expected: `while True` loop with no timeout budget.

**Step 3: Write minimal implementation**

Update the client and scripts so that:
- stream requests call `raise_for_status()` before returning
- SSE consumers explicitly close responses
- chapter analysis polling has configurable timeout and interval
- timeout failures explain what happened

**Step 4: Run verification**

Run: `python3 -m py_compile scripts/*.py`
Expected: exit code 0.

### Task 4: Clean user-facing output for agent platforms

**Files:**
- Modify: `scripts/fetch_unaudited.py`

**Step 1: Write the failing test**

Manual red check:

1. Read `scripts/fetch_unaudited.py`
2. Confirm full debug payloads are printed to stdout

**Step 2: Run the red check to verify the problem exists**

Run: `nl -ba scripts/fetch_unaudited.py | sed -n '14,34p'`
Expected: `DEBUG:` lines dumping response details.

**Step 3: Write minimal implementation**

Remove the debug output and keep only concise review-oriented chapter summaries.

**Step 4: Run verification**

Run: `nl -ba scripts/fetch_unaudited.py | sed -n '14,34p'`
Expected: no `DEBUG:` output remains.
