# literature-kg-construction — 使用与方法说明

文献知识图谱构建 Skill：从一批论文材料中抽取实体与关系、绑定原文证据（source_id + JATS 段落 ID + 原文短引）、跨篇对齐别名、导出可查询图谱并实际执行查询。本文件面向复用者与评审，说明依赖、调用步骤、方法、适用范围与自查方式。说明与提交版本一致。

## 依赖与安装

- Python ≥ 3.8，**仅标准库**（json / re / hashlib / unicodedata / argparse / os / sys）。无需 pip 安装，无网络依赖。
- 全部文件为 UTF-8 文本，无符号链接；脚本间通过文件路径传参，无隐藏状态。
- 文件清单（13 个资源文件 + 本说明 + SKILL.md）：
  - `SKILL.md`：Agent 调用指令（含 YAML frontmatter）
  - `scripts/kg_common.py`：规范化、quote 匹配、稳定 ID、IO（容忍 UTF-8 BOM）
  - `scripts/kg_index.py`：材料发现与段落索引
  - `scripts/kg_validate.py`：抽取结果校验（schema + 证据回查）
  - `scripts/kg_build.py`：合并应用、稳定 ID、图谱导出、冲突自动检测
  - `scripts/kg_query.py`：查询执行（entity / compare / evidence / search）
  - `schema/ontology.md`：实体/关系类型、证据强度、归属、合并规则
  - `schema/extraction_format.md`：extraction.json 字段规范
  - `templates/extraction.template.json`、`templates/queries.template.json`、`templates/result.template.json`
  - `examples/`：合成小样本端到端示例（见 `examples/README.md`，**仅为接口示意**）

## 调用步骤（与 SKILL.md 一致）

```bash
# 0. 段落索引（输入目录含 corpus-manifest / material / primary / secondary 等 JSON）
python scripts/kg_index.py --input /input --out /app/work/paragraph_index.json

# 1. Agent 阅读材料，按 schema/extraction_format.md 填写 /app/work/extraction.json

# 2. 校验（error 必须修复，warning 逐条处理或书面说明）
python scripts/kg_validate.py --index /app/work/paragraph_index.json \
    --extraction /app/work/extraction.json --report /app/work/validation_report.json

# 3. 建图（graph.json / graph.md / changes.md）
python scripts/kg_build.py --index /app/work/paragraph_index.json \
    --extraction /app/work/extraction.json --outdir /app/output

# 4. 查询（≥3 个真实查询，结果含证据）
python scripts/kg_query.py --graph /app/output/graph.json \
    --queries /app/work/queries.json --out /app/output/query_results.json

# 5. Agent 按 case.json 的 output_contract 组装 /app/output/result.json
```

## 关键方法

1. **证据强约束**：实体/关系必须携带 `{source_id, paragraph_id, quote}`；`kg_validate.py` 用规范化包含匹配（NFKC、小写、去空白标点）核验 quote 确实出现在对应段落，未命中即 warning，防止"凭常识补全"。
2. **受控词表**：实体 11 类、谓词 12 类（见 ontology.md），`outperforms` 强制填写 `conditions`；`inferred` 关系强制进入 uncertainty。
3. **对齐与冲突**：合并只在 `merge_decisions` 中显式声明且必须给 justification；跨篇合并禁用于 conclusion/value 类节点（脚本强制）；同 (subject, object) 对上出现 `contradicts` 与正向谓词时自动记为冲突并保留。
4. **稳定 ID**：节点/边 ID 为规范化名称的 SHA-1 短哈希，增量加入新论文不会重编号既有节点，满足增量更新要求。
5. **人机分工**：脚本承担索引、校验、建图、查询等确定性工作；模型只做阅读抽取与结果组装，降低幻觉面并适配 64 请求 / 900 秒预算。

## 适用范围与限制

- 适用：组织方提供的 JSON 化论文材料（含 source_id 与 JATS 段落 ID 的任何嵌套结构；walker 自动发现，字段名不预设）。PDF 需先由平台工具转成文本段落。
- 不适用：无段落 ID 的纯文本（索引为空时脚本会 WARN，此时应按异常流程记录 partial 而非编造 ID）。
- 已知限制：实体识别与关系判断由模型完成，质量依赖抽取者的阅读；quote 匹配对公式线性化宽容但可能漏报，需以 `match_note` 标注；查询为精确/子串匹配，无语义检索。

## 失败处理与自查

| 自查项 | 方法 |
|-|-|
| 证据可回查 | `validation_report.json` 中 errors/warnings 应为 0 或全部有书面处置 |
| 图谱一致 | `graph.md` 表格逐行核对 sources 列是否覆盖两篇 |
| 合并有据 | `changes.md` 每条 MERGE 有 justification 与 confidence |
| 查询真实 | `query_results.json` 每条含 status 与 evidence；`no_result` 如实保留 |
| 结果完整 | `result.json` 含 case_id 与 output_contract 全部字段，status 诚实 |

异常（材料缺失、无法判断、运行失败）在 result.json 的 status/status_reason 与 uncertainty 中分别说明；部分完成须指明界限。

## 维护

- 版本：v1.0（2026-11）。词表与脚本向后兼容：新增谓词/类型只需更新 `schema/ontology.md` 与 `kg_validate.py` 中的集合。
- 问题反馈与更新：见 `GITHUB_URL.txt` 指向的公开仓库。
