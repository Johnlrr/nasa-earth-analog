"""Assemble the static site exactly as GitHub Pages serves it (workflow and local preview).

    python scripts/build_site.py _site            # what .github/workflows/pages.yml runs
    python scripts/build_site.py --serve 8000     # build into a temp folder and serve it locally

The page in web/ links to files that live in docs/ (validation report, test protocols, figures) and
to the slide deck in slides/. Serving web/ alone leaves those links broken; this script copies them
next to the page so the local preview and the deployed site are the same tree. Standard library
only, so the workflow needs no install step.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (source, destination inside the site); a missing optional source is skipped
COPIES = [
    ("docs/validation_report.md", "validation_report.md"),
    ("docs/test_protocols.md", "test_protocols.md"),
    ("docs/field_facility.md", "field_facility.md"),
    ("docs/figures", "figures"),
    ("slides/SIMILITUDE-slides.pdf", "SIMILITUDE-slides.pdf"),
]
# local-only folders that must never be published
SKIP = shutil.ignore_patterns(".taste-skill", "__pycache__", "*.mock.geojson.bak")


def build(out: Path) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "web", out, ignore=SKIP)
    done = []
    for src, dst in COPIES:
        s = ROOT / src
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, out / dst, dirs_exist_ok=True)
        else:
            shutil.copy2(s, out / dst)
        done.append(dst)
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", help="output folder (e.g. _site)")
    ap.add_argument("--serve", type=int, metavar="PORT", help="build to a temp folder and serve it")
    a = ap.parse_args()
    if a.serve:
        out = Path(tempfile.mkdtemp(prefix="similitude_site_")) / "site"
        print("built:", ", ".join(build(out)))
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        print(f"serving {out} at http://localhost:{a.serve}/")
        http.server.ThreadingHTTPServer(("127.0.0.1", a.serve), handler).serve_forever()
    elif a.out:
        print("built:", ", ".join(build(Path(a.out))))
    else:
        ap.error("give an output folder or --serve PORT")


if __name__ == "__main__":
    main()
