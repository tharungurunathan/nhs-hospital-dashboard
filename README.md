# NHS Hospital Burden vs Per-patient Intensity (1998/99 – 2023/24)

An interactive treemap dashboard built from 26 years of NHS England Hospital Episode Statistics (HES) admitted-patient-care data. Rectangle area encodes total **Burden** (Admissions × Mean Length of Stay) and colour encodes **Per-patient Intensity** (Waiting-list FAE × Mean LOS). The dashboard is filterable by financial year and groups diagnoses by their ICD-10 super-chapter and chapter.

Built for COMP4037 Research Methods, University of Nottingham.

## Quick look

Just open `index.html` in any modern browser. It's a single self-contained file with the chart JSON and Plotly bundled in, so no build step or web server is required.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The built dashboard. Treemap, sunburst, heatmap, quadrant scatter and stacked-area stream, all interactive. |
| `dashboard_template.html` | Light-theme HTML shell that `build_website.py` fills in with chart JSON. |
| `build_website.py` | Reads the processed CSV and writes `index.html` plus the four supplementary PNGs. |
| `export_treemap_png.py` | Renders the static 2020/21 treemap (`supp_treemap.png`) used as Figure 1 in the report. |
| `nhs_multi_year_analysis.py` | Data pipeline. Reads the 26 raw NHS Excel workbooks and writes `nhs_all_years_processed.csv`. |
| `nhs_all_years_processed.csv` | The cleaned long-format dataset (~285 rows per year × 26 years). |
| `supp_treemap.png` · `supp_sunburst.png` · `supp_heatmap.png` · `supp_quadrant.png` · `supp_stream.png` | Static chart exports referenced by the report. |

## Reproduce from raw data

The raw HES distribution is not committed (it's ~83 MB zipped, ~110 MB unzipped). Download it from NHS Digital's Hospital Episode Statistics page and place the zip alongside the scripts:

> https://digital.nhs.uk/data-and-information/publications/statistical/hospital-admitted-patient-care-activity

Then:

```bash
pip install -r requirements.txt
python nhs_multi_year_analysis.py     # extracts the zip and writes nhs_all_years_processed.csv
python build_website.py                # writes index.html + supp_*.png (heatmap, quadrant, stream, sunburst)
python export_treemap_png.py           # writes supp_treemap.png
```

If you only want to rebuild the dashboard and you already have `nhs_all_years_processed.csv`, you can skip `nhs_multi_year_analysis.py` entirely.

## What's in the dashboard

- **Treemap** — top 40 diagnoses by burden in any chosen year (1998/99 – 2023/24), nested by Super-chapter → Chapter → Diagnosis. Year filter dropdown is in the top-left.
- **Sunburst** — same hierarchy as a radial view of the latest year.
- **Heatmap** — Chapter × Year, coloured by share of total burden, useful for spotting long-run drift.
- **Quadrant scatter** — Burden vs Per-patient Intensity on log-log axes, with reference lines splitting the field into four strategic quadrants.
- **Stacked-area stream** — Super-chapter burden over the full 26-year window.

## Tech

Python 3.10+, pandas, NumPy, Plotly, Matplotlib, squarify, openpyxl. See `requirements.txt`.

## Credits

Data: NHS Digital, Hospital Episode Statistics (HES) — Admitted Patient Care, financial years 1998/99 to 2023/24. Analysis and visualisation: Tharun, School of Computer Science, University of Nottingham.
