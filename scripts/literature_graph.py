"""Build a citation graph around the thesis bibliography, using OpenAlex.

Jamie's LaTeX repos carry the seed set: every ``.bib`` entry is a work the thesis cites.
OpenAlex then supplies each work's references, so the graph shows both what the thesis
cites and what that cited literature cites — the "literature space" around fuel
mitigation modelling.

Outputs (under ``runtime/literature/``):

- ``seeds.csv`` — the bibliography entries with the OpenAlex match and its confidence
- ``nodes.csv`` — every work in the graph
- ``edges.csv`` — citing -> cited pairs
- ``graph.json`` — node-link form for a viewer
- ``summary.md`` — counts, top works by in-degree, topic mix

No API key is needed. OpenAlex asks for a ``mailto`` in the polite pool, given below.

Usage::

    python scripts/literature_graph.py --repos-root ..
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

OPENALEX = "https://api.openalex.org/works"
MAILTO = "femic-dev@ubc-fresh.local"
REPOS = (
    "Jamie-Iversen-MASc-Proposal",
    "Jamie-Iversen-MASc-Thesis",
    "Jamie-Iversen-MASc-Paper-1",
    "Jamie-Iversen-MASc-Paper-2",
)


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    """Return ``{key: {field: value}}`` for one BibTeX file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"@(\w+)\{([^,]+),", text):
        key = match.group(2).strip()
        start = match.end()
        depth = 1
        index = start
        while index < len(text) and depth:
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        body = text[start : index - 1]
        fields: dict[str, str] = {}
        for field in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?", body, re.S):
            fields[field.group(1).lower()] = " ".join(field.group(2).split())
        entries[key] = fields
    return entries


def _get(url: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode({**params, "mailto": MAILTO})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(f"{url}?{query}", timeout=30) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # OpenAlex answers 429 when the polite pool is busy. Back off explicitly
            # rather than hammering it; give up on the entry after the last attempt.
            if attempt == 5:
                return {}
            time.sleep(15 if exc.code == 429 else 3 * (attempt + 1))
        except Exception:  # noqa: BLE001
            # A malformed title should skip the entry, not abort the run.
            if attempt == 5:
                return {}
            time.sleep(3 * (attempt + 1))
    return {}


def resolve(fields: dict[str, str]) -> dict | None:
    """Resolve one bibliography entry to an OpenAlex work."""
    doi = fields.get("doi", "").strip()
    if doi:
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        payload = _get(OPENALEX, {"filter": f"doi:{doi}", "per-page": "1"})
        results = payload.get("results") or []
        if results:
            results[0]["_match"] = "doi"
            return results[0]
    title = " ".join(fields.get("title", "").strip("{} ").split())[:200]
    if not title:
        return None
    payload = _get(OPENALEX, {"search": title, "per-page": "1"})
    results = payload.get("results") or []
    if results:
        results[0]["_match"] = "title"
        return results[0]
    return None


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
    parser.add_argument("--sleep", type=float, default=1.1)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    # 1. Seed set: every bib entry across the writing repos.
    seeds: dict[str, dict[str, str]] = {}
    for repo in REPOS:
        for bib in (args.repos_root / repo).rglob("*.bib"):
            for key, fields in parse_bib(bib).items():
                seeds.setdefault(key, fields)
    print(f"seed entries: {len(seeds)}")

    # 2. Resolve each seed and record its references.
    rows: list[dict[str, object]] = []
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str]] = set()
    for index, (key, fields) in enumerate(sorted(seeds.items()), 1):
        work = resolve(fields)
        if work is None:
            rows.append({"key": key, "status": "unresolved", "title": fields.get("title", "")})
            continue
        short = _short(work)
        nodes[short["id"]] = short
        rows.append(
            {
                "key": key,
                "status": "resolved",
                "match": work.get("_match", ""),
                "openalex": short["id"],
                "doi": short["doi"],
                "year": short["year"],
                "title": short["title"],
                "cited_by": short["cited_by"],
                "topic": short["topic"],
            }
        )
        for ref in short["references"]:
            edges.add((short["id"], ref))
            nodes.setdefault(
                ref,
                {"id": ref, "doi": "", "title": "", "year": None, "cited_by": 0, "topic": "", "references": []},
            )
        if index % 25 == 0:
            print(f"  resolved {index}/{len(seeds)}")
        time.sleep(args.sleep)

    # 3. Give the referenced-only nodes a title, in batches, so the graph is readable.
    missing = [n for n, node in nodes.items() if not node["title"]]
    print(f"referenced-only nodes without a title: {len(missing)}")
    for start in range(0, len(missing), 50):
        batch = missing[start : start + 50]
        payload = _get(
            OPENALEX,
            {"filter": "openalex_id:" + "|".join(batch), "per-page": "50",
             "select": "id,title,publication_year,cited_by_count,primary_topic"},
        )
        for work in payload.get("results") or []:
            short = _short(work)
            if short["id"] in nodes:
                nodes[short["id"]].update(
                    {k: short[k] for k in ("title", "year", "cited_by", "topic")}
                )
        time.sleep(args.sleep)

    # 4. Write the artifacts.
    import csv

    with (args.out / "seeds.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.out / "nodes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["id", "doi", "title", "year", "cited_by", "topic", "in_degree"]
        )
        writer.writeheader()
        in_degree = Counter(target for _, target in edges)
        for node in sorted(nodes.values(), key=lambda n: -in_degree[n["id"]]):
            writer.writerow({**{k: node[k] for k in ("id", "doi", "title", "year", "cited_by", "topic")},
                             "in_degree": in_degree[node["id"]]})
    with (args.out / "edges.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["citing", "cited"])
        writer.writerows(sorted(edges))
    (args.out / "graph.json").write_text(
        json.dumps(
            {
                "nodes": list(nodes.values()),
                "edges": [{"source": s, "target": t} for s, t in sorted(edges)],
            },
            indent=1,
        ),
        encoding="utf-8",
    )

    # 5. Summary.
    resolved = [row for row in rows if row["status"] == "resolved"]
    by_key = {node["id"]: node for node in nodes.values()}
    top = sorted(
        (node for node in nodes.values() if node["title"]),
        key=lambda n: -in_degree[n["id"]],
    )[:20]
    topics = Counter(node["topic"] for node in nodes.values() if node["topic"])
    years = Counter(node["year"] for node in nodes.values() if node["year"])
    lines = [
        "# Literature graph summary",
        "",
        f"- seed bibliography entries: **{len(seeds)}**",
        f"- resolved against OpenAlex: **{len(resolved)}** "
        f"({len(resolved) / max(len(seeds), 1) * 100:.0f}%)",
        f"- nodes (works): **{len(nodes)}**",
        f"- citation edges: **{len(edges)}**",
        "",
        "## Most cited by the seed set and its references",
        "",
        "| in-degree | year | title |",
        "| ---: | ---: | --- |",
    ]
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
