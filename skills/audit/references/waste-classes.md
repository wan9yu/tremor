# waste mode — 6-8 类 "看似有用其实无用" 详细扫描

来源: 老 `/subtract` skill 的 6 类 + carved-out follow-up + outdated protocol (A-H). 每类 = 模式 + verify bash + KEEP signal + action.

---

## A. Dead code (zero consumer)

模式: 函数 / 类 / 模块 / utility 不被 import / call.

```bash
# A1. symbol level
rg "<symbol_name>" --type py -l | wc -l  # 1 = only definer = dead

# A2. module level
find <module> -name "*.py" -exec basename {} .py \; | \
  while read m; do echo "$m: $(rg "import $m\|from $m" --type py | wc -l)"; done

# A3. orphan test (tests/test_X.py with no covered code path)
pytest --collect-only -q | grep "test_X" — exists?
```

**KEEP signal** (skip delete):
- entry point in `pyproject.toml [project.scripts]` / `[project.entry-points]`
- referenced in `docker-compose.yml` / systemd unit / CI workflow
- referenced in user-facing doc as agent command (`tools/X.py` for dev/qa/product)
- `__all__` 包含但本 module 用 (public API)

---

## B. Stale doc (contradicted by reality)

模式: `last_verified` 过期 / 版本号停在 N-2 / 引用废弃 API / 描述与 code 实际行为差.

```bash
# B1. last_verified > 90 day
rg "^last_verified:" docs/ | awk -F: '{ ... cmp date ... }'

# B2. version claim vs gateway/version.py
grep -rE "v1\.\d|\d+\.\d+\.\d+" docs/ README.md website/ | \
  cross-check against gateway/version.py __version__

# B3. API claim vs actual import
# E.g. AGENTS.md says `redact(text, with_types=True)` — actually run it
python3 -c "from X import Y; help(Y)" — verify signature match

# B4. expires_after past
rg "^expires_after:" docs/ — date < today → archive

# B5. status: draft 但实际 ship 完
git log --since="<since-date>" --grep="<ship-keyword>" — verify shipped
```

**KEEP signal**:
- IMMUTABLE (`docs/engineering/decisions-immutable.md`)
- 战略 blueprint (`docs/product/v*-blueprint*.md`)
- 协议 (`schedule/team_agreements.md`, `schedule/prompts/*.md`)

---

## C. Premature abstraction (single consumer)

模式: SSOT helper / shared module / `_utils.py` 只被 1 处 import.

```bash
# C1. consumer count for helper module
rg "from <helper_module> import\|import <helper_module>" --type py | wc -l
# 1 = single consumer → premature

# C2. abstraction layer benefit
# 抽象层有 < 30 行 OR < 3 method/function = 可能 premature
wc -l <helper_path>
```

**Action**: in-line 回 single consumer + 删 helper. 待真有 multi-consumer 再抽出.

**KEEP signal**:
- "for future use" 旁注 + GitHub issue / Sand 卡 explicit reference 该 multi-consumer 在 next milestone
- IMMUTABLE / 协议 SSOT (天然 single-consumer for security/correctness)

---

## D. Duplicate content (mirror-of 仍 copy-paste)

模式: `team_agreements.md` 与 `decisions-immutable.md` 共享段; `<!-- mirror-of: X -->` 注释存在但 content 仍复制; zh/en doc pair drift.

```bash
# D1. find mirror-of comments
rg "<!-- mirror-of:" docs/ schedule/ --type md

# D2. for each, diff vs source — 应该一致 OR 该改 pointer
# D3. zh/en doc pair line drift > 50%
for f in docs/user-guide/*.en.md; do
  z=${f%.en.md}.md
  z_lines=$(wc -l < "$z")
  e_lines=$(wc -l < "$f")
  ratio=$(echo "scale=2; $e_lines / $z_lines" | bc)
  echo "$f $z_lines:$e_lines ($ratio)"
done | awk '$NF < 0.5 || $NF > 1.5'  # > 50% drift
```

**Action**: 删 mirror 段, 留 pointer 引 source SSOT.

---

## E. Over-engineering (defense without threat)

模式: 防御 N 层但 threat model 不清; retry/fallback 层多但 upstream 已稳; 多种 backup 但 1 种足够.

**Verify**:
- 该 defense 防什么? — `docs/engineering/decisions-immutable.md` / `team_agreements.md §边界红线` 列?
- 该 defense 触发过? — `git log` 找该路径真 trip 案例; 0 trip in N 月 = 候选删
- 该 defense 增加 N 行代码 vs 风险概率 — ROI 评

**KEEP signal**:
- 7-layer safety net 类 (审计 + invariant + smart + cron + monitor + pre-commit + ramp-up) — 故意多层 by design
- 异步竞态防护 (flock / atomic write) — 单层不够

---

## F. Archive cruft (>60 day, 0 access)

模式: `snapshots-archive/2026-XX/` / `legacy-*` / `migration-archive/` / `*-archive*.md` 存在但 0 incoming link, 0 grep ref.

```bash
# F1. inbound reference
rg "<archive_path>\b" --type md --type py | wc -l
# 0 = orphan

# F2. last read access
ls -tu <archive_dir>  # `t -u` 按 access time sort, top should be recent

# F3. git log content 已 codify 到现行 doc
grep -E "<key_concept_from_archive>" docs/ --include="*.md"  # 内容已被 codify → archive 可删
```

**Action**: git rm (history 兜底). 不 mv 到任何过渡区 — 违反"working-tree 清洁"原则.

---

## G. Carved-out follow-up 未立 (#X-b 类)

模式: close 的 issue body 含 unchecked AC "后续轮 follow-up #X-b 立卡" 但 follow-up issue 不存在.

```bash
# G1. find close 时承诺 follow-up
gh search issues "follow-up" --state=closed --json number,body,closedAt \
  | jq '.[] | select(.body | contains("#[0-9]+-b"))'

# G2. for each, check 是否真立
gh issue list --search "<follow-up-tag>" --state=all
```

**Action**: 真未立 → **当前 milestone Sand 立卡** (per memory `feedback_audit_followup_default_current_milestone`); 不要 default v-next defer.

---

## H. Outdated protocol (replaced but not deleted)

模式: `team_agreements.md` 内部 self-contradict (新协议段 + 老协议段并存); `_common.md` 含已废止指令.

```bash
# H1. 同 file 找 "新协议" / "整改" / "废止" / "deprecation" 关键字
grep -nE "整改|废止|deprecated|新协议|2026-0[1-9]" schedule/team_agreements.md

# H2. 对应 invariant / 守门 工具是否真改
# E.g. team_agreements 说 "X 自动化" → tools/X.py 真存在? invariant 真守?
```

**Action**: 删老协议段 (Migration: 注解备案), 不留 deprecation banner — banner 是缓和但 agent boot 仍读, drift 风险在.
