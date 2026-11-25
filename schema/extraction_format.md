# extraction.json 字段规范

抽取结果是 Agent 手填的唯一中间产物，位于 `/app/work/extraction.json`。所有字段均为 UTF-8 JSON。

## 顶层结构

```json
{
  "papers": [...],
  "entities": [...],
  "relations": [...],
  "merge_decisions": [...],
  "conflicts": [...],
  "uncertainties": [...]
}
```

## papers[]（必填，每篇一条）

| 字段 | 说明 |
|-|-|
| source_id | 材料中的论文标识（与 paragraph_index 一致，如 primary / secondary） |
| doi / title / authors | 以 `corpus-manifest.json` 与该篇自身材料为准；根级 DOI/title/authors 只属于第一篇 |
| file | 正文来源文件名 |

## entities[]（必填）

| 字段 | 必填 | 说明 |
|-|-|-|
| id | 是 | 局部标识，抽取者自定（如 e_tio2_primary），仅在本文件内引用 |
| name | 是 | 原文表面形式（surface form），保持原文大小写与符号 |
| normalized | 否 | 规范化名称（小写、去修饰）；缺省时脚本自动生成 |
| type | 是 | 见 ontology.md |
| aliases | 否 | 该篇内出现的其他写法（缩写、全称、大小写变体） |
| source_id | 是 | 所属论文 |
| attribution | 是 | author / reported_other |
| evidence | 是 | 至少一条 `{paragraph_id, quote}`；quote 为原文连续短引 |
| notes | 否 | 补充说明（如同名歧义、类型存疑） |

## relations[]（必填，可为空数组但需在 uncertainty 说明）

| 字段 | 必填 | 说明 |
|-|-|-|
| id | 是 | 局部标识 |
| subject / object | 是 | 引用 entities 的局部 id |
| predicate | 是 | 见 ontology.md |
| conditions | 否（outperforms 必填） | 关系成立的适用条件，照录原文限定 |
| evidence_strength | 是 | direct / reported / inferred |
| attribution | 是 | author / reported_other |
| evidence | 是 | 至少一条 `{source_id, paragraph_id, quote}` |
| notes | 否 | — |

## merge_decisions[]（可空）

`{canonical, merged: [...], justification, confidence}`。justification 必须说明依据（同化学名、官方缩写对照等），跨篇合并须指向两篇各自的证据。只合并概念级实体；conclusion/value/样品/条件实例禁止跨篇合并。

## conflicts[]（可空）

`{items: [...], description, resolution}`。决定不合并的同名对象、源内数值冲突、跨篇条件差异都记在这里。

## uncertainties[]（可空）

自由文本数组：材料缺口、无法判断项、inferred 关系说明、quote 校验未命中的处置。

## 校验规则（kg_validate.py）

- error：关系端点未定义；实体缺 name/type/source_id/evidence；merge 引用不存在的 id。必须修复。
- warning：quote 未命中对应段落文本；type/predicate 不在词表；merge 两端 type 不同；evidence_strength=inferred。逐条处理或书面说明。
