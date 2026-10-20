"""Create the base-name VDYP cache aliases a resume preflight expects.

The build leaves TSA-scoped caches (`vdyp_ply-tsa23.feather`, `vdyp_lyr-tsa23.feather`,
`vdyp_results-tsa23.pkl`), while the preflight and the pipeline look for the unscoped
base names. Rather than keep those aliases as undocumented, hand-made symlinks, this
script creates them idempotently.

Usage::

    python scripts/link_vdyp_caches.py --instance-root .
    python scripts/link_vdyp_caches.py --instance-root . --apply

Dry run by default.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# (base name the code expects, TSA-scoped artifact the build produced)
ALIASES = (
    ("vdyp_ply.feather", "vdyp_ply-tsa23.feather"),
    ("vdyp_lyr.feather", "vdyp_lyr-tsa23.feather"),
    ("vdyp_results.pkl", "vdyp_results-tsa23.pkl"),
)


def plan(instance_root: Path) -> list[tuple[Path, Path]]:
    """Return the (base, scoped target) aliases that are missing and can be created."""
    data = instance_root / "data"
    pending: list[tuple[Path, Path]] = []
    for base, scoped in ALIASES:
        link = data / base
        target = data / scoped
        if link.exists() or link.is_symlink():
            continue
        if target.exists():
            pending.append((link, target))
    return pending


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-root", type=Path, default=Path("."), dest="instance_root")
    parser.add_argument("--apply", action="store_true", help="create the links")
    args = parser.parse_args()

    root = args.instance_root.resolve()
    pending = plan(root)
    if not pending:
        print("All base-name cache aliases are already present (or no scoped cache exists).")
        return
    for link, target in pending:
        print(f"{'link' if args.apply else 'would link'}: data/{link.name} -> {target.name}")
        if args.apply:
            link.symlink_to(target.name)
    if not args.apply:
        print(f"\n{len(pending)} link(s) would be created. Re-run with --apply.")
        return
    print(f"\nCreated {len(pending)} link(s). data/ is gitignored, so nothing to commit.")


if __name__ == "__main__":
    sys.exit(main())
