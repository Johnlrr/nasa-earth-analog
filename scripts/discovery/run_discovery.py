"""B9 — run discovery and export web/data/candidates.geojson.

Fidelity source: data/derived/fidelity.parquet (A8, Bao) if present, else the provisional scorer
output (scripts/provisional/score_b.py) -> metadata.provisional = true.
Rank / null cells chosen as candidates get a place name by reverse geocoding (OSM Nominatim,
coordinates only, 1 request/s, cached in data/derived/geocode_cache.json); their Attention Index
is then queried (scripts/attention/openalex.py). Controls and decoys are exported too (role
control / decoy) so the web map shows the validation cases next to the discoveries.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
import time

import pandas as pd
import requests

from similitude import discovery as disc
from similitude import io

DERIVED = io.REPO_ROOT / "data" / "derived"
OUT = io.REPO_ROOT / "web" / "data" / "candidates.geojson"
GEOCODE_CACHE = DERIVED / "geocode_cache.json"
LENSES = ("M1", "X1", "L1", "L2")


def load_fidelity() -> tuple[pd.DataFrame, pd.DataFrame | None, bool]:
    final = DERIVED / "fidelity.parquet"
    if final.exists():
        return pd.read_parquet(final), None, False
    fid = pd.read_parquet(DERIVED / "fidelity_provisional.parquet")
    z = pd.read_parquet(DERIVED / "fidelity_z_provisional.parquet")
    return fid, z, True


def reverse_geocode(lat: float, lon: float, cache: dict) -> tuple[str, str]:
    key = f"{lat:.3f},{lon:.3f}"
    if key not in cache:
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
                         params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 8,
                                 "accept-language": "en"},
                         headers={"User-Agent": "similitude-hackathon/0.1 (research prototype)"},
                         timeout=30)
        cache[key] = r.json() if r.ok else {}
        time.sleep(1.1)
    j = cache[key]
    a = j.get("address", {})
    local = a.get("county") or a.get("state_district") or j.get("name") or ""
    region = a.get("state") or a.get("region") or ""
    # generic admin names ("Zone 1", "District 3") are useless for a literature query
    if not local or re.match(r"^(Zone|District|Region|County|Area)\s*\d+$", local):
        local = region or local or "unnamed area"
    display = f"{local}, {region}" if region and region != local else local
    return display, local, a.get("country", "")


def seed_meta() -> dict:
    out = {}
    for f in ("seeds_m1.yaml", "seeds_x1.yaml"):
        for s in io.load_yaml(io.CONFIG_DIR / f)["seeds"]:
            out[f"seed_{s['id']}"] = s
    return out


def main() -> None:
    fid, ztab, provisional = load_fidelity()
    lenses = io.load_lenses()
    seeds = seed_meta()
    controls = {f"ctl_{c['id']}": c for c in io.load_controls()}
    cache = json.loads(GEOCODE_CACHE.read_text(encoding="utf-8")) if GEOCODE_CACHE.exists() else {}
    att_path = DERIVED / "attention.parquet"

    def attention_table() -> dict:
        a = pd.read_parquet(att_path)
        return {r.key: (None if pd.isna(r.n_pubs) else int(r.n_pubs)) for r in a.itertuples()}, a

    features, summary = [], {}
    for lens_id in LENSES:
        f = fid[fid["lens_id"] == lens_id]
        earth_path = DERIVED / f"earth_{lens_id}.parquet"
        if f.empty or not earth_path.exists():
            summary[lens_id] = {"status": "no fidelity data yet"}
            continue
        lens = lenses[lens_id]
        earth = pd.read_parquet(earth_path)
        targets = pd.read_parquet(DERIVED / f"targets_{lens_id}.parquet")
        tref = targets[targets["is_reference"]].set_index("target_id")
        best = disc.best_target(f)

        # 1st pass: names + attention for non-seed candidates passing fidelity
        att, _ = attention_table()
        pre = disc.select_hidden(best, earth, att, lens, per_lens=15)
        names = []
        for _, r in pre.iterrows():
            if str(r["cell_id"]).startswith(("rank", "null")) and r["cell_id"] not in att:
                display, place, country = reverse_geocode(r["lat"], r["lon"], cache)
                names.append({"key": r["cell_id"], "name": f"{display} ({country})",
                              "place": place})
        GEOCODE_CACHE.write_text(json.dumps(cache), encoding="utf-8")
        if names:
            cn = DERIVED / "candidate_names.csv"
            old = pd.read_csv(cn) if cn.exists() else pd.DataFrame(columns=["key", "name", "place"])
            pd.concat([old, pd.DataFrame(names)]).drop_duplicates("key", keep="last").to_csv(
                cn, index=False)
            subprocess.run([sys.executable, str(io.REPO_ROOT / "scripts/attention/openalex.py"),
                            "--only-missing"], check=True)
        att, att_df = attention_table()
        att_q = att_df.set_index("key")
        hidden = disc.select_hidden(best, earth, att, lens, per_lens=5)

        cn_path = DERIVED / "candidate_names.csv"
        cname = (pd.read_csv(cn_path).set_index("key") if cn_path.exists()
                 else pd.DataFrame(columns=["name", "place"]))
        earth_i = earth.set_index("cell_id")

        def build(row, role, lens_id=lens_id, lens=lens, earth_i=earth_i, tref=tref,
                  cname=cname, att_q=att_q):
            cid = row["cell_id"]
            er = earth_i.loc[cid]
            zr = None
            if ztab is not None:
                zz = ztab[(ztab["cell_id"] == cid) & (ztab["lens_id"] == lens_id)
                          & (ztab["target_id"] == row["target_id"])]
                zr = zz.iloc[0] if len(zz) else None
            tr = tref.loc[row["target_id"]] if row["target_id"] in tref.index else None
            ls = disc.lens_score(row, lens, zr, tr, er)
            if cid in seeds:
                s = seeds[cid]
                name, country, klass = s["name"], s["country"], s.get("class")
            elif cid in controls:
                c = controls[cid]
                name, country, klass = c["name"], "", None
            elif cid in cname.index:
                name, country, klass = cname.loc[cid, "name"], "", None
            else:
                name, country, klass = f"Cell {cid}", "", None
            key = disc.attention_key(row)
            aq = att_q.loc[key] if key in att_q.index else None
            status = disc.evidence_status(lens_id, role)
            note = ("Provisional diagonal scorer (scripts/provisional/score_b.py) until the A5/A8"
                    " fidelity engine is merged." if provisional else "")
            if ls["no_analog"]:
                note += (" Best Earth cell for this target is still > 2 sigma: reported as"
                         " 'no natural analog' for the target, with this cell as Earth's best.")
            rates = {"freeze_thaw_cycles_per_yr": None, "wind_exceedance_frac": None}
            if lens_id == "X1":
                rates["freeze_thaw_cycles_per_yr"] = disc._round(er.get("ft_yr"), 1)
            props = {
                "id": f"{lens_id}-{cid}", "name": str(name), "country": str(country or ""),
                "lat": round(float(er["lat"]), 4), "lon": round(float(er["lon"]), 4),
                "footprint_km": float(lens["footprint_km"]), "role": role,
                "process_title": disc.PROCESS_TITLE.get((lens_id, klass))
                or disc.PROCESS_TITLE[(lens_id, None)],
                "lens_scores": {lens_id: ls},
                "process_rates": rates,
                "test_here": [{**t, "lens": lens_id} for t in disc.TEST_HERE[lens_id]],
                "cannot_test": disc.cannot_test(lens_id),
                "attention": {"n_pubs": None if aq is None or pd.isna(aq["n_pubs"])
                              else int(aq["n_pubs"]),
                              "query": "" if aq is None else str(aq["query"]),
                              "source": "OpenAlex",
                              "date": dt.date.today().isoformat() if aq is None
                              else str(aq["date"])},
                "access": {"travel_time_h": None, "protected_area": None,
                           "note": "Accessibility not assessed (optional item, not done)."},
                "in_exclusion_buffer": bool(er["in_exclusion_buffer"]),
                "evidence_status": status, "evidence_note": note.strip(),
                "data_sources": disc.DATA_SOURCES[lens_id],
            }
            return disc.feature(props)

        for _, r in hidden.iterrows():
            features.append(build(r, "hidden"))
        for cid, c in controls.items():
            if c["lens_id"] != lens_id:
                continue
            tgt = c.get("target_id")
            rows = f[(f["cell_id"] == cid) & ((f["target_id"] == tgt) if tgt else True)]
            if rows.empty:
                continue
            row = rows.sort_values("d").iloc[0]
            features.append(build(row, "decoy" if c["role"] == "decoy" else "control"))
        summary[lens_id] = {
            "n_scored": int(best["cell_id"].nunique()),
            "n_null": int(f["n_null"].max()) if "n_null" in f else None,
            "n_hidden": int(len(hidden)),
            "best_sigma": round(float(best["sigma"].min()), 3),
            "no_hidden_found": bool(hidden.empty),
        }

    review_path = io.CONFIG_DIR / "review_b10.yaml"
    review = io.load_yaml(review_path)["features"] if review_path.exists() else {}
    for ft in features:
        p = ft["properties"]
        rv = review.get(p["id"])
        if not rv:
            continue
        if rv.get("action") == "downgrade":
            p["evidence_status"] = rv.get("status", "hypothesis")
        if rv.get("process_title"):
            p["process_title"] = rv["process_title"]
        p["evidence_note"] = (p.get("evidence_note", "") + " " + rv.get("note", "")).strip()

    doc = {"type": "FeatureCollection",
           "metadata": {"generated": dt.datetime.now().isoformat(timespec="minutes"),
                        "provisional": provisional, "mock": False, "lenses": summary,
                        "thresholds": {"percentile_min": disc.PERCENTILE_MIN,
                                       "sigma_max_without_percentile": disc.SIGMA_MAX_NO_PCT,
                                       "attention_max": disc.ATTENTION_MAX}},
           "features": features}
    n = io.write_candidates(doc, OUT)
    print(f"wrote {n} features -> {OUT}")
    print(json.dumps(summary, indent=1))
    for ft in features:
        p = ft["properties"]
        ls = next(iter(p["lens_scores"].values()))
        print(f"{p['role']:8s} {p['id']:38s} {p['name'][:40]:40s} sigma={ls['sigma']:6.2f} "
              f"pct={ls['percentile']} att={p['attention']['n_pubs']} {p['evidence_status']}")


if __name__ == "__main__":
    main()
