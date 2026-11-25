# 实体与关系类型定义（ontology）

本词表是抽取时的受控词汇。确有需要可用 `other` 并在 notes 中说明，但 `other` 占比过高会被视为抽取不规范。

## 实体类型（entity.type）

| 类型 | 含义 | 示例 | 跨篇合并规则 |
|-|-|-|-|
| researcher | 研究者/团队 | "Chen et al."、"本研究第一作者" | 同名需额外证据（单位、ORCID、上下文），否则不合并 |
| material | 材料/试剂/样品 | "TiO2"、"mesoporous TiO2 layer" | 化学名/别名可合并；具体样品（批次、制备条件）不跨篇合并 |
| method | 方法/工艺/算法 | "spin-coating"、"DFT" | 通用方法概念可合并；具体参数实例不合并 |
| task | 研究任务/问题 | "perovskite solar cell fabrication" | 可合并，保留各自证据 |
| metric | 评价指标 | "PCE"、"power conversion efficiency" | 指标概念可合并；指标取值不是实体合并对象 |
| dataset | 数据集/语料 | 名称 + 版本 | 名称+版本一致才可合并 |
| model | 模型/器件结构 | "n-i-p planar device" | 结构概念可合并；具体器件实例不合并 |
| condition | 实验/计算条件 | "AM 1.5G, 100 mW cm-2" | 条件集合完全一致才可合并 |
| conclusion | 论文结论/发现 | 作者声称的因果关系、性能结论 | 一律不跨篇合并；各篇独立成节点 |
| value | 数值结果 | "PCE of 21.1%" | 一律不跨篇合并，绑定到所属论文 |
| other | 上述不能覆盖 | — | 默认不合并 |

## 关系谓词（relation.predicate）

| 谓词 | 方向 | 含义 | 直接证据判据 |
|-|-|-|-|
| uses | subject → object | 使用了材料/方法/数据集 | 原文明确陈述使用 |
| evaluates_on | subject → object | 在任务/数据集上评测 | 原文明确评测设置 |
| measures | subject → object | 用指标度量对象 | 指标与对象同时被明确关联 |
| compares_with | subject ↔ object | 与基线/他法比较 | 原文出现比较设置 |
| outperforms | subject → object | 优于 | 原文给出比较结论与条件；必须填 conditions |
| supports | subject → object | 支持某结论 | 作者明确表述 |
| contradicts | subject → object | 与某结论/结果矛盾 | 作者明确表述；与共现无关 |
| part_of | subject → object | 组成关系 | 原文明确结构/层级 |
| causes | subject → object | 因果 | 作者明确因果声称；相关不等于因果 |
| reports_value | subject → object | 报告某数值结果 | 数值与对象在同句/同段 |
| cites | subject → object | 转述他人工作 | attribution=reported_other 时常用 |
| other | — | — | 需在 notes 说明 |

## 证据强度（evidence_strength）

- `direct`：该论文作者对自身实验/计算/分析的直接陈述。
- `reported`：作者转述他人结果或综述性陈述（引用文献）。
- `inferred`：抽取者根据上下文推断。原则上不进图谱；确需保留时必须在 result 的 uncertainty 中说明。

## 归属（attribution）

- `author`：作者自述（本研究做了/发现）。
- `reported_other`：转述他人工作。转述内容不能作为本论文自身实验的直接证据。

## 冲突与合并记录

- `merge_decisions`：每条含 `canonical`、`merged`、`justification`、`confidence`(high/medium/low)。跨篇合并 justification 必须指向双方原文证据。
- `conflicts`：`items`（涉及实体/关系）、`description`、`resolution`（kept_separate / both_kept / unresolved）。源内数值冲突、跨篇条件不同导致的结论差异，都以冲突保留，不得择一删除。
