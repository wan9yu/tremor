---
name: audit
description: 周期审计 ritual, 3 mode 一套框架. waste (减法, 找"看似有用其实无用"的 code/doc/test/protocol) / drift (一致性, 跨 doc+code+protocol 找漂移) / strategic (整体 holistic critique). 触发 "/audit [mode]"; "减法"/"做减法"/"找该删的"→waste; "漂移审计"/"一致性审计"/"drift"→drift; "战略审计"/"整体审计"/"--strategic"→strategic; 无 mode = 问用户或全跑. 替代已合并的 /subtract + /drift-audit.
---

# /audit — 周期审计 ritual (waste / drift / strategic 三 mode 同框架)

waste + drift + strategic 三种审计共享同一套机器 (哲学 → verify-first → parallel 发现 → 主 thread 复核 → 分桶 → surface 给 stakeholder). 区别只在**扫哪组类** + **分哪种桶** + **fix 边界**. 本 skill 把共享机器写一次, class-set 按 mode 分。

## 哲学 (三 mode 共享)

> "The most expensive code is the code that looks useful but isn't."

代码库不停扩大, 死代码 / 过期 doc / premature SSOT / mirror-of 段 / 老协议遗留 / 数字漂移 不停累. 加容易, 删/对齐难 — 因为不确定 "是否还有人用 / 哪个才是真值". 本 skill 用**证据驱动 verify** 把不确定变成 yes/no, 让审计可执行。

**核心信念**:
1. **看似有用 ≠ 实际有用** (waste 主轴) — `grep -r consumer` 才知道; 大 ≠ waste
2. **Verify > 直觉** — 数字声称必查源, 抽象层必检 consumer 数, "missing" 必 ls 实证
3. **False-positive 比 false-negative 危险** — 删错代码 / 误报 drift 代价大于漏一个; gray area 默保守
4. **SSOT 向代码迁移, prevent > detect** (drift 主轴) — 检测漂移是 reactive, 改架构让漂移没空间是 proactive
5. **Surface impact + options 给 stakeholder, 不审计者拍** — 除 drift 的两个 AUTO-FIX 例外, 列 impact + 决策点给 owner, 不主动 fix
6. **协议层 stale 比代码 stale 危险** — agent boot 读 stale 协议会反复踩

## 何时召唤

仅在用户**明确要求**时执行 — **不主动跑**, 是 ritual, 用户拍节奏。建议 cadence: 每 50-100 commits OR minor version ramp-up 启时召唤一次 (strategic mode cost 大, quarterly / project pivot 才启, 推荐**新的独立 session** 避免上下文污染)。

| mode | 触发 | 扫什么 | 输出 |
|---|---|---|---|
| **waste** (减法) | `/audit waste` / `/audit` (default 含) / "减法" / "做减法" / "找该删的" / "找冗余" / "audit 浪费" | 6-8 类 A-H (dead code / stale doc / premature abstraction / dup content / over-eng / archive cruft / carved-out follow-up / outdated protocol) | 6-bucket 减法清单 |
| **drift** (一致性) | `/audit drift` / "漂移审计" / "一致性审计" / "drift audit" | 5 类 (doc↔code / code↔code 双源 / comment↔reality / SSOT 应迁 / 客户可见性 gap) | stakeholder 分桶 (AUTO-FIX + surface) |
| **strategic** (战略) | `/audit strategic` / `/audit --strategic` / "战略审计" / "整体审计" | systemic pattern + 增长 trajectory + 协议通胀 | holistic critique + 3-5 战略 options |

`/audit` 无 mode → 问用户要哪个 mode, 或按需 all (waste+drift 跑, strategic 单独因 cost 大). 可加 scope: `/audit waste code` / `/audit drift customer` (见各 mode 详情)。

## 模式

### waste (减法)

找"看似有用其实无用"的 8 类。每类 1 行摘要, 详细 verify bash + KEEP signal + action 见 **`references/waste-classes.md`**:

