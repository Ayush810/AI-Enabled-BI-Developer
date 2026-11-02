"""BI + AI (Power BI with Fabric / Copilot / AI skills) salary model.

Usage: python build_biai.py <data_dir> <out_dir> [target_years]   (default 5.583 = 5 years 7 months)

Reads <data_dir>/biai_roles.csv and <data_dir>/biai_postings.csv.

There is no portal title for "Power BI + AI developer", so the profile is built from
AmbitionBox roles whose work combines BI with Fabric, Azure data or AI
(group "BI + AI/Fabric"). "Core BI" roles are the baseline without that premium,
and "AI ceiling" (AI Engineer) shows the pay of moving fully into AI work.

For the target experience, each role's low/high is interpolated between the 3-6
band (centre 4.5 yrs) and the 6-9 band (centre 7.5 yrs). A role counts towards a
city's minimum and maximum only when its 3-6 band has at least MIN_SAMPLE salaries
and a 6-9 band exists to interpolate towards.

Writes to <out_dir>:
  biai_market.csv          city x role x band: low, mid, high, salaries
  biai_target_roles.csv    city x role at the target experience
  biai_target_summary.csv  one row per city: BI+AI min / typical / max and drill-down fields
  biai_target_postings.csv Fabric/AI postings whose experience range includes the target
"""
import csv
import sys
from datetime import date
from pathlib import Path

