"""Build a citation graph around the thesis bibliography, using Crossref + OpenAlex.

Jamie's LaTeX repos carry the seed set: every ``.bib`` entry is a work the thesis cites.
Crossref resolves a title to a DOI (it has generous limits and no key requirement), and
OpenAlex then supplies the work's references. The result is the "literature space"
around fuel mitigation modelling: what the thesis cites, and what that literature cites.

Why Crossref first: only 35 of the 257 seed entries carry a DOI, so title matching is
mandatory. OpenAlex's free-text search endpoint rate-limits aggressively from a shared
host (HTTP 429); Crossref's ``query.bibliographic`` does not, and OpenAlex by DOI is a
single cheap lookup per work.

Outputs (under ``runtime/literature/``):

- ``seeds.csv`` — each bib entry, the resolved DOI, and the match method/confidence
- ``nodes.csv`` — every work in the graph, with in-degree
- ``edges.csv`` — citing -> cited pairs
- ``graph.json`` — node-link form for a viewer
- ``summary.md`` — counts, top works by in-degree, topic mix, publication years

Usage::

    python scripts/literature_graph.py --repos-root .. --limit 10   # smoke test
    python scripts/literature_graph.py --repos-root ..
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"
MAILTO = "femic-dev@ubc-fresh.local"
REPOS = (
    "Jamie-Iversen-MASc-Proposal",
    "Jamie-Iversen-MASc-Thesis",
    "Jamie-Iversen-MASc-Paper-1",
    "Jamie-Iversen-MASc-Paper-2",
)


def _get_json(url: str, params: dict[str, str] | None = None, *, attempts: int = 4) -> dict:
    """GET JSON with explicit 429 handling. Returns {} when the resource cannot be read."""
    query = urllib.parse.urlencode({**(params or {}), "mailto": MAILTO})
    full = f"{url}?{query}" if query else url
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(full, headers={"User-Agent": f"tsa23-litgraph/1.0 (mailto:{MAILTO})"})
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if attempt == attempts - 1:
                return {}
            time.sleep(20 if exc.code == 429 else 2 * (attempt + 1))
        except Exception:  # noqa: BLE001
            if attempt == attempts - 1:
                return {}
            time.sleep(2 * (attempt + 1))
    return {}


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    """Return ``{key: {field: value}}`` for one BibTeX file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"@(\w+)\{([^,]+),", text):
        start = match.end()
        depth = 1
        index = start
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        body = text[start : index - 1]
        fields: dict[str, str] = {}
        for field in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?", body, re.S):
            fields[field.group(1).lower()] = " ".join(field.group(2).split())
        entries[match.group(2).strip()] = fields
    return entries


