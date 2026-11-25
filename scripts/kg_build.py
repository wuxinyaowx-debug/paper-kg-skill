"""Build the evidence-bound knowledge graph from a validated extraction.

Usage:
    python kg_build.py --index /app/work/paragraph_index.json \
        --extraction /app/work/extraction.json --outdir /app/output

Outputs: graph.json, graph.md, changes.md
Node/edge ids are hash-based and stable: re-running or adding a new paper does
not renumber existing nodes. Contradictory predicates on the same
(subject, object) pair are auto-recorded as conflicts and kept, never silently
resolved.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_common import dump_json, load_json, norm, stable_id

POSITIVE = {"supports", "outperforms", "uses", "measures", "causes"}


def attach_evidence(items, para_lookup_note=""):
    out = []
    for ev in items or []:
        rec = {"source_id": ev.get("source_id"),
               "paragraph_id": str(ev.get("paragraph_id")),
               "quote": ev.get("quote", "")}
        if ev.get("match_note"):
            rec["match_note"] = ev["match_note"]
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--extraction", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    ext = load_json(args.extraction)
    entities = {e["id"]: e for e in ext.get("entities", [])}

    # --- apply merges -------------------------------------------------------
    changes = []
    alias_of = {}          # local id -> canonical local id
    for m in ext.get("merge_decisions", []):
        canon = m["canonical"]
        for mid in m.get("merged", []):
            if mid in entities and mid != canon:
                alias_of[mid] = canon
        changes.append({
            "kind": "merge", "canonical": canon, "merged": m.get("merged", []),
            "justification": m.get("justification", ""),
            "confidence": m.get("confidence", ""),
            "cross_paper": len({entities[x]["source_id"]
                                for x in [canon] + m.get("merged", [])
                                if x in entities}) > 1,
        })

    def canon_of(lid):
        return alias_of.get(lid, lid)

    # --- nodes --------------------------------------------------------------
    nodes = {}
    for lid, e in entities.items():
        c = canon_of(lid)
        if c not in nodes:
            ce = entities[c]
            node_id = stable_id("N", ce["type"], ce.get("normalized") or ce["name"])
            nodes[c] = {
                "node_id": node_id,
                "name": ce["name"],
                "normalized": norm(ce.get("normalized") or ce["name"]),
                "type": ce["type"],
                "aliases": sorted(set(ce.get("aliases", []))),
                "attribution": ce.get("attribution"),
                "sources": [],
                "merged_from": [],
                "notes": ce.get("notes", ""),
            }
        n = nodes[c]
        if lid != c:
            n["merged_from"].append(lid)
            for a in [e["name"]] + e.get("aliases", []):
                if norm(a) != n["normalized"] and a not in n["aliases"]:
                    n["aliases"].append(a)
        src_rec = {"source_id": e["source_id"],
                   "evidence": attach_evidence(
                       [dict(ev, source_id=ev.get("source_id", e["source_id"]))
                        for ev in e.get("evidence", [])])}
        n["sources"].append(src_rec)

    # --- edges --------------------------------------------------------------
    edges = []
    for r in ext.get("relations", []):
        s, o = canon_of(r["subject"]), canon_of(r["object"])
        if s not in nodes or o not in nodes:
            continue  # validate.py already reports this; skip defensively
        edge_id = stable_id("R", nodes[s]["node_id"], r["predicate"],
                            nodes[o]["node_id"], r.get("conditions", ""))
        edges.append({
            "edge_id": edge_id,
            "subject": nodes[s]["node_id"],
            "subject_name": nodes[s]["name"],
            "predicate": r["predicate"],
            "object": nodes[o]["node_id"],
            "object_name": nodes[o]["name"],
            "conditions": r.get("conditions", ""),
            "evidence_strength": r.get("evidence_strength"),
            "attribution": r.get("attribution"),
            "evidence": attach_evidence(r.get("evidence")),
            "notes": r.get("notes", ""),
        })

    # --- automatic contradiction detection ----------------------------------
    conflicts = list(ext.get("conflicts", []))
    by_pair = {}
    for ed in edges:
        by_pair.setdefault((ed["subject"], ed["object"]), []).append(ed)
    for (s, o), group in by_pair.items():
        preds = {g["predicate"] for g in group}
        if "contradicts" in preds and preds & POSITIVE:
            conflicts.append({
                "items": [g["edge_id"] for g in group],
                "description": "auto-detected: same (subject, object) carries "
                               "both 'contradicts' and positive predicates "
                               "({}); kept as-is, not resolved".format(
                                   ", ".join(sorted(preds))),
                "resolution": "both_kept",
            })
            changes.append({"kind": "auto_conflict",
                            "pair": [s, o], "predicates": sorted(preds)})

    graph = {
        "papers": ext.get("papers", []),
        "nodes": sorted(nodes.values(), key=lambda n: n["node_id"]),
        "edges": edges,
        "conflicts": conflicts,
        "uncertainties": ext.get("uncertainties", []),
        "id_scheme": "hash-based stable ids (N_/R_ + sha1[:10]); incremental "
                     "updates keep existing ids",
    }
    os.makedirs(args.outdir, exist_ok=True)
    dump_json(graph, os.path.join(args.outdir, "graph.json"))

    # --- human-readable graph.md --------------------------------------------
    lines = ["# Knowledge graph", ""]
    lines.append("Papers: " + ", ".join(
        "{} ({})".format(p.get("source_id"), p.get("doi") or "no-doi")
        for p in graph["papers"]))
    lines += ["", "## Nodes ({})".format(len(graph["nodes"])), "",
              "| node_id | name | type | aliases | sources |", "|-|-|-|-|-|"]
    for n in graph["nodes"]:
        srcs = "; ".join("{}: {}".format(
            s["source_id"],
            ", ".join(ev["paragraph_id"] for ev in s["evidence"]))
            for s in n["sources"])
        lines.append("| {} | {} | {} | {} | {} |".format(
            n["node_id"], n["name"], n["type"],
            "; ".join(n["aliases"]), srcs))
    lines += ["", "## Edges ({})".format(len(edges)), "",
              "| edge_id | subject | predicate | object | conditions | strength | evidence |",
              "|-|-|-|-|-|-|-|"]
    for ed in edges:
        ev = "; ".join("{}:{} \"{}\"".format(
            e["source_id"], e["paragraph_id"],
            (e["quote"][:60] + "...") if len(e["quote"]) > 60 else e["quote"])
            for e in ed["evidence"])
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            ed["edge_id"], ed["subject_name"], ed["predicate"],
            ed["object_name"], ed["conditions"], ed["evidence_strength"], ev))
    if conflicts:
        lines += ["", "## Conflicts (kept, not resolved)", ""]
        for c in conflicts:
            lines.append("- {} -> {}".format(c.get("description", ""),
                                             c.get("resolution", "")))
    if graph["uncertainties"]:
        lines += ["", "## Uncertainties", ""]
        for u in graph["uncertainties"]:
            lines.append("- {}".format(u))
    with open(os.path.join(args.outdir, "graph.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # --- changes.md ----------------------------------------------------------
    cl = ["# Merge / conflict change log", ""]
    if not changes:
        cl.append("No merges or auto-conflicts.")
    for c in changes:
        if c["kind"] == "merge":
            cl.append("- MERGE {} <- {} (cross_paper={}, confidence={}): {}".format(
                c["canonical"], ", ".join(c["merged"]),
                c["cross_paper"], c["confidence"] or "n/a", c["justification"]))
        else:
            cl.append("- AUTO-CONFLICT on pair {}: {}".format(
                c["pair"], ", ".join(c["predicates"])))
    with open(os.path.join(args.outdir, "changes.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(cl) + "\n")

    print("nodes: {}, edges: {}, conflicts: {}".format(
        len(graph["nodes"]), len(edges), len(conflicts)))
    print("written to", os.path.abspath(args.outdir))


if __name__ == "__main__":
    main()
