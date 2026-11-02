# AI-enabled BI Developer Pay

Market benchmark for an AI-enabled Power BI developer (AI for BI: Copilot in Power BI, Microsoft Fabric, AI-assisted modelling and insights) with **5 years 7 months** of experience in India's prime cities, November 2026.

**Live dashboard:** https://ayush810.github.io/AI-Enabled-BI-Developer/

## What's in this repo

| Path | What it is |
|---|---|
| `index.html` | The dashboard (static page, no build step) |
| `assets/dash.js` | Small runtime that loads the CSV files and draws the charts (uses d3 v7 from jsDelivr) |
| `data/biai_target_summary.csv` | Per city: AI-enabled BI minimum / typical / maximum pay at 5y 7m, core Power BI baseline, AI premium, job-posting ranges |
| `data/biai_target_roles.csv` | Each role's pay at 5y 7m per city, and whether it counts toward the range (the drill-down) |
| `data/biai_target_postings.csv` | Naukri Fabric / Copilot / AI postings whose experience range includes 5y 7m |
| `data/biai_market.csv` | AmbitionBox pay by role, city and experience band |
| `data/biai_postings.csv` | All Fabric / Copilot / AI Naukri postings with pay shown |
| `data/source/biai_roles.csv` | Raw AmbitionBox figures as collected (role, city, band, low, high, salary count, date) |
| `data/source/biai_postings.csv` | Raw Naukri postings as collected |
| `data/source/raw_records.csv` | Raw core Power BI figures from AmbitionBox, Naukri, Glassdoor, Indeed and Hyring |
| `scripts/build_biai.py` | Rebuilds the `data/biai_*.csv` files from `data/source/` |

Rebuild the data:

```bash
python scripts/build_biai.py data/source data
```

The experience level defaults to 5 years 7 months. Pass a number of years as a third argument for another level, e.g. `7.5`.

## Sources

- AmbitionBox employee-reported salaries (updated Oct–Nov 2026):
  [Power BI Developer](https://www.ambitionbox.com/profile/power-bi-developer-salary),
  [Senior Power BI Developer](https://www.ambitionbox.com/profile/senior-power-bi-developer-salary),
  [BI Developer](https://www.ambitionbox.com/profile/bi-developer-salary),
  [Senior BI Developer](https://www.ambitionbox.com/profile/senior-bi-developer-salary),
  [BI Engineer](https://www.ambitionbox.com/profile/bi-engineer-salary),
  [Power BI Consultant](https://www.ambitionbox.com/profile/power-bi-consultant-salary),
  [Analytics Engineer](https://www.ambitionbox.com/profile/analytics-engineer-salary),
  [Power Platform Developer](https://www.ambitionbox.com/profile/power-platform-developer-salary),
  each read per city (for example `/gurgaon-location`, `/bengaluru-location`).
- Naukri job postings with pay shown, read 2 Nov 2026:
  [Microsoft Fabric + Power BI](https://www.naukri.com/microsoft-fabric-power-bi-jobs),
  [Power BI Copilot](https://www.naukri.com/power-bi-copilot-jobs),
  [Power BI generative AI](https://www.naukri.com/power-bi-generative-ai-jobs),
  [Power BI Developer](https://www.naukri.com/power-bi-developer-jobs).

## Method in brief

- No portal has an "AI-enabled BI developer" title, so the profile is built from BI roles that take in Fabric, Copilot or AI-assisted analytics. AI Engineer and Azure Data Engineer are left out as different jobs.
- Pay at 5 years 7 months is read a third of the way from each role's 3–6 year band to its 6–9 year band.
- A role figure counts toward the minimum and maximum only with at least 10 salaries in the 3–6 year band, at least 5 reported salaries in the 6–9 year band, and data updated in the last six months.
- All figures are annual fixed CTC in ₹ lakh. Prime cities: Gurugram, New Delhi, Noida, Bengaluru, Hyderabad, Pune, Mumbai.
