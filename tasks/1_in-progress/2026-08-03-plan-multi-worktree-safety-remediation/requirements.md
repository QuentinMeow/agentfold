# Requirements — Plan the multi-worktree safety remediation

Owner words only, verbatim and dated: an entry is appended and never edited, reordered, or
deleted. Interpretation lives in `task.md`; this task was filed before acceptance criteria
carried provenance labels, so its criteria stay as written.

## 2026-08-31 — chat

```text
/Users/quentinmiao/Documents/Codex/2026-08-30/ba/outputs/multi-agent-git-implementation-prompt.md check this,  as well as understand the current repo structure[$agent-orchestration](/Users/quentinmiao/code/dotagents/skills/agent-orchestration/SKILL.md)  use strongest agent teams to implement this, and also reason about the human workflow for collaborating with agents. Make sure you design for each common development cycle and create common usage scenario upfront, and let subagents verify they work in the end. You can work for as long as you want, even more than 10 hours are fine. Do whatever you need to unblock yourself. I'm able to answer questions for the first 6 hours. Go full auto after 6 hours. Make sure you reason about the plan and have detailed plans for verifying the results (let subagents search for harness testing and self evolved AI agents).

If you find current repo has problems, fix current repo first. Do the most correct way, finishing implementation is not a hard requirement, I want to do things right instead of done.

In the end, I want all progress in the form of PRs. You don't need backward compatibility, I only need the most correct final version in PRs.
```

## 2026-08-30 — the owner-supplied request document

