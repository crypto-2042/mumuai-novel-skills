# OpenClaw 单书团队操作手册

具体操作步骤请优先参考：

- [OpenClaw 运作手册（中文）](openclaw-operations-runbook.zh-CN.md)
- [OpenClaw 运作手册（英文）](openclaw-operations-runbook.md)

本文说明如何在 OpenClaw 中使用 MuMuAINovel 的单书团队模式。默认建议是：

- 一套团队只管理一个 `project_id`
- 一个 agent 只承担一个清晰的角色
- 一个 `MUMU_OWNER_ID` 只属于一个 agent 会话

不要让同一套团队轮转多本书，这样很容易出现错书操作、读者反馈串线、初始化状态冲突。

## 推荐团队编制

### 精简版团队

适合连载速度优先、审稿分工较轻的场景。

- `Showrunner`
- `Writer`
- `Chief Editor`
- `Reader`

### 标准版团队

适合已经进入稳定连载，需要更强质量控制但又不能牺牲节奏的场景。

- `Showrunner`
- `Writer`
- `Chief Editor`
- `Lore Editor`
- `Pacing Editor`
- `Reader Panel`

## 运行时规则

每个 agent 至少要拥有以下环境变量：

```bash
export MUMU_API_URL="https://your-mumu-host"
export MUMU_USERNAME="your-account"
export MUMU_PASSWORD="your-password"
export MUMU_OWNER_ID="book-a-showrunner"
```

`MUMU_OWNER_ID` 必须按 agent 区分，例如：

- `book-a-showrunner`
- `book-a-writer`
- `book-a-chief-editor`
- `book-a-reader`

这样做是为了避免多个 OpenClaw agent 共用同一 checkout 时，误把 `.mumu_runtime/` 里的状态文件当成自己可以接管的任务。

## 单书团队工作流

### 1. Showrunner 完成初始化

`Showrunner` 负责创建或绑定小说，并持续推进初始化直到项目 ready。

推荐命令：

```bash
python scripts/bind_project.py --action create \
  --title "<Title>" \
  --description "<Plot>" \
  --theme "<Theme>" \
  --genre "<Genre>"
python scripts/bind_project.py --action advance --project_id <PROJECT_ID> --budget-seconds 90 --json
```

`advance` 是默认初始化入口。它会返回结构化进度和大致等待建议，而且在支持长生命周期子进程的运行时中，可以前台先返回、后台继续跑当前阶段。

### 2. Writer 负责扩纲和生成

项目 ready 后，`Writer` 才进入生产：

```bash
python scripts/generate_outline.py --project_id <PROJECT_ID> --count 5
python scripts/materialize_outlines.py --project_id <PROJECT_ID>
python scripts/trigger_batch.py --project_id <PROJECT_ID> --style_id <STYLE_ID> --count 5
```

需要注意：

- `generate_outline.py` 负责扩纲
- `materialize_outlines.py` 会先生成 chapter plans，再调用 `create-chapters-from-plans` 创建章节槽位
- `trigger_batch.py` 只能在项目已经存在空章节槽位时工作

`Writer` 不负责最终发布判断，也不应该直接批准章节。

### 3. 编辑组负责审稿

`Chief Editor` 是最终质量闸门：

```bash
python scripts/fetch_unaudited.py --project_id <PROJECT_ID>
python scripts/analyze_chapter.py --project_id <PROJECT_ID> --chapter_id <CHAPTER_ID>
python scripts/review_chapter.py --project_id <PROJECT_ID> --action approve --chapter_id <CHAPTER_ID>
python scripts/review_chapter.py --project_id <PROJECT_ID> --action rewrite --chapter_id <CHAPTER_ID> --content "<Full rewritten chapter text>"
```

`fetch_unaudited.py` 当前会读取完整章节列表，并高亮可能需要审阅的章节，不是严格意义上的服务端待审 inbox。

标准版团队中：

- `Lore Editor` 专注设定一致性、伏笔和连续性风险
- `Pacing Editor` 专注节奏、钩子、灌水风险和章节结尾转化率

### 4. Reader 提供用户侧反馈

Reader 类 agent 必须像真实读者一样工作：

- 只读已经可见的章节内容
- 不把隐藏系统信息当作普通读者已知内容
- 反馈困惑、无聊、兴奋、角色喜爱度和弃读点

精简版用一个 `Reader` 即可，标准版则用 `Reader Panel` 汇总多个读者画像。

## 角色边界

### Showrunner

- 负责项目创建、初始化、任务路由和是否继续连载的决策
- 可以查看全链路状态
- 不应成为默认的逐章重写人

