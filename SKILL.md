---
name: literature-kg-construction
description: 从一批论文材料中抽取科研实体与关系、绑定原文证据（source_id + JATS 段落 ID + 原文短引）、跨篇对齐别名、构建可查询可回查的文献知识图谱，并输出结构化 result.json。当任务要求对给定论文/材料做实体关系抽取、证据绑定、图谱导出、关系查询或增量更新时使用。
---

# 文献知识图谱构建（literature-kg-construction）

将给定的一批论文材料（每篇独立 source_id）转换为带证据的节点与边，交付可查询、可回查的知识图谱。每个实质节点/边都能回到具体论文的具体段落和原文片段；跨篇合并有依据，冲突显式保留。

## 适用条件与输入

运行时输入位于 `/input/`：`case.json`、`task.md`，以及材料文件（典型为 `corpus-manifest.json`、`material.json`、`primary-material.json`、`secondary-material.json`，篇数与文件名以实际为准）。工作目录 `/app/work`，最终产物写入 `/app/output`。

先**实际读取**这些文件确认结构，不要凭文件名臆测内容。`case.json` 中的根 DOI/title/authors 只属于第一篇（primary），不得套到第二篇。

## 四条铁律（对应评分核心）

1. **抽得准**：实体必须是论文文本中真实出现的科研对象（研究者、材料、方法、任务、指标、结论、数据集、模型、条件等）。每个实体至少挂一条原文证据；禁止凭领域常识补全概念。区分作者自述（attribution=author）与转述他人工作（attribution=reported_other）。
2. **连得对**：关系类型、方向和适用条件以原文为据。共现、综述转述、推测不算直接证据，用 `evidence_strength`（direct / reported / inferred）标注；inferred 关系应尽量避免，无法避免时必须在 uncertainty 中说明。
3. **对得齐**：别名、缩写、大小写、全称/简称的合并必须给出依据（merge_decisions.justification）。同名不同对象不得合并。相同通用方法/材料术语不代表两篇使用相同样品、模型实例、数据集或实验条件——概念节点可合并（保留各自来源证据），结论、数值、样品节点不得跨篇合并。仅同篇存在多种文件格式不算跨篇证据。
4. **查得到、回得去**：位置一律使用组织方给定的段落 ID（JATS 段落 ID），不是 PDF 页码；本类材料无 PDF 页码，不得自建"第 1 页"。未报告、无法判断、源内冲突显式保留，不写成事实。

## 工作流程（务必按序执行）

### 第 0 步：盘点输入（约 1–2 次请求）

```bash
ls -la /input/
python /skills/weekly-skill/scripts/kg_index.py --input /input --out /app/work/paragraph_index.json
```

脚本自动发现材料文件、递归提取所有 `{source_id, paragraph_id, text}` 段落，并从 manifest 提取论文元数据。阅读其输出的统计（各 source_id 段落数、文本总量），判断材料是否完整；PDF 无法解析或材料缺失时记录到结果的 `status` 与 `uncertainty`，不要编造内容。

### 第 1 步：读材料、做抽取（主要工作量）

- 先读 `case.json` 的 `output_contract` 与 `task.md`，明确题目要求的实体类型、关系类型、查询问题和输出字段。
- 分段读取各材料正文（按 paragraph_index 的段落 ID 顺序），填写 `/app/work/extraction.json`，格式严格遵循 `schema/extraction_format.md`，可拷贝 `templates/extraction.template.json` 起步。
- 每个实体/关系的每条证据写 `{source_id, paragraph_id, quote}`，quote 为原文连续短引（10–40 词为宜），脚本会做规范化包含校验。
- 跨篇合并候选写入 `merge_decisions`（含 justification 与 confidence）；决定不合并的同名/近似对象写入 `conflicts`（resolution=kept_separate）并说明理由。
- 数值结果、实验条件、样品归属保持各篇独立，写入各自 paper 的实体，不合成统一结论。

### 第 2 步：校验抽取