def _norm(title: str) -> str:
    """Normalise a title for similarity comparison."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def crossref_doi(title: str, doi_hint: str = "") -> tuple[str, str]:
    """Return ``(doi, method)`` for a bibliography entry, or ``("", "")``."""
    if doi_hint:
        doi = doi_hint.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        if doi:
            return doi, "bibtex"
    if not title:
        return "", ""
    payload = _get_json(CROSSREF, {"query.bibliographic": title[:200], "rows": "1",
                                   "select": "DOI,title"})
    items = (payload.get("message") or {}).get("items") or []
    if not items:
        return "", ""
    candidate = items[0]
    candidate_title = (candidate.get("title") or [""])[0]
    score = difflib.SequenceMatcher(None, _norm(title), _norm(candidate_title)).ratio()
    if score < 0.86:
        return "", f"weak:{score:.2f}"
    return candidate.get("DOI", ""), f"crossref:{score:.2f}"


def openalex_work(doi: str) -> dict:
    """Return the OpenAlex work for a DOI, or {}."""
    if not doi:
        return {}
    payload = _get_json(f"{OPENALEX}/https://doi.org/{doi}", {})
    return payload if payload.get("id") else {}


def _short(work: dict) -> dict:
    """Reduce an OpenAlex work to the fields the graph needs."""
    topic = (work.get("primary_topic") or {}).get("display_name")
    return {
        "id": work.get("id", "").rsplit("/", 1)[-1],
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "title": work.get("title") or work.get("display_name") or "",
        "year": work.get("publication_year"),
        "cited_by": work.get("cited_by_count", 0),
        "topic": topic or "",
        "references": [ref.rsplit("/", 1)[-1] for ref in work.get("referenced_works", [])],
    }


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, default=Path(".."), dest="repos_root")
    parser.add_argument("--out", type=Path, default=Path("runtime/literature"))
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--limit", type=int, default=0, help="only process the first N entries")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    seeds: dict[str, dict[str, str]] = {}
    for repo in REPOS:
        for bib in (args.repos_root / repo).rglob("*.bib"):
            for key, fields in parse_bib(bib).items():
                seeds.setdefault(key, fields)
    items = sorted(seeds.items())
    if args.limit:
        items = items[: args.limit]
    print(f"seed entries: {len(seeds)}; processing {len(items)}")

    rows: list[dict[str, object]] = []
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str]] = set()
    for index, (key, fields) in enumerate(items, 1):
        doi, method = crossref_doi(fields.get("title", ""), fields.get("doi", ""))
        work = openalex_work(doi) if doi else {}
        if not work:
            rows.append({"key": key, "status": "unresolved", "method": method,
                         "title": fields.get("title", "")})
        else:
            short = _short(work)
            nodes[short["id"]] = short
            rows.append({"key": key, "status": "resolved", "method": method,
                         "openalex": short["id"], "doi": short["doi"],
                         "year": short["year"], "title": short["title"],
                         "cited_by": short["cited_by"], "topic": short["topic"]})
            for ref in short["references"]:
                edges.add((short["id"], ref))
                nodes.setdefault(ref, {"id": ref, "doi": "", "title": "", "year": None,
                                       "cited_by": 0, "topic": "", "references": []})
        if index % 20 == 0:
            print(f"  {index}/{len(items)} (resolved {sum(1 for r in rows if r['status'] == 'resolved')})")
        time.sleep(args.sleep)

    # Titles for the referenced-only nodes, so the graph is readable.
    missing = [n for n, node in nodes.items() if not node["title"]]
    print(f"referenced-only nodes without a title: {len(missing)}")
    for start in range(0, len(missing), 50):
        batch = missing[start : start + 50]
        payload = _get_json(
            OPENALEX,
            {"filter": "openalex_id:" + "|".join(batch), "per-page": "50",
             "select": "id,title,publication_year,cited_by_count,primary_topic"},
        )
        for work in payload.get("results") or []:
            short = _short(work)
            if short["id"] in nodes:
                nodes[short["id"]].update({k: short[k] for k in ("title", "year", "cited_by", "topic")})
        time.sleep(args.sleep)

    import csv

    with (args.out / "seeds.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["key", "status", "method", "openalex", "doi", "year", "title",
                        "cited_by", "topic"],
            restval="",
        )
        writer.writeheader()
        writer.writerows(rows)
    in_degree = Counter(target for _, target in edges)
    with (args.out / "nodes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "doi", "title", "year", "cited_by", "topic", "in_degree"])
        writer.writeheader()
        for node in sorted(nodes.values(), key=lambda n: -in_degree[n["id"]]):
            writer.writerow({**{k: node[k] for k in ("id", "doi", "title", "year", "cited_by", "topic")},
                             "in_degree": in_degree[node["id"]]})
    with (args.out / "edges.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["citing", "cited"])
        writer.writerows(sorted(edges))
    (args.out / "graph.json").write_text(
        json.dumps({"nodes": list(nodes.values()),
                    "edges": [{"source": s, "target": t} for s, t in sorted(edges)]}, indent=1),
        encoding="utf-8",
    )

    resolved = [row for row in rows if row["status"] == "resolved"]
    top = sorted((n for n in nodes.values() if n["title"]), key=lambda n: -in_degree[n["id"]])[:20]
    topics = Counter(node["topic"] for node in nodes.values() if node["topic"])
    years = Counter(node["year"] for node in nodes.values() if node["year"])
    lines = [
        "# Literature graph summary", "",
        f"- seed bibliography entries: **{len(seeds)}** (processed {len(items)})",
        f"- resolved: **{len(resolved)}** ({len(resolved) / max(len(items), 1) * 100:.0f}%)",
        f"- nodes (works): **{len(nodes)}**",
        f"- citation edges: **{len(edges)}**", "",
        "## Match methods", "", "| method | entries |", "| --- | ---: |",
    ]
    for method, count in Counter(row.get("method", "") for row in rows).most_common():
        lines.append(f"| {method or '(none)'} | {count} |")
    lines += ["", "## Most cited within the seed neighbourhood", "",
              "| in-degree | year | title |", "| ---: | ---: | --- |"]
    for node in top:
        lines.append(f"| {in_degree[node['id']]} | {node['year']} | {node['title'][:90]} |")
    lines += ["", "## Topic mix (OpenAlex primary topic)", "", "| works | topic |", "| ---: | --- |"]
    for topic, count in topics.most_common(15):
        lines.append(f"| {count} | {topic} |")
    lines += ["", "## Publication years", "", "| year | works |", "| ---: | ---: |"]
    for year in sorted(y for y in years if y):
        lines.append(f"| {year} | {years[year]} |")
    (args.out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}/{{seeds,nodes,edges}}.csv, graph.json, summary.md")


if __name__ == "__main__":
    main()
