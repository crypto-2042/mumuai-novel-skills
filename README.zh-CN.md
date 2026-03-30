# MuMu OpenClaw Agent Skills

![License: GPL 3.0](https://img.shields.io/badge/License-GPL_3.0-blue.svg)
![Python](https://img.shields.io/badge/Python->=3.8-yellow.svg)
![Compatible](https://img.shields.io/badge/Compatible-OpenClaw%20%7C%20Codex-green.svg)

这是一个面向 [MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel) 的 **Agentic AI skills** 仓库，可供 [OpenClaw](https://github.com/openclaw/openclaw)、ClawHub、Codex、Claude Code 等运行时使用，用来完成长篇小说的初始化、扩纲、批量生成、审稿和重写。

English version: [README.md](README.md)

## 兼容性

| 运行时 | 状态 | 说明 |
| --- | --- | --- |
| OpenClaw / ClawHub | 直接支持 | `SKILL.md` 已包含 OpenClaw 元数据和环境变量声明。ClawHub 安装命令：`clawhub install mumuai-novel-skills` |
| Codex | 直接支持 | 仓库已采用 `SKILL.md` + supporting files 的 skills 组织方式 |
| Claude Code | 通过适配器支持 | 仓库内置 [.claude/agents/mumu-showrunner.md](.claude/agents/mumu-showrunner.md) |

## 快速开始

### 方法 A：通过 ClawHub 安装

```bash
clawhub install mumuai-novel-skills
```

运行时至少需要：

```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_API_URL="https://your-mumu-host"
export MUMU_USERNAME="your-account"
export MUMU_PASSWORD="your-password"
EOF
source ~/.zprofile
```

如果多个 agent 共用同一个工作目录，还应为每个 agent 设置唯一的 `MUMU_OWNER_ID`：

```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_OWNER_ID="novel-agent-a"
EOF
source ~/.zprofile
```

### 方法 B：在 Codex 中使用

1. 在 Codex 中选择 `Skill Installer`
2. 输入 GitHub 仓库地址：

```text
https://github.com/crypto-2042/mumu-openclaw-skills
```

3. 安装后重启 Codex
4. 安装 Python 依赖：

```bash
pip install requests
```

5. 将必要环境变量写入 `~/.zprofile`：

```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_API_URL="https://your-mumu-host"
export MUMU_USERNAME="your-account"
export MUMU_PASSWORD="your-password"
export MUMU_OWNER_ID="codex-agent-a"
EOF
source ~/.zprofile
```

6. 在 Codex 中直接调用这个 skill。

如果你的 Codex 运行环境支持 skill 本地持久化文件，并且你希望复用登录 cookies，也可以额外写入：

```bash
cat >> ~/.zprofile <<'EOF'
export MUMU_SESSION_FILE="/safe/writable/path/mumu-session.json"
EOF
source ~/.zprofile
```

### 方法 C：在 Claude Code 中使用

Claude Code 直接使用仓库中的 [.claude/agents/mumu-showrunner.md](.claude/agents/mumu-showrunner.md) 作为项目子代理适配层。

## 初始化流程

MuMuAINovel 的初始化是分阶段、长耗时流程。推荐顺序：

```bash
python scripts/bind_project.py --action create \
  --title "Project Title" \
  --description "Synopsis" \
  --theme "成长" \
  --genre "科幻"
python scripts/bind_project.py --action status --project_id <PROJECT_ID> --json
python scripts/bind_project.py --action advance --project_id <PROJECT_ID> --budget-seconds 90 --json
python scripts/bind_project.py --action ready --project_id <PROJECT_ID>
```

`advance` 是默认初始化入口。它会返回结构化的 `phase`、`subphase`、`message`、`recommended_wait_seconds` 和 `estimated_remaining_minutes`。这些时间字段只是经验提示，不是硬保证。

`status` 现在会尽量带上本地 runtime snapshot；如果你更关心当前阶段内部到底在做什么，优先看 `advance`。`wait` 超时后如果存在 runtime snapshot，也会返回与 `advance` 类似的运行态信息，而不只是基础 `wizard_step`。

## 多 Agent 说明

- `project_id` 和可选 `style_id` 必须视为 agent 自己的上下文，不要当成全局共享变量
- `.mumu_runtime/` 中的运行态文件是本地调度状态，不应被别的 agent 当作可接管状态
- 如果多个 agent 共用一个 checkout，必须为每个 agent 设置不同的 `MUMU_OWNER_ID`
- `advance` 是推荐的高层初始化入口，`status`、`resume`、`wait` 用于调试或手工控制

## OpenClaw 单书团队

OpenClaw 推荐采用 `single-book team = single project_id` 的模式，不要用一套团队轮转多本书。

- 精简版团队：`Showrunner`、`Writer`、`Chief Editor`、`Reader`
- 标准版团队：`Showrunner`、`Writer`、`Chief Editor`、`Lore Editor`、`Pacing Editor`、`Reader Panel`
- 每个 agent 都应有自己的 `MUMU_OWNER_ID`

详细操作手册：
- [OpenClaw 多 agent 操作手册（英文）](docs/openclaw-multi-agent-guide.md)
- [OpenClaw 多 agent 操作手册（中文）](docs/openclaw-multi-agent-guide.zh-CN.md)

可复用模板：
- [精简版模板（英文）](examples/openclaw/single-book-team-lite/en/SOUL.md)
- [精简版模板（中文）](examples/openclaw/single-book-team-lite/zh-CN/SOUL.md)
- [标准版模板（英文）](examples/openclaw/single-book-team-standard/en/SOUL.md)
- [标准版模板（中文）](examples/openclaw/single-book-team-standard/zh-CN/SOUL.md)

## 连载工作流

1. `Showrunner` 负责初始化、调度和是否继续连载的决策
2. `Writer` 负责扩纲，并在项目已经存在 chapter slots 时触发批量生成
3. `Chief Editor` 负责抓取整份章节列表中的待审候选、审稿、批准或重写
4. `Reader` 或 `Reader Panel` 只从真实读者视角给反馈

不要在项目还没 `ready` 时进入批量生成、审稿或重写流程。

当前已知限制：

- `generate_outline.py` 负责扩纲；若项目还没有 chapter slots，应继续运行 `materialize_outlines.py`
- `materialize_outlines.py` 按 MuMu Web 的真实两步流程处理：先生成 chapter plans，再调用 `create-chapters-from-plans` 创建章节槽位
- `trigger_batch.py` 启动后，可用 `check_batch_status.py --batch_id <BATCH_ID>` 查询进度
- `trigger_batch.py` 也支持 `--wait`，可在触发后直接轮询到完成或超时
- `fetch_unaudited.py` 读取的是完整章节列表，并高亮可能需要审阅的章节，不是严格意义上的服务端“待审 inbox”
- `check_foreshadows.py` 查看的是 `pending-resolve` 视图，不等于项目中的全部伏笔