MIN_SAMPLE = 10
MAX_AGE_DAYS = 183  # role figures last updated longer ago than this are shown but not counted
MIN_SAMPLE_6_9 = 5  # the 6-9 band we interpolate towards must be self-reported with at least this many salaries
CENTRE = {"3-6": 4.5, "6-9": 7.5}
# Prime locations shown. Rows for any other city in the input files are ignored.
CITIES = ["Gurugram", "New Delhi", "Noida", "Bengaluru", "Hyderabad", "Pune", "Mumbai"]
NCR = ["Gurugram", "New Delhi", "Noida"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def wmean(pairs):
    pairs = [(v, n) for v, n in pairs if v is not None]
    total = sum(n for _, n in pairs)
    if not pairs:
        return None
    if total == 0:
        return sum(v for v, _ in pairs) / len(pairs)
    return sum(v * n for v, n in pairs) / total


def main(data_dir, out_dir, target):
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    roles =[r for r in read(data_dir / "biai_roles.csv") if r["city"] in CITIES]
    postings = read(data_dir / "biai_postings.csv")

    market = []
    cells = {}
    for r in roles:
        lo, hi = num(r["salary_min_lpa"]), num(r["salary_max_lpa"])
        n = int(num(r["sample_size"]) or 0)
        row = {"role": r["role"], "group": r["group"], "city": r["city"], "exp_band": r["exp_band"],
               "low_lpa": lo, "high_lpa": hi, "mid_lpa": round((lo + hi) / 2, 2), "salaries": n,
               "data_type": r["data_type"], "as_of": r["as_of"]}
        market.append(row)
        cells[(r["role"], r["city"], r["exp_band"])] = row
    write(out_dir / "biai_market.csv", market)

    f = (target - CENTRE["3-6"]) / (CENTRE["6-9"] - CENTRE["3-6"])
    newest = max(date.fromisoformat(r["as_of"]) for r in roles)
    stale = lambda row: (newest - date.fromisoformat(row["as_of"])).days > MAX_AGE_DAYS
    target_rows = []
    for (role, city, band), a in cells.items():
        if band != "3-6":
            continue
        b = cells.get((role, city, "6-9"))
        if b:
            lo = a["low_lpa"] + (b["low_lpa"] - a["low_lpa"]) * f
            hi = a["high_lpa"] + (b["high_lpa"] - a["high_lpa"]) * f
            method = "interpolated 3-6 to 6-9" + (" (6-9 is an AmbitionBox estimate)" if b["data_type"] == "estimate" else "")
        else:
            lo, hi, method = a["low_lpa"], a["high_lpa"], "3-6 band only (no 6-9 data)"
        weak_69 = not b or b["data_type"] != "self_reported" or b["salaries"] < MIN_SAMPLE_6_9
        if stale(a):
            method += f"; not counted: last updated {a['as_of']}, over 6 months old"
        elif b and weak_69:
            method += f"; not counted: 6-9 band has fewer than {MIN_SAMPLE_6_9} reported salaries"
        target_rows.append({
            "city": city, "role": role, "group": a["group"],
            "low_lpa": round(lo, 2), "mid_lpa": round((lo + hi) / 2, 2), "high_lpa": round(hi, 2),
            "salaries_3_6": a["salaries"], "salaries_6_9": b["salaries"] if b else 0,
            # A 3-6-only figure understates pay at 5+ years, so it is shown but not counted.
            "counts_for_range": "yes" if a["group"] == "BI + AI/Fabric" and a["salaries"] >= MIN_SAMPLE and not weak_69 and not stale(a) else "",
            "method": method,
        })
    target_rows.sort(key=lambda r: (CITIES.index(r["city"]), r["group"], -r["mid_lpa"]))
    write(out_dir / "biai_target_roles.csv", target_rows)

    hits = []
    for p in postings:
        emin, emax = num(p["exp_min"]), num(p["exp_max"])
        if emin is None or not (emin <= target <= emax):
            continue
        for city in p["locations"].split("|"):
            city = city.strip()
            if city not in CITIES and city != "Delhi NCR":
                continue
            hits.append({"city": city, "title": p["title"], "company": p["company"],
                         "experience": f"{p['exp_min']}-{p['exp_max']} yrs",
                         "salary_min_lpa": num(p["salary_min_lpa"]), "salary_max_lpa": num(p["salary_max_lpa"]),
                         "ai_skills": p["ai_skills"], "all_locations": p["locations"].replace("|", ", "),
                         "as_of": p["as_of"]})
    write(out_dir / "biai_target_postings.csv", hits)

    # Advertised pay for plain Power BI developer postings (from raw_records.csv, if present),
    # kept separate from reported pay: it is extra evidence, not the core baseline.
    core_posts = []
    raw_path = data_dir / "raw_records.csv"
    if raw_path.exists():
        for p in read(raw_path):
            emin, emax = num(p["exp_min"]), num(p["exp_max"])
            if p["data_type"] != "job_posting" or p["role"] != "Power BI Developer" or emin is None or not (emin <= target <= emax):
                continue
            mid = (num(p["salary_min_lpa"]) + num(p["salary_max_lpa"])) / 2
            for city in p["locations"].split("|"):
                core_posts.append({"city": city.strip(), "key": (p["company"], p["exp_min"], p["salary_min_lpa"]), "mid": mid,
                                   "lo": num(p["salary_min_lpa"]), "hi": num(p["salary_max_lpa"])})

    def core_ads(label, city_list):
        wanted = set(city_list) | ({"Delhi NCR"} if label in ("Delhi NCR", "All prime cities") or "Gurugram" in city_list else set())
        seen = {}
        for c in core_posts:
            if c["city"] in wanted:
                seen[c["key"]] = c
        if not seen:
            return {"core_ad_median_lpa": None, "core_ad_min_lpa": None, "core_ad_max_lpa": None, "core_ad_postings": 0}
        mids = sorted(c["mid"] for c in seen.values())
        n = len(mids)
        median = mids[n // 2] if n % 2 else (mids[n // 2 - 1] + mids[n // 2]) / 2
        return {"core_ad_median_lpa": round(median, 2), "core_ad_min_lpa": min(c["lo"] for c in seen.values()),
                "core_ad_max_lpa": max(c["hi"] for c in seen.values()), "core_ad_postings": n}

    def summarise(label, city_list):
        rows = [r for r in target_rows if r["city"] in city_list]
        inrange = [r for r in rows if r["counts_for_range"]]
        core = [r for r in rows if r["group"] == "Core BI" and r["salaries_3_6"] >= MIN_SAMPLE]
        ai = [r for r in rows if r["group"] == "AI ceiling"]
        posts = [h for h in hits if h["city"] in city_list or (label == "Delhi NCR" and h["city"] == "Delhi NCR")]
        if not inrange:
            return None
        lo_row = min(inrange, key=lambda r: r["low_lpa"])
        hi_row = max(inrange, key=lambda r: r["high_lpa"])
        typical = wmean([(r["mid_lpa"], r["salaries_3_6"]) for r in inrange])
        core_mid = wmean([(r["mid_lpa"], r["salaries_3_6"]) for r in core])
        return {
            "city": label,
            "biai_min_lpa": lo_row["low_lpa"],
            "biai_typical_lpa": round(typical, 2),
            "biai_max_lpa": hi_row["high_lpa"],
            "min_from_role": f"{lo_row['role']} ({lo_row['city']})" if len(city_list) > 1 else lo_row["role"],
            "max_from_role": f"{hi_row['role']} ({hi_row['city']})" if len(city_list) > 1 else hi_row["role"],
            "core_bi_typical_lpa": round(core_mid, 2) if core_mid else None,
            "ai_premium_pct": round((typical / core_mid - 1) * 100, 1) if core_mid else None,
            "roles_counted": len(inrange),
            "salaries_counted": sum(r["salaries_3_6"] for r in inrange),
            "posting_min_lpa": min((h["salary_min_lpa"] for h in posts), default=None),
            "posting_max_lpa": max((h["salary_max_lpa"] for h in posts), default=None),
            "postings": len({(h["title"], h["company"]) for h in posts}),
            "ai_engineer_low_lpa": min((r["low_lpa"] for r in ai), default=None),
            "ai_engineer_high_lpa": max((r["high_lpa"] for r in ai), default=None),
            **core_ads(label, city_list),
            "target_years": round(target, 3),
        }

    summary = [s for s in [summarise(c, [c]) for c in CITIES] + [summarise("Delhi NCR", NCR), summarise("All prime cities", CITIES)] if s]
    write(out_dir / "biai_target_summary.csv", summary)
    print(f"{len(market)} market cells, {len(target_rows)} role estimates, {len(hits)} posting-city matches, {len(summary)} city summaries")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 5 + 7 / 12)
