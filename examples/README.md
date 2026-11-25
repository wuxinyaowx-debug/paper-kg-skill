# 最小调用示例（SYNTHETIC EXAMPLE — 仅为接口示意）

本目录演示一次完整的"索引 → 抽取 → 校验 → 建图 → 查询"流程。**fixture 中的两篇"论文"是为演示接口而编写的虚构文本，extraction.example.json 是手工填写的示意输入，output/ 是其运行结果；均非正式案例结果，不得当作正式答案引用。**

## 文件

- `fixture/`：模拟组织方输入的四个文件
  - `corpus-manifest.json`：两篇虚构论文的 DOI/作者/许可（`10.0000/synthetic.demo.*` 为虚构 DOI）
  - `material.json`：两篇段落的汇总索引
  - `primary-material.json` / `secondary-material.json`：各 3 个段落的虚构正文
- `extraction.example.json`：示意抽取输入（含 4 条跨篇合并、2 条不合并冲突、3 条不确定性）
- `queries.example.json`：4 个示意查询（entity / compare / evidence / search）
- `work/`、`output/`：下列命令的实际运行产物

## 运行（在本目录的上一级 submission/ 下执行）

```bash
python scripts/kg_index.py --input examples/fixture --out examples/work/paragraph_index.json
python scripts/kg_validate.py --index examples/work/paragraph_index.json \
    --extraction examples/extraction.example.json --report examples/work/validation_report.json
python scripts/kg_build.py --index examples/work/paragraph_index.json \
    --extraction examples/extraction.example.json --outdir examples/output
python scripts/kg_query.py --graph examples/output/graph.json \
    --queries examples/queries.example.json --out examples/output/query_results.json
```

## 实际运行结果（本机复跑记录）

- 索引：4 个文件，primary 3 段 + secondary 3 段，manifest 识别 2 篇
- 校验：errors=0, warnings=0
- 建图：nodes=11（15 个局部实体经 4 组合并），edges=11，conflicts=2
- 查询：Q1 entity "TiO2" 命中跨篇合并节点（primary:p1 与 secondary:s1 双来源证据）；Q2 compare SnO2↔TiO2 返回比较子图；Q3 evidence 回查 `R_3a8d5c52a6`（SnO2 outperforms TiO2，附 secondary:s2 原文短引）；Q4 search "spin-coating" 命中合并后的方法节点

## 本示例演示的要点

1. 跨篇概念合并（TiO2 = titanium dioxide = mesoporous TiO2 的材料概念）保留双来源证据，而数值节点（21.1% PCE vs 92%/74% 保持率）按规则**不合并**，并记入 conflicts。
2. `outperforms` 边强制携带 conditions（500 h、85 C / 85% RH、仅限 paper B 器件）。
3. 转述他人工作（Chen et al.）以 attribution=reported_other 标注，不作为本篇直接证据。