### Writer

- 负责扩纲和批量生成
- 未经编辑审稿，不应直接发布章节
- 不负责修改团队策略或项目范围

### Chief Editor

- 负责 approve/rewrite 的最终决定
- 汇总 Writer、Reader 和专项编辑的意见
- 可以要求返工后再发布

### Lore Editor

- 仅标准版团队使用
- 专注设定一致性、时间线、伏笔和系统 RAG 风险

### Pacing Editor

- 仅标准版团队使用
- 专注网文节奏、爽点密度、钩子和信息释放

### Reader / Reader Panel

- 只提供用户侧阅读反馈
- 不触发生成脚本，也不负责批准发布

## 推荐交接顺序

### 精简版团队

1. `Showrunner` 完成初始化并确认 ready
2. `Writer` 扩纲并触发章节生成
3. `Chief Editor` 抓稿并 approve/rewrite
4. `Reader` 输出下一轮读者反馈

### 标准版团队

1. `Showrunner` 初始化并路由任务
2. `Writer` 扩纲和生成
3. `Lore Editor` 检查设定风险
4. `Pacing Editor` 检查连载节奏风险
5. `Reader Panel` 汇总用户感受
6. `Chief Editor` 做最终发布或返工决定

## 用 OpenClaw Cron 做任务型调度

推荐采用任务型 agent，而不是长期常驻的“坐班式” agent。让 cron 定时唤醒合适的角色，做完有限工作后退出。

推荐的 4 个 job：

### 1. `showrunner-scan`

- 建议频率：每 30 分钟一次
- owner 身份：`book-a-showrunner`
- 作用：
  - 检查项目是否仍然 `ready`
  - 决定这本书是否继续稳定连载
  - 决定是否唤醒 `Writer`、`Chief Editor`、`Reader Panel`

它应当是唯一负责高层连载决策的调度任务。

### 2. `writer-run`

- owner 身份：`book-a-writer`
- 触发条件：
  - 大纲 runway 不足
  - 待审章节没有积压过多
  - 最近读者反馈没有明显恶化
- 允许动作：
  - `generate_outline.py`
  - `materialize_outlines.py`
  - `trigger_batch.py`

### 3. `editor-run`

- owner 身份：`book-a-chief-editor`
- 触发条件：
  - 完整章节列表中存在待审候选
- 允许动作：
  - `fetch_unaudited.py`
  - `analyze_chapter.py`
  - `review_chapter.py`

### 4. `reader-panel-run`

- owner 身份：`book-a-reader` 或 `book-a-reader-panel`
- 触发条件：
  - 有新的可阅读章节
  - 留存或反馈出现走弱迹象
- 允许动作：
  - 阅读已知章节内容
  - 给出继续连载、降速或暂停修整的建议

## 连载决策状态

`Showrunner` 应把书的状态归类为以下三种之一：

- `continue`
  - 反馈健康，可以保持当前连载节奏
- `slow_down`
  - 反馈一般、质量波动、审稿积压上升
- `pause_and_fix`
  - 反馈明显变差，或质量问题连续出现

不要把 cron 配成“固定到点自动发布”。cron 的职责是定时唤醒检查，再由团队决定要不要继续生产。

补充说明：

- `check_foreshadows.py` 读取的是 `pending-resolve` 视图，不等于项目中的全部伏笔
- 新增伏笔后，若暂未进入待回收集合，`check_foreshadows.py` 可能不会立即显示它

## OpenClaw 部署建议

- 从 `clawhub install mumuai-novel-skills` 开始
- skill 是共享工具箱，但 agent 身份必须通过 `MUMU_OWNER_ID` 隔离
- 最好每本书有自己的团队目录或配置块
- 如果必须共用一个 checkout，绝不要复用同一个 `MUMU_OWNER_ID`
- 优先从 `examples/openclaw/` 提供的模板开始，而不是从零写角色 prompt

## 模板入口

- [精简版 SOUL（英文）](../examples/openclaw/single-book-team-lite/en/SOUL.md)
- [精简版 SOUL（中文）](../examples/openclaw/single-book-team-lite/zh-CN/SOUL.md)
- [标准版 SOUL（英文）](../examples/openclaw/single-book-team-standard/en/SOUL.md)
- [标准版 SOUL（中文）](../examples/openclaw/single-book-team-standard/zh-CN/SOUL.md)
- [Cron 示例（英文）](../examples/openclaw/cron/README.md)
- [Cron 示例（中文）](../examples/openclaw/cron/README.zh-CN.md)
