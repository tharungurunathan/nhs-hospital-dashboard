# NHS Hospital Burden vs Per-patient Intensity (1998/99 – 2023/24)

This is the project I built for COMP4037 Research Methods at the University of Nottingham. It's an interactive treemap of 26 years of NHS England hospital admissions, grouped by ICD-10 diagnosis. Rectangle area shows total **burden** (admissions × mean length of stay) and colour shows **per-patient intensity** (waiting-list FAE × mean LOS), so the big patches are the diagnoses that swallow the most bed-days overall and the colour tells you whether each patient costs a lot of resource or not.

Live site: **https://tharungurunathan.github.io/nhs-hospital-dashboard/**

## Just look at it

Open `index.html` in a browser, or use the live link above. Everything is bundled into a single file — no server, no build, no install needed. The treemap has a year dropdown in the top-left so you can step through 1998/99 to 2023/24.

## Files in this repo

`index.html` is the dashboard you actually open.
`build_website.py` is what generated it.
`dashboard_template.html` is the HTML shell that the build script fills in.
`export_treemap_png.py` makes the static treemap PNG used as Figure 1 in my report.
`nhs_multi_year_analysis.py` is the data pipeline — it reads the raw NHS Excel workbooks and writes the cleaned CSV.
`nhs_all_years_processed.csv` is that cleaned CSV. About 285 rows per year × 26 years, in long format.
`supp_treemap.png`, `supp_sunburst.png`, `supp_heatmap.png`, `supp_quadrant.png`, `supp_stream.png` are the static chart images for the report.

## Data

The dataset I'm using is `nhs_all_years_processed.csv` — it's already in the repo. I assembled it from 26 financial years of NHS Hospital Episode Statistics (admitted patient care) workbooks, harmonised the column names, dropped the aggregate rows, and added the derived metrics (mean LOS, burden, intensity). All the dashboard scripts read from that CSV directly, so you don't need to re-download anything.

## Running it from scratch

```bash
pip install -r requirements.txt
python build_website.py        # rebuilds index.html and the supplementary PNGs
python export_treemap_png.py   # rebuilds the Figure 1 treemap PNG
```

If you ever want to rebuild the CSV from raw Excel workbooks, run `python nhs_multi_year_analysis.py` first — but you only need that if the underlying data changes.

## What's on the dashboard

The treemap is the main view, with a year filter. Below it sit a sunburst (same hierarchy as a radial), a chapter × year heatmap that makes the slow drift toward mental health and musculoskeletal admissions visible, a quadrant scatter (burden vs intensity on log-log axes) that splits diagnoses into four strategic quadrants, and a stacked-area stream of super-chapter burden across the full 26 years.

## Stack

Python 3.10, pandas, NumPy, Plotly, Matplotlib, squarify, openpyxl. Versions are pinned in `requirements.txt`.

— Tharun
