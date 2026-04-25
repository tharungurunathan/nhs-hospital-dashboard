import os
import re
import zipfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ZIP_PATH       = "NHS Hospital Admissions.zip"
EXTRACT_PATH   = "nhs_data"
DATA_ROOT      = Path(EXTRACT_PATH) / "NHS Hospital Admissions"
TOP_N_PER_YEAR = 25

if not DATA_ROOT.exists() and Path(ZIP_PATH).exists():
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(EXTRACT_PATH)

ICD_CHAPTERS = {
    "A": "Infectious Diseases", "B": "Infectious Diseases",
    "C": "Neoplasms",           "D": "Blood Disorders",
    "E": "Endocrine & Metabolic","F": "Mental Disorders",
    "G": "Nervous System",      "H": "Eye & Ear",
    "I": "Circulatory System",  "J": "Respiratory System",
    "K": "Digestive System",    "L": "Skin Conditions",
    "M": "Musculoskeletal",     "N": "Genitourinary",
    "O": "Pregnancy & Childbirth","P": "Perinatal",
    "Q": "Congenital",          "R": "Symptoms & Signs",
    "S": "Injuries",            "T": "Injuries",
    "V": "External Causes",     "W": "External Causes",
    "X": "External Causes",     "Y": "External Causes",
    "Z": "Health Service Contact",
}

SUPER_CHAPTERS = {
    "Infectious Diseases":      "Infections",
    "Neoplasms":                "Cancer & Blood",
    "Blood Disorders":          "Cancer & Blood",
    "Endocrine & Metabolic":    "Systemic",
    "Mental Disorders":         "Systemic",
    "Nervous System":           "Neurological",
    "Eye & Ear":                "Neurological",
    "Circulatory System":       "Cardio & Respiratory",
    "Respiratory System":       "Cardio & Respiratory",
    "Digestive System":         "Digestive & Renal",
    "Genitourinary":            "Digestive & Renal",
    "Skin Conditions":          "Musculoskeletal",
    "Musculoskeletal":          "Musculoskeletal",
    "Pregnancy & Childbirth":   "Reproductive",
    "Perinatal":                "Reproductive",
    "Congenital":               "Reproductive",
    "Symptoms & Signs":         "Symptoms & Injuries",
    "Injuries":                 "Symptoms & Injuries",
    "External Causes":          "Symptoms & Injuries",
    "Health Service Contact":   "Other",
}

def find_header_row(df_raw: pd.DataFrame) -> int | None:
    for r in range(min(25, len(df_raw))):
        row_str = " ".join(str(x) for x in df_raw.iloc[r].dropna()).lower()
        if "finished" in row_str and ("consultant" in row_str or "admission" in row_str):
            return r
    return None

def pick_summary_sheet(xl: pd.ExcelFile) -> str:
    sheets = xl.sheet_names
    for keys in [("primary", "summary"), ("summary",), ("primary", "diagnosis"), ("diagnosis",)]:
        for s in sheets:
            sl = s.lower()
            if all(k in sl for k in keys):
                if "3" in sl or "4" in sl or "introduction" in sl or "all" in sl:
                    continue
                return s
    return sheets[0]

def standardize_columns(headers: list) -> dict:
    name_map: dict = {}
    used = set()

    def assign(i, name):
        if name not in used:
            name_map[i] = name
            used.add(name)

    for i, h in enumerate(headers):
        h_str = re.sub(r"\s+", " ", str(h).strip().lower().replace("\n", " "))
        if "finished consultant" in h_str:
            assign(i, "FCE")
        elif ("admission" in h_str and "episode" in h_str) or h_str == "admissions":
            assign(i, "Admissions")
        elif h_str.startswith("male"):
            assign(i, "Male")
        elif h_str.startswith("female"):
            assign(i, "Female")
        elif h_str.startswith("emergency"):
            assign(i, "Emergency")
        elif "waiting list" in h_str or h_str.startswith("waiting"):
            assign(i, "Waiting")
        elif h_str.startswith("mean length"):
            assign(i, "MeanLOS")
        elif h_str.startswith("mean time") or h_str.startswith("mean wait"):
            assign(i, "MeanWait")
        elif h_str.startswith("mean age"):
            assign(i, "MeanAge")
        elif "fce bed days" in h_str:
            assign(i, "BedDays")
        elif "primary diagnosis" in h_str and i == 0:
            assign(i, "CodeDesc")
    return name_map

def _open_excel(fp: Path):
    suffix = fp.suffix.lower()
    candidates = []
    if suffix == ".xlsx":
        candidates = ["openpyxl", "calamine"]
    elif suffix == ".xls":

        candidates = ["calamine", "xlrd"]
    else:
        candidates = ["openpyxl", "calamine", "xlrd"]

    last_err = None
    for eng in candidates:
        try:
            return pd.ExcelFile(fp, engine=eng)
        except ImportError as e:
            last_err = e
        except Exception as e:
            last_err = e
    raise RuntimeError(
        f"Could not open {fp.name}. Tried engines {candidates}. "
        f"Last error: {last_err}.  "
        f"Install the missing engine with:  pip install python-calamine"
    )

