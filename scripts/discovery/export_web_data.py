"""Export config / ledger YAML to JSON for the static web page (B11).

Output: web/data/lenses.json, web/data/ledger.json
"""

from __future__ import annotations

import json

from similitude import io

WEB = io.REPO_ROOT / "web" / "data"


def main() -> None:
    WEB.mkdir(parents=True, exist_ok=True)
    lenses = [{k: v for k, v in lens.items() if k != "min_scale"}
              for lens in io.load_lenses().values()]
    (WEB / "lenses.json").write_text(json.dumps(lenses, indent=1, ensure_ascii=False),
                                     encoding="utf-8")
    ledger = {body: io.load_yaml(io.REPO_ROOT / "ledger" / f"{body}.yaml")
              for body in ("moon", "mars")}
    (WEB / "ledger.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False,
                                                default=str), encoding="utf-8")
    print("wrote lenses.json, ledger.json")


if __name__ == "__main__":
    main()
