"""B8 — Analog Attention Index: how much has the planetary-analog literature looked at a place?

n_pubs = OpenAlex works whose title/abstract match
    "<place>" AND (analog OR analogue) AND (Mars OR Moon OR lunar OR planetary)
"Hidden" (DESIGN 2.2(6)) = high fidelity percentile AND low attention. Ambiguous names get a
geographic/feature qualifier (PLAN edge case: "Karakul" is also a sheep breed).
The exact query string and the query date are stored with every count.

Inputs : config/controls.yaml, config/seeds_m1.yaml, config/seeds_x1.yaml,
         optional data/derived/candidate_names.csv (key,name) written by discovery (B9)
Output : data/derived/attention.parquet  (key, name, query, n_pubs, source, date)
Usage  : python scripts/attention/openalex.py [--only-missing]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import time

import pandas as pd
import requests

from similitude import io

DERIVED = io.REPO_ROOT / "data" / "derived"
OUT = DERIVED / "attention.parquet"
API = "https://api.openalex.org/works"
HEADERS = {"User-Agent": "similitude-hackathon/0.1"}
CONTEXT = "(analog OR analogue) AND (Mars OR Moon OR lunar OR planetary)"

#: Place-name overrides: ambiguous or too-specific names -> literature name (+ qualifier).
OVERRIDES = {
    "karakul_structure": '"Karakul" AND (crater OR impact OR Pamir OR Tajikistan)',
    "harrat_khaybar": '"Harrat Khaybar" OR "Khaybar lava"',
    "harrat_rahat": '"Harrat Rahat"',
    "harrat_uwayrid": '"Harrat Uwayrid"',
    "semail_wadi_tayin_a": '"Semail" OR "Samail" OR "Oman ophiolite"',
    "semail_wadi_tayin_b": '"Semail" OR "Samail" OR "Oman ophiolite"',
    "semail_ibra": '"Semail" OR "Samail" OR "Oman ophiolite"',
    "semail_fizh": '"Semail" OR "Samail" OR "Oman ophiolite"',
    "semail_khawr_fakkan": '"Semail" OR "Samail" OR "Oman ophiolite"',
    "tibesti_emi_koussi": '"Emi Koussi" OR "Tibesti"',
    "lop_nur": '"Lop Nur" OR "Lop Nor"',
    "qaidam_dalangtan": '"Qaidam" OR "Dalangtan"',
    "salar_de_uyuni_edge": '"Uyuni"',
    "matanomadh": '"Matanomadh" OR "Kutch" OR "Kachchh"',
    "east_pamir_murghab": '"Pamir"',
    "west_kunlun_aksai_chin": '"Aksai Chin" OR "West Kunlun"',
    "changtang_north": '"Changtang" OR "Qiangtang"',
    "qiangtang_east": '"Changtang" OR "Qiangtang"',
    "kunlun_pass": '"Kunlun Pass" OR "Kunlun Mountain Pass"',
    "mongolian_altai_south": '"Mongolian Altai"',
    "tianshan_central": '"Tian Shan" OR "Tien Shan"',
    "puna_high": '"Puna"',
    "svalbard_adventdalen": '"Svalbard"',
    "atacama_yungay": '"Atacama"',
    "haughton_devon": '"Haughton" OR "Devon Island"',
    "haughton_devon_l2": '"Haughton" OR "Devon Island"',
    "devon_island": '"Haughton" OR "Devon Island"',
    "lake_salda": '"Salda"',
    "pilot_valley_utah": '"Pilot Valley"',
    "rio_tinto": '"Rio Tinto" OR "Río Tinto"',
    "wadi_rum": '"Wadi Rum"',
    "simpson_desert": '"Simpson Desert"',
    "beacon_valley": '"Beacon Valley"',
    "axel_heiberg_eureka": '"Axel Heiberg"',
    "yakutsk_lowland": '"Yakutsk" OR "Yakutia"',
    "west_siberia_lowland": '"West Siberian"',
    "kilauea_lava": '"Kilauea"',
    "lava_beds_california": '"Lava Beds"',
    "meteor_crater_arizona": '"Meteor Crater" OR "Barringer"',
    "sp_crater_black_point": '"SP Crater" OR "Black Point lava"',
    "sahara_lowlat_l2": '"Tibesti"',
    "troodos_olympus": '"Troodos"',
    "bay_of_islands": '"Bay of Islands"',
    "new_idria": '"New Idria"',
    "kempirsai": '"Kempirsai"',
    "haruj": '"Haruj"',
    "pinacate": '"Pinacate"',
    "craters_of_the_moon": '"Craters of the Moon National"',
    "bonneville": '"Bonneville Salt" OR "Bonneville Basin"',
    "chott_el_djerid": '"Chott el Djerid" OR "Chott el-Jerid" OR "Chott Djerid"',
    "makgadikgadi": '"Makgadikgadi"',
    "white_sands": '"White Sands"',
    "cuprite_nevada": '"Cuprite"',
    "painted_desert": '"Painted Desert" OR "Chinle Formation"',
    "hanksville_mancos": '"Hanksville" OR "Mancos Shale"',
    "peary_land": '"Peary Land"',
}


#: Admin-region names returned by reverse geocoding -> the names the analog literature uses.
REGION_ALIASES = {
    "Afar Region": '"Afar" OR "Danakil"',
    "Inuvik Region": '"Mackenzie King Island" OR "Queen Elizabeth Islands"',
    "Matruh": '"Western Desert" AND Egypt',
    "Ardakan County": '"Yazd" OR "Ardakan"',
    "Medina Province": '"Harrat Rahat" OR "Harrat Khaybar" OR "Medina"',
}


def default_place(name: str) -> str:
    """'Semail ophiolite, Wadi Tayin A (Oman)' -> '"Semail ophiolite"'."""
    base = re.sub(r"\(.*?\)", "", name).split(",")[0].strip()
    return f'"{base}"'


def entries() -> list[dict]:
    out = []
    for c in io.load_controls():
        out.append({"key": c["id"], "name": c["name"]})
    for f in ("seeds_m1.yaml", "seeds_x1.yaml"):
        for s in io.load_yaml(io.CONFIG_DIR / f)["seeds"]:
            out.append({"key": s["id"], "name": s["name"]})
    extra = DERIVED / "candidate_names.csv"
    if extra.exists():
        for r in pd.read_csv(extra).itertuples():
            out.append({"key": r.key, "name": r.name,
                        "place": getattr(r, "place", None) if hasattr(r, "place") else None})
    seen, uniq = set(), []
    for e in out:
        if e["key"] not in seen:
            seen.add(e["key"])
            uniq.append(e)
    return uniq


def build_query(e: dict) -> str:
    pl = e.get("place")
    if isinstance(pl, float):  # NaN from csv
        pl = None
    place = (OVERRIDES.get(e["key"]) or (pl and REGION_ALIASES.get(pl))
             or (pl and f'"{pl}"') or default_place(e["name"]))
    return f"({place}) AND {CONTEXT}"


class BudgetExhausted(RuntimeError):
    """OpenAlex free daily budget for this IP is used up (resets at midnight UTC)."""


def count(query: str, retries: int = 6) -> int | None:
    params = {"filter": f"title_and_abstract.search:{query}", "per-page": 1}
    key = os.environ.get("OPENALEX_API_KEY")  # optional personal key, never committed
    if key:
        params["api_key"] = key
    for k in range(retries):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return int(r.json()["meta"]["count"])
        if r.status_code == 429 and "budget" in r.text.lower():
            raise BudgetExhausted(r.json().get("message", "")[:200])
        time.sleep(2.0 * (k + 1))
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-missing", action="store_true")
    args = ap.parse_args()
    today = dt.date.today().isoformat()
    prev = pd.read_parquet(OUT) if OUT.exists() else pd.DataFrame(columns=["key"])
    have = set(prev["key"]) if args.only_missing else set()
    rows = [r for r in prev.to_dict("records") if r["key"] in have]
    for e in entries():
        if e["key"] in have:
            continue
        q = build_query(e)
        try:
            n = count(q)
        except BudgetExhausted as exc:
            # leave the remaining keys missing so the next --only-missing run fills them
            print(f"OpenAlex daily budget exhausted, stopping early: {exc}")
            break
        rows.append({"key": e["key"], "name": e["name"], "query": q, "n_pubs": n,
                     "source": "OpenAlex", "date": today})
        print(f"{e['key']:28s} {n!s:>5}  {q[:90]}")
        time.sleep(1.1)
    df = pd.DataFrame(rows)
    df["n_pubs"] = df["n_pubs"].astype("Int64")
    df.to_parquet(OUT, index=False)
    a = df.set_index("key")["n_pubs"]
    if "atacama_yungay" in a and "harrat_khaybar" in a:
        print(f"R13: Atacama {a['atacama_yungay']} vs Harrat Khaybar {a['harrat_khaybar']}")


if __name__ == "__main__":
    main()