def load_year_file(fp: Path) -> pd.DataFrame | None:
    try:
        xl = _open_excel(fp)
    except Exception as e:
        print(f"      ↳ {e}")
        return None
    sheet = pick_summary_sheet(xl)

    df_raw = pd.read_excel(fp, sheet_name=sheet, header=None, engine=xl.engine)
    hr = find_header_row(df_raw)
    if hr is None:
        return None

    headers = df_raw.iloc[hr].tolist()
    name_map = standardize_columns(headers)
    data = df_raw.iloc[hr + 1:].reset_index(drop=True)
    data.columns = [name_map.get(i, f"col_{i}") for i in range(len(data.columns))]

    if "CodeDesc" in data.columns:
        idx = list(data.columns).index("CodeDesc")
        if idx + 1 < len(data.columns):
            sample = data.iloc[2:10, idx + 1].dropna().astype(str).tolist()
            has_desc = any(len(s) > 5 and not s.replace(".", "").replace(",", "").isdigit()
                           for s in sample)
        else:
            has_desc = False

        if has_desc:
            data = data.rename(columns={data.columns[idx]: "Code",
                                        data.columns[idx + 1]: "Diagnosis"})
        else:
            data["Code"] = data["CodeDesc"].astype(str).str.extract(r"^([A-Z]\d{2}[\-\.]?[A-Z\d]*)")
            data["Diagnosis"] = (data["CodeDesc"].astype(str)
                                 .str.replace(r"^[A-Z]\d{2}[\-\.]?[A-Z\d]*\s*", "", regex=True))
    elif "col_0" in data.columns:
        data["Code"] = data["col_0"].astype(str).str.extract(r"^([A-Z]\d{2}[\-\.]?[A-Z\d]*)")
        data["Diagnosis"] = (data["col_0"].astype(str)
                             .str.replace(r"^[A-Z]\d{2}[\-\.]?[A-Z\d]*\s*", "", regex=True))

    for c in ("FCE", "Admissions", "Male", "Female", "Emergency",
              "Waiting", "MeanLOS", "MeanWait", "MeanAge", "BedDays"):
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors="coerce")

    keep = [c for c in ("Code", "Diagnosis", "FCE", "Admissions",
                        "Male", "Female", "Emergency", "Waiting",
                        "MeanLOS", "MeanWait", "MeanAge", "BedDays")
            if c in data.columns]
    data = data[keep]
    data = data.dropna(subset=["Code"])
    data = data[~data["Code"].astype(str).str.contains("Total", case=False, na=False)]
    data = data.reset_index(drop=True)
    return data

def discover_year_files(root: Path) -> dict[int, Path]:
    files = {}

    for year_dir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.isdigit()):
        yr = int(year_dir.name)
        for f in sorted(year_dir.iterdir()):
            n = f.name.lower()
            if not (n.endswith(".xls") or n.endswith(".xlsx")):
                continue
            if any(t in n for t in ("3cha", "4cha", "3char", "4char")):
                continue
            if "sum" in n or ("prim-diag" in n and "tab" in n):
                files[yr] = f
                break

    for f in sorted(root.iterdir()):
        if not f.is_file():
            continue
        n = f.name.lower()
        if not (n.endswith(".xls") or n.endswith(".xlsx")):
            continue
        if any(t in n for t in ("3cha", "4cha", "3char", "4char", "all")):
            continue
        m = re.search(r"(\d{4})-(\d{2})", f.name) or re.search(r"(\d{2})-(\d{2})", f.name)
        if not m:
            continue
        first = m.group(1)
        yr = int(first) if len(first) == 4 else 2000 + int(first)

        if yr not in files or "sum" in n or "tab" in n:
            files[yr] = f
    return files

def enrich(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df = df.copy()
    df["Year"] = year
    df["Diagnosis"] = df["Diagnosis"].fillna("Unknown").astype(str).str.strip()
    df["Diagnosis"] = df["Diagnosis"].str.slice(0, 60)

    df["Chapter_Letter"] = df["Code"].astype(str).str.strip().str[0]
    df["Chapter_Name"]   = df["Chapter_Letter"].map(ICD_CHAPTERS).fillna("Other Conditions")
    df["Super_Chapter"]  = df["Chapter_Name"].map(SUPER_CHAPTERS).fillna("Other")

    df["MeanLOS"] = df.get("MeanLOS", pd.Series(dtype=float)).fillna(0)
    df["Waiting"] = df.get("Waiting", pd.Series(dtype=float)).fillna(0)
    df["Admissions"] = df.get("Admissions", pd.Series(dtype=float)).fillna(0)

    df["Burden"]    = df["Admissions"] * df["MeanLOS"]
    df["Intensity"] = df["Waiting"]    * df["MeanLOS"]

    df = df.replace([np.inf, -np.inf], np.nan)
    df["Burden"]    = df["Burden"].fillna(0)
    df["Intensity"] = df["Intensity"].fillna(0)
    df = df[df["Burden"] > 0]

    return df.reset_index(drop=True)

print("Discovering files…")
year_files = discover_year_files(DATA_ROOT)
print(f"  → found {len(year_files)} years: {sorted(year_files)}")

frames = []
for yr in sorted(year_files):
    print(f"  Loading {yr}/{(yr + 1) % 100:02d} …")
    df_y = load_year_file(year_files[yr])
    if df_y is None or df_y.empty:
        print(f"    ! skip {yr}: could not parse")
        continue
    frames.append(enrich(df_y, yr))

if not frames:
    raise RuntimeError("No annual data could be loaded.")

all_data = pd.concat(frames, ignore_index=True)
print(f"\nLoaded {len(all_data):,} rows across {all_data['Year'].nunique()} years.")

all_data.to_csv("nhs_all_years_processed.csv", index=False)
print("Wrote nhs_all_years_processed.csv")
