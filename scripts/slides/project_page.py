"""docs/submission_kit.md -> docs/project_page.md: the form text with the number keys and Markdown
emphasis removed, ready to paste field by field into the Space Apps Project page.

    python scripts/slides/project_page.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "docs" / "submission_kit.md"
OUT = ROOT / "docs" / "project_page.md"

# a key bracket holds at least one `key`; the text in it is never meant for readers
KEY_BRACKET = re.compile(r"\s*\[[^\[\]]*`[A-Za-z0-9_]+`[^\[\]]*\]")


def strip(text: str) -> str:
    text = KEY_BRACKET.sub("", text)
    return text.replace("**", "")


def main() -> None:
    kit = KIT.read_text(encoding="utf-8")
    start = kit.index("## Project name")
    end = kit.index("\n---\n", start)
    body = strip(kit[start:end]).rstrip() + "\n"
    left = re.findall(r"`[A-Za-z0-9_]+` =", body)
    assert not left, f"keys left in the paste-ready text: {left[:3]}"
    head = ("# Project page — paste-ready (generated from docs/submission_kit.md; "
            "do not edit here)\n\n"
            "Paste each section into the field of the same name. "
            "Fill every ⟨TEAM⟩ before submitting.\n\n")
    OUT.write_text(head + body, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(body.split())} words")


if __name__ == "__main__":
    main()
