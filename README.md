# MuMu OpenClaw Agent Skills

![License: GPL 3.0](https://img.shields.io/badge/License-GPL_3.0-blue.svg)
![Python](https://img.shields.io/badge/Python->=3.8-yellow.svg)
![Compatible](https://img.shields.io/badge/Compatible-OpenClaw%20%7C%20Codex-green.svg)

This repository provides a set of highly automated **Agentic AI skills** allowing [OpenClaw](https://github.com/openclaw/openclaw), ClawHub, Codex, or Claude Code to manage and write entire novels using the [MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel) backend.

Chinese version: [README.zh-CN.md](README.zh-CN.md)

> **🌏 Designed for Deep World-Building**
> This skill set is heavily optimized for long-form fiction, specifically including structures typical of Chinese Web Novels (Wuxia, Xianxia, Cyberpunk, etc.). The prompt templates inside `SKILL.md` are instructed to handle deep Lore (RAG) and character arcs naturally.

## 📸 Demo In Action

![Agent Writing Novel](.github/images/banner.png)

With these skills, an agent transitions from being a simple text generator into a full **Showrunner/Editor-in-Chief**. It can maintain lore consistency, trigger background story-arc generation, read un-audited chapters, audit them using global memory RAG, and push massive rewrites.

## ✅ Compatibility

| Runtime | Status | Notes |
| --- | --- | --- |
| OpenClaw / ClawHub | Directly supported | `SKILL.md` contains OpenClaw metadata and required env declarations. ClawHub install command: `clawhub install mumuai-novel-skills`. |
| Codex | Directly supported | Codex supports skills and the Agent Skills open standard; this repo already follows the `SKILL.md` + supporting files pattern. |
| Claude Code | Supported via adapter | The repository includes a Claude Code project subagent adapter at `.claude/agents/mumu-showrunner.md`. |

## 📦 Directory Structure

```text
mumu-openclaw-skills/
├── README.md               # This documentation
├── SKILL.md                # System metadata & behavior injection for OpenClaw
├── .env.example            # Environment variables template
└── scripts/                # Core scripts for the agent
    ├── client.py           # Authenticated API Client with in-memory auth by default
    ├── bind_project.py     # Create / Link novel projects & Fix writing styles
    ├── generate_outline.py # Brainstorm & stream new outlines via SSE plot expansion
    ├── materialize_outlines.py # Turn outlines into chapter slots using the real MuMu flow
    ├── trigger_batch.py    # Trigger remote batch-generation when chapter slots already exist
    ├── check_batch_status.py # Query batch-generation task progress by batch_id
    ├── fetch_unaudited.py  # List all chapters and highlight likely review candidates
    ├── analyze_chapter.py  # Run RAG analysis vs existing continuity
    ├── review_chapter.py   # Final overwrite or immediate pass for draft chapters
    ├── check_foreshadows.py# Pull the pending-resolve foreshadow queue
    └── manage_memory.py    # Manually assert or reject memory nodes
```

## 🚀 Quick Setup

### Method A: Install via ClawHub (Recommended for OpenClaw Agents)
If you are using OpenClaw through ClawHub, install the published package directly:
```bash
clawhub install mumuai-novel-skills
```

After installation, make sure the runtime provides:
```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_API_URL="https://your-mumu-host"
export MUMU_USERNAME="your-account"
export MUMU_PASSWORD="your-password"
EOF
source ~/.zprofile
```

If you run multiple agents in the same shared workspace, also set a distinct owner ID per agent or session so runtime progress files are not mistaken for each other:
```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_OWNER_ID="novel-agent-a"
EOF
source ~/.zprofile
```

### Method B: Use in Codex

Install this skill directly inside Codex:

1. Open Codex and choose `Skill Installer`.
2. Paste the GitHub repo URL:
   ```text
   https://github.com/crypto-2042/mumu-openclaw-skills
   ```
3. Restart Codex so it picks up the new skill.
4. Install Python dependency:
   ```bash
   pip install requests
   ```
5. Write the required runtime env vars into `~/.zprofile`:
   ```bash
   cat >> ~/.zprofile <<'EOF'
   export MUMU_API_URL="https://your-mumu-host"
   export MUMU_USERNAME="your-account"
   export MUMU_PASSWORD="your-password"
   export MUMU_OWNER_ID="codex-agent-a"
   EOF
   source ~/.zprofile
   ```
6. Invoke the skill from Codex.

If your Codex environment supports skill-local persistent files and you want to reuse login cookies across calls, also add this to `~/.zprofile`:
```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_SESSION_FILE="/safe/writable/path/mumu-session.json"
EOF
source ~/.zprofile
```

### Method C: Use in Claude Code

Claude Code does not read OpenClaw skills directly. Its native extension points are project/user subagents and custom slash commands. This repository includes a ready-to-use project subagent adapter at `.claude/agents/mumu-showrunner.md`.

1. Open Claude Code in this repository so the project subagent is visible.
2. Export the runtime env vars before starting Claude Code:
   ```bash
   export MUMU_API_URL="https://your-mumu-host"
   export MUMU_USERNAME="your-account"
   export MUMU_PASSWORD="your-password"
   ```
   If multiple Claude Code agents may share the same workspace, also set:
   ```bash
   export MUMU_OWNER_ID="claude-agent-a"
   ```
3. In Claude Code, invoke the `mumu-showrunner` subagent for novel project initialization, batch generation, auditing, and rewrite flows.
4. If you want persistent login-cookie reuse across calls and your environment provides a safe writable path, also export:
   ```bash
   export MUMU_SESSION_FILE="/safe/writable/path/mumu-session.json"
   ```

### Method D: Manual Python Installation (For Standard Agents)

1. **Install Dependencies:**
   Because this skill conforms strictly to the OpenClaw standard, you can install the required dependencies manually:
   ```bash
   pip install requests
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env`, then export those variables into your shell before running the scripts.
   ```bash
   cp .env.example .env
   set -a
   source .env
   set +a
   ```
   *Note: OpenClaw can inject skill env vars directly, so `.env` export is mainly for manual shell usage. From version 1.0.6 onwards, agents are expected to memorize their `Project ID` and `Style ID` intrinsically and pass them via the `--project_id` and `--style_id` flags to support concurrent multi-agent executions in the same workspace. Login cookies are kept in-process by default; if your runtime provides a safe writable path, you can opt into persistence with `MUMU_SESSION_FILE=/safe/path/session.json`. If multiple agents share one workspace, set a distinct `MUMU_OWNER_ID` for each agent so `.mumu_runtime/` state files are not treated as reusable by another agent.*

## ⏳ Stage-Based Initialization

MuMuAINovel project initialization is a long-running, stage-based workflow. The `create` action no longer waits for world building, career system, characters, and outline generation to all finish in one blocking command.

Use the initialization actions like this:

1. Start project creation and the first stage:
   ```bash
   python scripts/bind_project.py --action create \
     --title "Project Title" \
     --description "Synopsis" \
     --theme "成长" \
     --genre "科幻"
   ```
2. Inspect current progress:
   ```bash
   python scripts/bind_project.py --action status --project_id <PROJECT_ID> --json
   ```
3. Recommended default agent entrypoint:
   ```bash
   python scripts/bind_project.py --action advance --project_id <PROJECT_ID> --budget-seconds 90 --json
   ```
   This returns structured `phase`, `subphase`, `message`, `recommended_wait_seconds`, and `estimated_remaining_minutes` fields. The ETA fields are approximate heuristics, not guarantees. On runtimes that support long-lived subprocesses, `advance` can return early while the current initialization stage continues in the background.
4. Resume the next initialization stage directly when you want lower-level control:
   ```bash
   python scripts/bind_project.py --action resume --project_id <PROJECT_ID>
   ```
5. Wait for readiness with a bounded timeout:
   ```bash
   python scripts/bind_project.py --action wait --project_id <PROJECT_ID> --timeout 60 --interval 5 --json
   ```
6. Check if initialization is fully complete:
   ```bash
   python scripts/bind_project.py --action ready --project_id <PROJECT_ID>
   ```

`status` now includes the local runtime snapshot when available. If you care about subphase-level progress, prefer `advance`. When `wait` times out and a runtime snapshot exists, it will return advance-style progress details instead of only the raw `wizard_step`.

Do not move on to batch generation, chapter auditing, or rewrite flows until the project reports `ready`.

## 🔀 Multi-Agent Notes

- `project_id` and optional `style_id` must be treated as agent-local memory, not global workspace state.
- Runtime initialization progress is written to `.mumu_runtime/` and is intentionally ignored by git.
- If multiple agents share one checkout, give each agent a distinct `MUMU_OWNER_ID`. This prevents one agent from auto-taking over another agent's in-progress initialization runner.
- `advance` is the recommended high-level initialization entrypoint. `status`, `resume`, and `wait` are lower-level controls for debugging or manual orchestration.

## 👥 OpenClaw Multi-Agent Setup

For OpenClaw, the recommended model is `single-book team = single project_id`. Do not run one shared team across multiple books.

- Lite team: `Showrunner`, `Writer`, `Chief Editor`, `Reader`
- Standard team: `Showrunner`, `Writer`, `Chief Editor`, `Lore Editor`, `Pacing Editor`, `Reader Panel`
- Every agent in the team should use its own `MUMU_OWNER_ID`
- Keep one team bound to one book, then clone the team template for the next book

Detailed operating guidance:
- [OpenClaw multi-agent guide](docs/openclaw-multi-agent-guide.md)
- [OpenClaw multi-agent guide (Chinese)](docs/openclaw-multi-agent-guide.zh-CN.md)

Reusable templates:
- [Lite team template (EN)](examples/openclaw/single-book-team-lite/en/SOUL.md)
- [Lite team template (ZH)](examples/openclaw/single-book-team-lite/zh-CN/SOUL.md)
- [Standard team template (EN)](examples/openclaw/single-book-team-standard/en/SOUL.md)
- [Standard team template (ZH)](examples/openclaw/single-book-team-standard/zh-CN/SOUL.md)

## 🤖 How the Agent "Lives" (Workflow)

If you are setting up an OpenClaw Agent, simply attach `SKILL.md` to its initialization prompt. The agent will execute following these guidelines:

### Phase 1: Creation & Binding
The AI creates a new fictional universe in multiple stages, securely pinning the resulting `project_id` into prompt memory context instead of a global `.env`.
```bash
# Example action the agent will run:
python scripts/bind_project.py --action create \
  --title "Cyber Dawn" \
  --description "A story about a rogue AI" \
  --theme "Survival" \
  --genre "Sci-Fi"
```

Then it keeps resuming initialization until the project is ready:
```bash
python scripts/bind_project.py --action status --project_id <Your ID> --json
python scripts/bind_project.py --action advance --project_id <Your ID> --budget-seconds 90 --json
python scripts/bind_project.py --action resume --project_id <Your ID>
python scripts/bind_project.py --action wait --project_id <Your ID> --timeout 60 --interval 5 --json
python scripts/bind_project.py --action ready --project_id <Your ID>
```

### Phase 2: The Writing Loop (Infinite Generation)
Once the novel is initialized and ready, the agent will loop the following cognitive steps ad-infinitum:

1. **Check Loose Ends:** 
   `python scripts/check_foreshadows.py --project_id <Your ID> --action list-pending`
   *Agent realizes a gun was shown in chapter 2 and hasn't fired yet.*

2. **Generate Plot Outlines:** 
   `python scripts/generate_outline.py --project_id <Your ID> --count 5`
   *This expands the story runway by creating outlines.*

3. **Materialize Chapter Slots:**
   `python scripts/materialize_outlines.py --project_id <Your ID>`
   *This follows the real MuMu Web flow: generate chapter plans from outlines, then create chapter slots from those plans.*

4. **Batch Write:** 
   `python scripts/trigger_batch.py --project_id <Your ID> --count 5`
   *Only use this when the project already has empty chapter slots.*
   *Add `--wait` if you want the command to poll until the batch completes or times out.*

5. **Check Batch Status:**
   `python scripts/check_batch_status.py --project_id <Your ID> --batch_id <Batch_ID>`

6. **Inbox Review:** 
   `python scripts/fetch_unaudited.py --project_id <Your ID>`
   *This reads the full chapter list and highlights likely review candidates. It is not a strict server-side unaudited inbox.*

7. **Approval or Execution:** 
   `python scripts/review_chapter.py --project_id <Your ID> --action rewrite --chapter_id <Chapter_ID> --content "<Full rewritten chapter text>"`
   *File input via `--file rewrite.md` is still available as a fallback when the runtime supports it.*

Known limitations:

- `check_foreshadows.py` reads the `pending-resolve` queue, not the full set of stored foreshadows.

## 📜 License
GPL-3.0 License. See the main MuMuAINovel project for more details.
