# strategic mode — 整体 holistic critique

来源: 老 `/subtract --strategic` (原独立 /subtract-full skill, 2026-05-13 并入). AI 角色 = architect (整体思考 + systemic 模式), 非 auditor (单点 findings).

跟 tactical (waste / drift) mode 不同:
- **scope**: 整 repo 必扫 (不可 scope-select)
- **context budget**: 15-30% 典型 (诊断: < 10% 可能 shallow, > 40% 可能 stuck on low-value reads)
- **执行流程**: 5 sub-agent 并行 (类 A+C / B+D / E+K / F+G / I+J 各扫 systemic pattern) + 主 thread cross-cutting synthesis
- **AI 角色**: architect (整体思考 + systemic 模式), 非 auditor (单点 findings)

## 系统级 lens (tactical 不查的 3 类)

- **I. 增长 trajectory** — code/doc/test 各自 LOC 增长 vs feature delivery
- **J. SSOT 应迁候选** — doc 手抄 fact 现状 + 迁 build-time inject / pointer 候选
- **K. 协议复杂度通胀** — protocol doc 累积 vs prune cadence; agent boot context tax

## Output 格式

TL;DR (≤3 句) + Growth Trajectory + 3-5 Systemic Root Causes + What's Working (防 negativity bias) + Cross-cutting Case Studies + 3-5 战略 Options (含"接受 by-design") + What I Did NOT Touch + Verify Quality.

## 必含原则

- TL;DR 必 ≤ 3 句
- 战略 options 必 ≥ 3 个 + 含 "接受 / 不动" 合法选项
- 各 option detail level 对等 (防 implicit hint bias)
- What's working 段 必有
- Trajectory 用 cadence / commits / event-trigger 表达, **不用日期/周数** (per memory `feedback_no_time_estimates`)

## 触发场景

- Quarterly major audit (~每 3 月或 200+ commits)
- Minor version pivot 后 (v1.X ship → v1.Y ramp-up)
- 用户感觉"项目 bloat 但说不清"
- tactical mode 多次出 KEEP-EXPLICIT / DISCUSS = 信号 holistic 看不全
- **避免**: 同 session 已用 30%+ context → 不召唤 (推荐新的独立 session 启避免上下文污染)