- **A. Dead code** — 函数/类/模块 zero consumer (rg symbol count = 1)。KEEP: entry point / compose / CI / 用户面 agent 命令。
- **B. Stale doc** — last_verified 过期 / 版本停 N-2 / 引用废弃 API / 描述与 code 行为差。KEEP: IMMUTABLE / blueprint / 协议。
- **C. Premature abstraction** — SSOT helper / shared module 只 1 处 import。Action: inline 回 single consumer。
- **D. Duplicate content** — mirror-of 注释存在但仍 copy-paste / zh-en pair drift。Action: 删 mirror 留 pointer。
- **E. Over-engineering** — 防御 N 层但 threat model 不清 / 0 trip in N 月。KEEP: 故意的 7-layer safety net / 竞态防护。
- **F. Archive cruft** — >60 day 0 inbound link 0 grep ref。Action: git rm (history 兜底)。
- **G. Carved-out follow-up 未立** — close 时承诺 #X-b 但 issue 不存在。Action: 立**当前** milestone Sand (不 defer)。
- **H. Outdated protocol** — team_agreements 内部 self-contradict / _common.md 含废止指令。Action: 删老段, 不留 banner。

scope: `/audit waste code` → A+C+E; `waste doc` → B+D+F; `waste protocol` → G+H; 默认 all 8。

### drift (一致性)

找 doc+code+protocol 跨源不一致的 5 类。每类 1 行摘要, 详细 verify bash 见 **`references/drift-classes.md`**:

- **类 1: doc↔code** — doc 字面抄 "N 类 X" / "v1.X" / API signature, code 是 SSOT 但抄了 stale 值。
- **类 2: code↔code 双源** — 同 fact 2+ 代码处独立维护, 缺 invariant 守门。
- **类 3: comment↔reality** — "see X" / 参见 Y 但 X 不存在 / Y 已 rename / broken md cross-ref。
- **类 4: SSOT 应迁候选** — doc 手抄 build artifact / 静态值, 应改 build-time inject 或 pointer (不强推)。
- **类 5: 客户可见性 gap** — 客户面 doc 声明 feature/behavior, 代码已 ship 别的。

scope: `/audit drift customer` / `dev` / `agent-boot` / `ssot-migration` 各限对应桶。

### strategic (战略)

整体 holistic critique — AI 角色 = architect 而非 auditor。整 repo 必扫 (不可 scope-select), context budget 15-30% 典型。5 sub-agent 扫 systemic pattern + 主 thread cross-cutting synthesis。output = TL;DR (≤3 句) + Growth Trajectory + 3-5 Systemic Root Causes + What's Working + Case Studies + 3-5 战略 Options (含"接受 by-design") + What I Did NOT Touch。tactical 不查的系统 lens: 增长 trajectory / SSOT 迁移面 / 协议复杂度通胀。详见 **`references/strategic-mode.md`**。

## 执行流程 (5 phase — 三 mode 共享同一套机器)

### Phase 1: Scope 选 (定 mode + class-set)

按上表定 mode → 定扫哪组类 (waste A-H / drift 类1-5 / strategic systemic)。有 scope arg 则缩小 class-set / bucket。

### Phase 2: 候选发现 (parallel sub-agent 委托)

分路 sub-agent 并行扫 (waste 3 路 per 类组合 / drift 5 路 per 类 / strategic 5 路 per systemic pattern)。每 agent return:
- raw findings (file:line + 一句 evidence + verify command)
- agent self-verify status
- ≤ 400 字 / agent

委托提示词必含:
- "**只给 raw findings**, 不 cherry-pick 不分桶不建议 fix"
- "**每 finding 必含 file:line + grep count / git log age / cross-check 实测命令输出**"
- "**verify status 语义** (不歧义):"
  - "✓ **confirmed**: waste=zero-consumer/stale 实证 · drift=doc 抄写值 vs SSOT 不一致 实证"
  - "⚠ **unverified**: 候选但未充分 cross-check, 主 thread 复核"
  - "✗ **verify-failed / false-positive**: 进一步实证 claim 不成立 (仍有 consumer / doc 与 SSOT 实际一致)"

