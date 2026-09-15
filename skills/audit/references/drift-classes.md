# drift mode — 5 类一致性 drift 详细扫描

来源: 老 `/drift-audit` skill 的 5 类. 每类 = 模式 + verify bash. Stakeholder 分桶 + AUTO-FIX 边界见 SKILL.md 主体.

---

## 类 1: doc↔code drift (数字 / version / API / count 抄写)

模式: doc 字面写"N 类 X" / "v1.X" / "API signature foo(arg1, arg2)" — code 是 SSOT, doc 抄了 stale 值.

```bash
# version drift
grep -rE "v\d+\.\d+|\d+\.\d+\.\d+" docs/ README.md website/ \
  | cross-check 项目代码 version SSOT (e.g. <pkg>/__version__.py / pyproject.toml)

# count drift
grep -rE "\b\d+\s*(类|个|种)\s*<topic>" docs/ \
  | cross-check 实际 enumeration (ls / wc / dynamic count)

# API drift
grep -rE "<api_func>\([^)]+\)" docs/ \
  | python -c "import <module>; help(<module>.<func>)" 验 signature 匹配

# dep version drift (e.g. argus-redact 0.4.2 in doc vs 0.6.5 in pyproject)
grep -rE "<dep_name>\s*[><=~]+\s*\d" docs/ AGENTS.md \
  | grep "<dep_name>" pyproject.toml | cross-check
```

---

## 类 2: code↔code SSOT 双源 drift

模式: 同 fact 在 2+ 代码处独立维护, 缺 invariant 守门.

```bash
# 同模块名 list 出现多处
grep -rn "_MODULE_ORDER\|_REGISTRY\|_LIST" <code_dir>/*.py \
  | awk -F: '{print $1}' | sort -u  # >1 file → 双源候选

# "must stay in sync" comment 无 invariant
grep -rnE "(must|should|need|应当?|必须) (stay|keep|be kept|保持) (in )?sync" \
  <code_dir>/ --include="*.py" \
  | while read m; do
      file=$(echo "$m" | cut -d: -f1)
      # 反查 invariant
      grep -rE "test_.*sync|test_.*ssot|test_.*matches|test_.*aligned" tests/ \
        | grep -q "$file" || echo "DRIFT: $m (无 invariant)"
    done
```

---

## 类 3: comment↔reality drift

模式: 注释/doc 提"see X" / "参见 Y" but X 不存在 OR Y 已 rename / "must stay in sync" 已废.

```bash
# broken cross-ref in markdown
grep -rE "\[([^]]+)\]\(([^)]+\.md[^)]*)\)" docs/ \
  | while read line; do
      target=$(echo "$line" | sed -E 's/.*\(([^)]+)\).*/\1/')
      [ -e "$(dirname "$file")/$target" ] || echo "BROKEN: $line"
    done

# Python comment "see <path>" pattern
grep -rnE "see [a-zA-Z_/.\-]+\.(py|md)" --include="*.py" \
  | verify each path exists
```

---

## 类 4: SSOT 应迁候选 (手抄应改为 generated/pointer)

模式: doc 字面抄 build artifact / 静态值 — 应改为 build-time inject 或 pointer.

```bash
# count claim that should be derived
grep -rE "\b\d+\s*(invariant|test|module|adapter|endpoint)" docs/ \
  | check if matched value is dynamically derivable (ls | wc -l, etc.)

# version claim that should be inject
# (e.g. doc says "v1.5" — should reference __version__ via build-time substitution)
```

输出**应迁候选清单** — 不强推 (architectural choice), 给 dev/architect 决策方向.

---

## 类 5: 客户可见性 gap (客户面 doc claim vs ship reality)

模式: 客户面 doc (user-guide / website / README) 声明 X feature / Y behavior, 但代码已 ship 别的.

```bash
# customer-facing API claim vs actual
grep -rE "endpoint|method.*POST|GET" docs/user-guide/ \
  | cross-check with actual routes (FastAPI / Flask / etc. introspection)

# feature claim vs git log
grep -rE "v\d+\.\d+ (已发布|shipped|released)" docs/ website/ \
  | cross-check git tag / changelog SSOT
```
