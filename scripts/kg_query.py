"""Execute queries against a built graph and return evidence-bound answers.

Usage:
    python kg_query.py --graph /app/output/graph.json \
        --queries /app/work/queries.json --out /app/output/query_results.json

Query file: a JSON list. Each item needs an "id" and a "type":
  {"id": "Q1", "type": "entity",   "name": "TiO2"}           # one node + its edges
  {"id": "Q2", "type": "compare",  "entity_a": "...", "entity_b": "..."}
  {"id": "Q3", "type": "evidence", "edge_id": "R_..."}       # or "node_id": "N_..."
  {"id": "Q4", "type": "search",   "text": "spin coating"}   # free-text over nodes
Every result carries matched nodes/edges with full evidence, or status
"no_result" with an explicit reason. Nothing is fabricated.
"""
import argparse
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_common import dump_json, load_json, norm


def find_nodes(graph, text):
    t = norm(text)
    hits = []
    for n in graph["nodes"]:
        cands = [n["name"], n["normalized"]] + n.get("aliases", [])
        if any(t and t in norm(c) or norm(c) == t for c in cands):
            hits.append(n)
    return hits


def edges_of(graph, node_ids):
    return [e for e in graph["edges"]
            if e["subject"] in node_ids or e["object"] in node_ids]


def node_view(n):
    return {"node_id": n["node_id"], "name": n["name"], "type": n["type"],
            "aliases": n.get("aliases", []), "sources": n.get("sources", []),
            "merged_from": n.get("merged_from", [])}


def edge_view(e):
    return e  # edges already carry names + evidence


def run_query(graph, q):
    qt = q.get("type")
    if qt == "entity":
        hits = find_nodes(graph, q.get("name", ""))
        if not hits:
            return {"status": "no_result",
                    "reason": "no node matching '{}'".format(q.get("name")),
                    "nodes": [], "edges": []}
        ids = {n["node_id"] for n in hits}
        return {"status": "ok", "nodes": [node_view(n) for n in hits],
                "edges": [edge_view(e) for e in edges_of(graph, ids)]}
    if qt == "compare":
        a = find_nodes(graph, q.get("entity_a", ""))
        b = find_nodes(graph, q.get("entity_b", ""))
        if not a or not b:
            return {"status": "no_result",
                    "reason": "unmatched side(s): {}".format(
                        [s for s, h in (("entity_a", a), ("entity_b", b)) if not h]),
                    "nodes": [], "edges": []}
        ids = {n["node_id"] for n in a + b}
        ea, eb = edges_of(graph, {n["node_id"] for n in a}), \
                 edges_of(graph, {n["node_id"] for n in b})
        shared = sorted({e["object"] for e in ea} & {e["object"] for e in eb} |
                        {e["subject"] for e in ea} & {e["subject"] for e in eb})
        return {"status": "ok",
                "nodes": [node_view(n) for n in a + b],
                "edges": [edge_view(e) for e in {e["edge_id"]: e for e in ea + eb}.values()],
                "shared_neighbour_ids": shared,
                "note": "shared neighbours indicate comparison points; check "
                        "each edge's evidence and source_id before concluding "
                        "the two papers used the same sample/conditions"}
    if qt == "evidence":
        if q.get("edge_id"):
            hits = [e for e in graph["edges"] if e["edge_id"] == q["edge_id"]]
            if not hits:
                return {"status": "no_result",
                        "reason": "edge_id '{}' not found".format(q["edge_id"]),
                        "nodes": [], "edges": []}
            return {"status": "ok", "nodes": [], "edges": [edge_view(h) for h in hits]}
        if q.get("node_id"):
            hits = [n for n in graph["nodes"] if n["node_id"] == q["node_id"]]
            if not hits:
                return {"status": "no_result",
                        "reason": "node_id '{}' not found".format(q["node_id"]),
                        "nodes": [], "edges": []}
            return {"status": "ok", "nodes": [node_view(h) for h in hits], "edges": []}
        return {"status": "no_result", "reason": "evidence query needs edge_id or node_id",
                "nodes": [], "edges": []}
    if qt == "search":
        hits = find_nodes(graph, q.get("text", ""))
        if not hits:
            return {"status": "no_result",
                    "reason": "no node contains '{}'".format(q.get("text")),
                    "nodes": [], "edges": []}
        return {"status": "ok", "nodes": [node_view(n) for n in hits], "edges": []}
    return {"status": "no_result", "reason": "unknown query type '{}'".format(qt),
            "nodes": [], "edges": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    graph = load_json(args.graph)
    queries = load_json(args.queries)
    results = []
    for q in queries:
        r = run_query(graph, q)
        r["query"] = q
        results.append(r)
        print("{} [{}]: {} ({} nodes, {} edges)".format(
            q.get("id", "?"), q.get("type"), r["status"],
            len(r.get("nodes", [])), len(r.get("edges", []))))
        if r["status"] != "ok":
            print("   reason:", r.get("reason"))
    dump_json({"graph_stats": {"nodes": len(graph["nodes"]),
                               "edges": len(graph["edges"])},
               "results": results}, args.out)
    print("written to", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
