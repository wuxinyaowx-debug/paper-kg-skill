"""Discover material files under --input and build a paragraph index.

Usage:
    python kg_index.py --input /input --out /app/work/paragraph_index.json

The walker is structure-tolerant: any dict carrying both an id-like key and a
text-like key is indexed as a paragraph. source_id is taken from an explicit
record field when present, otherwise inferred from the file name
(primary-material.json -> "primary", secondary-material.json -> "secondary",
anything else -> file stem). Actual field names are discovered, never assumed.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_common import dump_json, load_json

ID_KEYS = ("paragraph_id", "para_id", "pid", "id")
TEXT_KEYS = ("text", "content", "paragraph", "sentence", "body")
SOURCE_KEYS = ("source_id", "source", "paper_id", "doc_id")
MATERIAL_HINTS = ("material", "corpus", "manifest", "paper")


def infer_source_id(filename):
    stem = os.path.splitext(os.path.basename(filename))[0].lower()
    if "primary" in stem:
        return "primary"
    if "secondary" in stem:
        return "secondary"
    return stem


def walk(node, source_id, fname, out, seen):
    if isinstance(node, dict):
        sid = source_id
        for k in SOURCE_KEYS:
            if isinstance(node.get(k), str) and node[k].strip():
                sid = node[k].strip()
                break
        pid = next((node[k] for k in ID_KEYS
                    if isinstance(node.get(k), (str, int))), None)
        txt = next((node[k] for k in TEXT_KEYS
                    if isinstance(node.get(k), str) and len(node[k]) > 20), None)
        if pid is not None and txt:
            key = (sid, str(pid))
            # keep the longest text if duplicated across files
            if key not in seen or len(txt) > len(seen[key]["text"]):
                rec = {"source_id": sid, "paragraph_id": str(pid),
                       "text": txt, "file": fname}
                seen[key] = rec
        for v in node.values():
            walk(v, sid, fname, out, seen)
    elif isinstance(node, list):
        for v in node:
            walk(v, source_id, fname, out, seen)


def extract_papers(manifest, fname):
    papers = []
    if not isinstance(manifest, dict):
        return papers
    items = manifest.get("papers") or manifest.get("documents") or \
        manifest.get("sources") or manifest.get("items") or []
    if isinstance(items, dict):
        items = [dict(v, source_id=k) if isinstance(v, dict) else v
                 for k, v in items.items()]
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        papers.append({
            "source_id": it.get("source_id") or it.get("id") or it.get("key"),
            "doi": it.get("doi") or it.get("DOI"),
            "title": it.get("title"),
            "authors": it.get("authors"),
            "license": it.get("license") or it.get("licence"),
            "sha256": it.get("sha256") or it.get("hash"),
            "manifest_file": fname,
        })
    return papers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--out", default="/app/work/paragraph_index.json")
    args = ap.parse_args()

    files = []
    for root, _dirs, names in os.walk(args.input):
        for n in sorted(names):
            if n.lower().endswith(".json") and any(
                    h in n.lower() for h in MATERIAL_HINTS):
                files.append(os.path.join(root, n))
    if not files:  # fall back to every json except case/task metadata
        for root, _dirs, names in os.walk(args.input):
            for n in sorted(names):
                if n.lower().endswith(".json") and n.lower() not in (
                        "case.json", "config.json"):
                    files.append(os.path.join(root, n))

    seen, papers = {}, []
    for f in files:
        fname = os.path.basename(f)
        try:
            data = load_json(f)
        except Exception as e:  # malformed json must not kill the run
            print("WARN: cannot parse {}: {}".format(fname, e))
            continue
        walk(data, infer_source_id(fname), fname, [], seen)
        if "manifest" in fname.lower():
            papers.extend(extract_papers(data, fname))

    paragraphs = sorted(seen.values(),
                        key=lambda r: (r["source_id"], r["paragraph_id"]))
    out = {"input_dir": os.path.abspath(args.input),
           "files_scanned": [os.path.basename(f) for f in files],
           "papers": papers, "paragraphs": paragraphs}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    dump_json(out, args.out)

    by_source = {}
    for p in paragraphs:
        by_source[p["source_id"]] = by_source.get(p["source_id"], 0) + 1
    print("files_scanned:", len(files))
    for s, c in sorted(by_source.items()):
        print("  source_id={}: {} paragraphs".format(s, c))
    print("papers_from_manifest:", len(papers))
    print("total_paragraphs:", len(paragraphs))
    if not paragraphs:
        print("WARN: no paragraphs indexed; check material file structure "
              "and read the files directly before proceeding.")


if __name__ == "__main__":
    main()