### Phase 3: 主 thread verify (high-stakes findings)

agent 报 confirmed 不直接信。抽样 verify (per memory `feedback_spec_doc_must_grep_ssot_first` + 哲学信念 2/3):
- 任何 "≥ N 例" / 数字声称 → grep 数实证
- 任何 "missing" / "缺 invariant" 声称 → ls / find / grep test files 实证
- 任何 "single consumer" 声称 → rg 实证
- 任何 "breaking change" / "broken cross-ref" 声称 → run / test / ls path 实证
- verify 时 quote SSOT 原文, 别转述

历史 baseline: audit false-positive rate ~15-20% (waste 立时实证 3/16 = 19%: #546 已 closed 非 future / 累 ≥3 例实际 1-2 / since-version 注解误读为 pin)。**必标 verify-failed** — false-positive 是一等输出, 不是隐藏项。

### Phase 4: 分桶输出 (mode-dependent)

**waste → 6 桶**:
- **DELETE-CONFIRM** (立即可删, 用户拍即 git rm) — file:line | 证据 | 命令
- **MERGE-PROPOSE** (合并到 X) — source files | target SSOT | est 行数收益
- **SIMPLIFY-PROPOSE** (删抽象层) — helper path | consumer count | inline 路径
- **KEEP-EXPLICIT** (看似可删实 load-bearing) — file | 为什么留 | 标记防下次再审
- **DISCUSS** (用户拍方向) — gray area | 候选 action | 风险
- **VERIFY-FAILED** (claim 不成立) — claim | 实际状态 | 误判类型

**drift → stakeholder 桶** (判桶: file 路径 in customer-facing list → customer; in agent-boot list [prompts/*.md, AGENTS.md, role prompts] → agent-boot; in protocol list → protocol; in tests/ 或 code/ 且双源 → code↔code SSOT; 其他 doc → dev internal; "应迁候选" → SSOT-迁移):
- 🤖 **customer-facing** (user-guide / first-install / integrations / README / website) — AUTO-FIX
- 🤖 **agent-boot** (boot prompts / AGENTS.md / 入口索引 / role prompts) — AUTO-FIX
- 👥 **dev internal** (engineering / process / dev notes) — surface, 等 dev/QA
- 👥 **protocol** (team agreements / boot rules / 决策档案) — surface, 等用户拍
- 🏗️ **code↔code SSOT 双源** — surface, dev 决策 (options: 立 invariant / 收单源 / 接受)
- 💭 **SSOT 应迁候选** — surface, architect/lead 决策 (options: build-time inject / pointer / generator / 不动)
- ✗ **false-positive** — audit drift claim 实证不成立

每 surface finding 出: **Impact** (谁受影响 + 影响实例) + **≥3 options** (含"不动" 合法) + **Decision owner** + **1 句 recommendation hint (明示不强推)**。

**strategic** → 见 `references/strategic-mode.md` output 格式 (非分桶, 是 holistic critique)。

### Phase 5: Ship path (mode-dependent fix 边界)

- **waste**: **不立卡, 不主动 git rm / Edit** — 默认 markdown 报告 only, 用户拍 ship 路径 (直推顺手 commit **当前** milestone / 立 Sand 卡 / 不动标 KEEP-EXPLICIT)。减法是 high-stakes 必用户审视。
- **drift**: **AUTO-FIX 仅两桶 (customer-facing + agent-boot)** — 直接 Edit, commit body 段:
  ```
  audit(drift) AUTO-FIX:
  - file:line
  - drift evidence: <count vs SSOT / version mismatch>
  - fix applied: <inline 改动>
  - SSOT 来源: <code SSOT path>
  ```
  例外理由: customer 商业敏感 + 读 stale 直接体验受损必 fix; agent-boot 不能给 feedback, auditor 代决。**其他所有桶 surface only, 不动文件** — internal/protocol/SSOT-双源/应迁 是 stakeholder 决策点, 不 auditor 越权代决。
- **strategic**: 报告 only, 3-5 战略 options 给用户拍, What I Did NOT Touch 明示。

## 风格要求 / 不做的事

- **数字 lead, 不靠形容词** — "snapshots-archive/2026-04 90 文件 0 inbound link" / "argus-redact doc 0.4.2 vs pyproject 0.6.5", 不是 "累积过多" / "漂得厉害"
- **Verify status 必标** — 每 finding ✓ confirmed / ⚠ unverified / ✗ verify-failed
- **False-positive rate footer 必出** — "扫 N findings, verify pass M (X%)", 累 ≥ 20% 调 sub-agent prompt
- **保守倾向** — gray area 默 KEEP-EXPLICIT (waste) / surface (drift), 不误删不越权 AUTO-FIX
- ❌ **不主动 git rm / delete** — 唯二例外是 drift 的 customer-facing + agent-boot AUTO-FIX
- ❌ **不下推 milestone** — 真问题立**当前** milestone (per memory `feedback_audit_followup_default_current_milestone`)
- ❌ **不出 100-pt 总分** — 审计是 actionable 清单/诊断, 不是评分
- ❌ **不基于"代码量大"声称 waste** — 大 ≠ waste, 单 file 1500 行可能是合理 epic
- ❌ **不替代 commit-time invariant** — invariant 是 hard-gate; 本 skill 找 invariant 缺位候选, 不立 invariant

## 与其他 skill 区分

| skill | scope | trigger | output |
|---|---|---|---|
| `/simplify` | git diff changed files | post-edit / PR 内 | inline 修复 (code reuse / quality / efficiency) |
| `docs-sync` | docs/ + website/ 全 doc tree | 周期 | 漂移 fix + auto-rewrite |
| `/uspi-score` | 4 metric 项目节奏 | on-demand | 决策驱动 traffic-light |
| `static-ssot-audit` | static value SSOT | 周期 | 数字 drift fix |
| **`/audit waste`** | 全 repo (code+doc+test+protocol) | 周期 ritual | 减法清单 (delete/merge/simplify) |
| **`/audit drift`** | 全 repo (doc+code+protocol) | 周期 ritual | 一致性报告 (AUTO-FIX + surface 分桶) |
| **`/audit strategic`** | 整 repo | quarterly / pivot | holistic critique + 战略 options |

边界: `/simplify` 看新写 quality (per-PR inline); `/audit` 跨整 repo 周期。waste 找"该删", drift 找"该一致" — 不重叠。`/audit` 找 invariant 缺位候选但**不立 invariant** (surface 给 dev)。

## 改进迭代 (本 skill 自身)

每次召唤后跟踪: false-positive rate (多少 verify-failed) / 用户实际删/改了多少 vs KEEP-EXPLICIT (定 ROI) / AUTO-FIX 误改率 (push 后又改回) / surface 决策 turnaround / bucket 命中分布 (某 bucket 长期 0 → prompt 删该桶路径; dominant → 拆 sub-bucket)。累 ≥5 次同类 false-positive → 该类 sub-agent prompt 改或删。用户提"漏了 X / 错杀 Y" → update 本 SKILL.md class 列表。

## 历史

- **2026-07-05 合并**: `/subtract` + `/drift-audit` 两 skill 合并为 `/audit` 带 mode arg — 二者共享 ~identical 5-phase 机器 (Scope → parallel sub-agent 发现 → 主 thread verify → 分桶 → surface-not-auto-fix), 各自维护一份近重复 copy。合并写共享机器一次, class-set 按 mode (waste A-H / drift 类1-5 / strategic systemic) 分。净 -1 skill file, 同等功能。
- **前史**: `/subtract-full` (新 session 战略 audit) 早已并入 `/subtract --strategic` (2026-05-13, 实测仅 11% context vs spec'd 50% → 独立 skill over-engineered, 改 mode arg) — 现为本 skill 的 strategic mode。`/drift-audit` 本身 2026-05-13 合并自老 `docs-sync` (doc 全树) + `static-ssot-audit` (静态 SSOT 反模式), thesis = drift 是 stakeholder 决策点, auditor 只 surface impact + options (除客户面 + agent-boot 两例外)。