```text
# 任务：用现成工具落地多 agent 的 Git 工作流

请在我的实际开发环境中落地一套可用的工作流。多个编码 agent 要能并行开发、查询彼此任务、中断后接续，并减少后续 PR 重复解决同一次重构冲突。请完成配置与验证，不要停在概念、选型报告或架构图。

目标仓库使用我提供的项目或当前明确的产品仓库。如果当前目录只是资料目录，或存在多个无法判断的项目，请先确认目标；不要把研究输出目录当产品仓库。

## 1. 先检查环境，再选择最小方案

读取仓库说明和 AGENTS.md，检查未提交改动、现有 worktree、活动会话、Git 远端、CI、工具版本与现有授权。保留用户正在进行的工作。

优先复用现有工具，只补缺失能力。不要自建调度器、任务数据库、文件锁服务或控制面板；现成工具没有覆盖的小缺口，才考虑薄脚本，并解释必要性。

以下是前期调查的候选，不是要求全部安装。能力来自官方文档，尚未做产品间兼容性实测，实施前核对当前版本：

- Vibe Kanban：workspace 对应独立 worktree / branch；配置其 MCP 后，agent 可查询 issues、依赖关系、workspaces 和 sessions。适合人分任务、agent 查询共享看板。
- Worktrunk：管理 worktree 的创建、切换、hooks 与清理，适合保留 CLI 工作方式。它本身不等于共享任务系统。
- Beads + MCP Agent Mail：Beads 管任务依赖、ready 与原子领取；Mail 管身份、消息和文件预约。需要所有会话连接同一协调后端。
- Graphite：管理 stacked PR（有父子依赖的 PR）和 restack（父分支变化后更新子分支基线）。依赖 PR 经常出现时再引入。
- Gas Town：已有派发、持久任务状态、邮箱、巡检恢复和 Refinery 合并队列。需要更高自治程度且能承担运维时才选。
- Conductor：另一个工作区管理选择，具有本地逐轮 checkpoints。若已在使用，不为更换界面而迁移。

默认先评估 Vibe Kanban + MCP + 已有 Git 远端 / CI；已有工作区工具能胜任时保留它。最后只采用一个主要工作区管理方式、一个任务状态来源和一个最终合并入口。不要让两套工具同时重写同一组分支。

用一小段话说明选择、复用项与缺口，然后在已有授权范围内继续实施，不因普通实现细节反复询问。

## 2. 必须落地的行为

### A. 编辑隔离

每个并行写任务有独立 worktree 和任务分支；同一 worktree 只有一个 writer。只读 review 可以并行。任务范围包含允许改动的路径，共享接口、迁移、lockfile 和公共重构有明确负责人。

端口、测试数据库和输出目录也要避免争用。worktree 不等于权限沙箱；git worktree lock 也不是文件写锁。需要强制隔离时使用环境已有的沙箱能力，不把提示词规则描述成强制控制。

### B. 任务彼此可见

使用选定工具的共享状态，不让每个 worktree 各维护一份独立 tasks.json。把任务 ID、owner、分支 / 目录、依赖、写入范围和交接记录映射到现有 issue / notes / 字段。

agent 在启动、恢复、扩大改动范围和交接前，查询最新任务与相关消息。不能仅展示一个人类可见的看板，就宣称 agent 已知道彼此。

自动领取任务时验证并发领取语义。文件预约冲突时，agent 应等待、协调或缩小范围；不能继续越界写入。区分任务领取、文件预约和操作系统写权限。

### C. 保存与中断恢复

在可恢复的小步骤完成、等待用户、切换上下文和 rebase / merge 前，由当前 writer 保存检查点。检查点包含代码提交与交接说明：已做、未做、测试结果、下一步、依赖变化。

在已授权远端上推送任务分支，确认远端 SHA 后才标记“已远端保存”。WIP 提交不代表可以合入主线。任务库 / 消息的备份与代码 push 分别落实。

不要用定时器在 agent 编辑过程中盲目 git add / commit。恢复时先确认旧 writer 已停止，保留原 worktree、未提交修改和日志，再让新会话接手；心跳过期不等于旧进程已停止。不得先 reset --hard、clean 或删目录。

明确三种恢复边界：进程退出、工作目录丢失、整台机器丢失。只能承诺恢复到实际保留或确认同步的状态，不能承诺零丢失。

### D. 减少重复合并冲突

公共重构优先作为前置 PR 合并，再从新基线启动依赖任务。不能让多个 agent 在各自分支重复实现同一重构，也不要把全局格式化混入功能 PR。

确实不能等待父 PR 时，使用明确的 stacked PR；任务依赖不自动等于 Git 分支依赖。父分支更新后，由指定 owner 在安全停顿点协调 restack，避免多个进程同时改写共享分支引用。

最终使用已有 merge queue，或一个集成负责人依次验证并合入。CI 必须检查最新主线与候选改动的组合，不能只看各分支单独的绿色结果。实际内容或接口冲突仍要修复并重新测试。

## 3. 实施时必须核对的工具边界

- Vibe Kanban MCP 面向本机客户端；跨机器使用要另行确认连接与状态共享。核对每个 agent profile 的接入和 project / issue 映射。
- 当前官方 Beads 使用 Dolt；embedded 与 server 模式的并发能力不同。Mail 安装器可能引入 Beads Rust（br）并创建 bd alias。核对实现、版本和实际数据库位置，不能混用旧 JSONL 教程或覆盖既有安装。
- Agent Mail 的文件预约是 advisory lease；Git guard 也不是任意文件写入的硬锁。核对所有 worktree 是否映射到同一个 Mail project identity，以及预约续期与释放流程。
- Graphite 1.8.4+ 通常跳过其他 worktree 正在检出的分支；相关目录需分别同步。sync / get 对 trunk 存在例外。实施前核对当前文档，并协调活动 writer；不要默认一个 agent 能替所有分支重写历史。
- Graphite 和 Gas Town 都使用 gt 命令；避免 PATH 指向错误工具。
- Conductor checkpoints 存在本地，不是连续或异机备份；restore 会撤销代码并删除相应后续对话。不能把它当作无损崩溃恢复按钮。
- GitHub merge queue 的必需 GitHub Actions 检查需覆盖 merge_group；核对仓库可用性和现有分支保护。

## 4. 用隔离试验验收，不拿真实工作做故障测试

使用可丢弃的试验仓库或独立试验任务，不修改生产分支，不停止用户已有会话。优先用两个实际 agent 会话验证；若只能模拟，明确哪些 agent 行为尚未实测。

1. 并行编辑：两个任务使用不同 worktree，分别写入；证明工作文件互不覆盖。再模拟范围重叠，验证选定的阻塞或协调机制，说明哪些约束只是协议。
2. 共享状态：两个会话查询到同一个任务、owner 和依赖；其中一个更新状态，另一个重新查询能看到。若采用自动领取，同一任务竞争时不能出现两个成功 owner。
3. 中断接续：暂停或结束你自己启动的试验会话。接手会话能定位原代码、未完成事项与下一步；另从已保存提交重建目录。说明各自恢复了什么、没恢复什么。同盘 bare remote 只能验证 Git 流程，不算异机备份。
4. 依赖 PR：建立公共变更 R 和依赖变更 B，修改 R，并验证 R 合并后 B 能接到正确基线。至少覆盖实际采用的合并策略；若用 squash，必须验证 squash 后的 restack。
5. 集成失败：构造单独通过、组合失败的候选，证明 CI / 队列会阻止其进入主线；修复后再次验证。

每项留下操作、观察结果、提交 / 分支证据与未验证范围。没有跑过就写“未验证”，不能用文档描述代替验收结果。

## 5. 交付与权限

交付实际配置、必要的最小脚本，以及一份简短操作手册。手册说明：人如何创建 / 暂停 / 接手任务，agent 如何查任务与保存，如何整合 PR，以及何时可以清理 worktree。

另附验收记录、恢复 / 回滚步骤，以及仍需用户完成的账号或权限操作。不要再次交付只有概念的架构报告。

按已有授权推进可回滚的项目内配置与隔离试验。需要新增付费服务、上传私有代码到新服务、修改全局环境或远端保护规则，而授权尚不明确时，先准备具体改动、风险和回滚方案，再集中询问。保留所有用户工作，不擅自覆盖既有指令。

## 原始资料

以下用于核对实现，不要求安装全部工具：

- Vibe Kanban MCP：https://www.vibekanban.com/docs/integrations/vibe-kanban-mcp-server
- Vibe Kanban workspace：https://www.vibekanban.com/docs/workspaces/creating-workspaces
- Worktrunk：https://worktrunk.dev/
- Beads：https://github.com/gastownhall/beads
- MCP Agent Mail：https://github.com/Dicklesworthstone/mcp_agent_mail
- Graphite 多 worktree：https://graphite.com/docs/multiple-worktrees
- Graphite restack：https://graphite.com/docs/restack-branches
- Gas Town：https://github.com/gastownhall/gastown
- Conductor checkpoints：https://www.conductor.build/docs/reference/checkpoints
- GitHub merge queue：https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue

研究背景：STORM 研究在写入时检测过期上下文；并发 agent PR 研究通过合并重放观察冲突。两者都不证明某个现成工具组合普遍最优，也不要求你复刻论文框架。

- STORM：https://arxiv.org/html/2605.20563v1
- 并发 agent PR 研究：https://arxiv.org/html/2607.04697v2
```