```bash
python /skills/weekly-skill/scripts/kg_validate.py --index /app/work/paragraph_index.json --extraction /app/work/extraction.json --report /app/work/validation_report.json
```

- error（关系端点不存在、实体缺证据等）必须修复后重跑。
- warning（quote 未在对应段落中命中、类型/谓词不在词表等）逐条处理：优先修正 paragraph_id 或改用原文精确短引；确实因公式线性化/上下标丢失导致不命中的，在该证据加 `"match_note"` 说明并在最终 uncertainty 中汇总。

### 第 3 步：构建图谱

```bash
python /skills/weekly-skill/scripts/kg_build.py --index /app/work/paragraph_index.json --extraction /app/work/extraction.json --outdir /app/output
```

产物：`graph.json`（节点/边/证据/冲突）、`graph.md`（人类可读表格）、`changes.md`（合并与冲突处置记录）。节点/边 ID 由规范化名称哈希生成，增量加入新论文时既有编号不变。脚本自动检测同 (subject, object) 上的谓词冲突并保留为 conflict，不静默消解。

### 第 4 步：实际执行查询（至少 3 个）

按 `task.md` 要求的查询问题（题目未给定时自拟覆盖：单实体关系查询、跨篇比较、证据回查），填写 `/app/work/queries.json`（模板见 `templates/queries.template.json`），然后：

```bash
python /skills/weekly-skill/scripts/kg_query.py --graph /app/output/graph.json --queries /app/work/queries.json --out /app/output/query_results.json
```

查询是真实执行的，结果含命中子图与证据；查不到的关系如实输出 `no_result` 及说明，禁止补造。

### 第 5 步：写 result.json 与说明

按 `case.json` 的 `output_contract` 逐字段组装 `/app/output/result.json`（含 `case_id`），模板见 `templates/result.template.json`。必须包含：

- `status`：success / partial / cannot_determine / refused 及原因；
- 主结果：图谱统计、产物文件路径、查询结果摘要；
- 证据与边界：所有定位使用 source_id + paragraph_id + 原文短引；未报告项与不确定项单列；
- 变更记录：合并、冲突、校验未命中 quote 的处置。

另写 `/app/output/README.md` 简述本案例构建过程与复核入口（如何重跑校验与查询）。异常（材料缺失、无法判断、运行失败）分别说明，部分完成要指明界限。

## 异常处理

| 情况 | 处置 |
|-|-|
| 材料文件缺失或为空 | status=partial/cannot_determine，uncertainty 记录缺什么，不臆造内容 |
| 段落 ID 在索引中不存在 | 回到材料重新定位，禁止虚构 ID |
| quote 校验反复不命中 | 换更短的原文精确片段；公式线性化导致的不命中加 match_note |
| 跨篇同名对象证据不足 | 默认不合并，记入 conflicts（kept_separate） |
| 查询无结果 | 如实输出 no_result 与可能原因 |
| 请求/时间预算不足 | 先保 graph.json + result.json（诚实 partial），再补查询与说明 |

## 预算提示（64 请求 / 900 秒 / 16k tokens）

重活交给脚本：索引、校验、建图、查询全自动。模型只做两件事——读材料填 extraction.json、按 output_contract 写 result.json。读材料用分段读取，不要把整个语料粘进单条回复；extraction.json 用 write 工具一次性落盘，校验后只做增量修补。

## 资源清单

- `scripts/kg_index.py`：材料发现与段落索引（stdlib，Python ≥3.8）
- `scripts/kg_validate.py`：抽取结果 schema 与证据回查校验
- `scripts/kg_build.py`：合并应用、稳定 ID 分配、图谱导出（json/md）与冲突检测
- `scripts/kg_query.py`：查询执行（entity / compare / evidence / search）
- `scripts/kg_common.py`：共享工具（规范化、quote 匹配、稳定 ID）
- `schema/ontology.md`：实体/关系类型与证据强度定义
- `schema/extraction_format.md`：extraction.json 字段规范
- `templates/`：extraction、queries、result 三个起步模板
- `examples/`：合成小样本端到端调用示例（**仅为接口示意，非正式案例结果**）
