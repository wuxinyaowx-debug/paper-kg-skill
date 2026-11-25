"""Validate an extraction.json against the paragraph index and the ontology.

Usage:
    python kg_validate.py --index /app/work/paragraph_index.json \
        --extraction /app/work/extraction.json \
        --report /app/work/validation_report.json

Exit code 1 on hard errors (broken references, missing required fields).
Quote mismatches and off-vocabulary terms are warnings: they must be fixed or
explicitly justified in the final result's uncertainty section.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_common import dump_json, load_paragraph_index, load_json, quote_in

ENTITY_TYPES = {"researcher", "material", "method", "task", "metric", "dataset",
                "model", "condition", "conclusion", "value", "other"}
PREDICATES = {"uses", "evaluates_on", "measures", "compares_with", "outperforms",
              "supports", "contradicts", "part_of", "causes", "reports_value",
              "cites", "other"}
STRENGTHS = {"direct", "reported", "inferred"}
ATTRS = {"author", "reported_other"}
NO_CROSS_MERGE = {"conclusion", "value"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--extraction", required=True)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    para_map, _papers = load_paragraph_index(args.index)
    ext = load_json(args.extraction)
    errors, warnings = [], []

    entities = ext.get("entities", [])
    relations = ext.get("relations", [])
    merges = ext.get("merge_decisions", [])
    eids = {}
    for i, e in enumerate(entities):
        tag = "entities[{}] ({})".format(i, e.get("id", "?"))
        if not e.get("id"):
            errors.append("{}: missing id".format(tag))
        elif e["id"] in eids:
            errors.append("{}: duplicate id".format(tag))
        else:
            eids[e["id"]] = e
        for f in ("name", "type", "source_id", "attribution"):
            if not e.get(f):
                errors.append("{}: missing required field '{}'".format(tag, f))
        if e.get("type") and e["type"] not in ENTITY_TYPES:
            warnings.append("{}: type '{}' not in ontology".format(tag, e["type"]))
        if e.get("attribution") and e["attribution"] not in ATTRS:
            warnings.append("{}: bad attribution '{}'".format(tag, e["attribution"]))
        ev = e.get("evidence") or []
        if not ev:
            errors.append("{}: entity has no evidence".format(tag))
        for j, evi in enumerate(ev):
            pid, src = evi.get("paragraph_id"), evi.get("source_id", e.get("source_id"))
            key = (src, str(pid))
            if key not in para_map:
                errors.append("{}: evidence[{}] paragraph not in index: {}".format(tag, j, key))
            elif evi.get("quote") and not quote_in(evi["quote"], para_map[key]["text"]):
                warnings.append("{}: evidence[{}] quote not found in {} "
                                "(fix paragraph_id/quote, or add match_note if "
                                "caused by linearised formulae)".format(tag, j, key))

    for i, r in enumerate(relations):
        tag = "relations[{}] ({})".format(i, r.get("id", "?"))
        for end in ("subject", "object"):
            if r.get(end) not in eids:
                errors.append("{}: {} '{}' is not a declared entity id".format(tag, end, r.get(end)))
        if r.get("predicate") not in PREDICATES:
            warnings.append("{}: predicate '{}' not in ontology".format(tag, r.get("predicate")))
        if r.get("evidence_strength") not in STRENGTHS:
            errors.append("{}: evidence_strength must be one of {}".format(tag, sorted(STRENGTHS)))
        if r.get("evidence_strength") == "inferred":
            warnings.append("{}: inferred relation - justify in uncertainty".format(tag))
        if r.get("predicate") == "outperforms" and not r.get("conditions"):
            warnings.append("{}: outperforms without conditions".format(tag))
        ev = r.get("evidence") or []
        if not ev:
            errors.append("{}: relation has no evidence".format(tag))
        for j, evi in enumerate(ev):
            key = (evi.get("source_id"), str(evi.get("paragraph_id")))
            if key not in para_map:
                errors.append("{}: evidence[{}] paragraph not in index: {}".format(tag, j, key))
            elif evi.get("quote") and not quote_in(evi["quote"], para_map[key]["text"]):
                warnings.append("{}: evidence[{}] quote not found in {}".format(tag, j, key))

    # merge decisions
    for i, m in enumerate(merges):
        tag = "merge_decisions[{}]".format(i)
        canon = m.get("canonical")
        if canon not in eids:
            errors.append("{}: canonical '{}' unknown".format(tag, canon))
        merged = m.get("merged") or []
        if not merged:
            errors.append("{}: empty merged list".format(tag))
        if not m.get("justification"):
            errors.append("{}: missing justification".format(tag))
        srcs, types = set(), set()
        for mid in ([canon] if canon else []) + list(merged):
            if mid not in eids:
                errors.append("{}: merged id '{}' unknown".format(tag, mid))
            else:
                srcs.add(eids[mid].get("source_id"))
                types.add(eids[mid].get("type"))
        if len(types) > 1:
            warnings.append("{}: merging entities of different types {}".format(tag, sorted(types)))
        if len(srcs) > 1:
            if types & NO_CROSS_MERGE:
                errors.append("{}: cross-paper merge of {} is forbidden".format(tag, sorted(types & NO_CROSS_MERGE)))
            if m.get("confidence") not in ("high", "medium", "low"):
                warnings.append("{}: cross-paper merge without confidence level".format(tag))

    report = {"errors": errors, "warnings": warnings,
              "counts": {"entities": len(entities), "relations": len(relations),
                         "merge_decisions": len(merges),
                         "conflicts": len(ext.get("conflicts", [])),
                         "uncertainties": len(ext.get("uncertainties", []))}}
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        dump_json(report, args.report)
    print("errors: {}, warnings: {}".format(len(errors), len(warnings)))
    for m in errors:
        print("ERROR:", m)
    for m in warnings:
        print("WARN :", m)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
