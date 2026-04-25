import os, json, math
from pathlib import Path
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LogNorm
from matplotlib import cm

DATA = "nhs_all_years_processed.csv"
df   = pd.read_csv(DATA)

LATEST_YEAR = int(df["Year"].max())
df_latest   = df[df["Year"] == LATEST_YEAR].copy()

INT_LO = float(df["Intensity"].quantile(0.10))
INT_HI = float(df["Intensity"].quantile(0.90))

CHAPTER_COLORS = {
    "Infectious Diseases":   "#1b9e77",
    "Neoplasms":             "#d95f02",
    "Blood Disorders":       "#7570b3",
    "Endocrine & Metabolic": "#e7298a",
    "Mental Disorders":      "#66a61e",
    "Nervous System":        "#e6ab02",
    "Eye & Ear":             "#a6761d",
    "Circulatory System":    "#666666",
    "Respiratory System":    "#1f78b4",
    "Digestive System":      "#33a02c",
    "Skin Conditions":       "#fb9a99",
    "Musculoskeletal":       "#fdbf6f",
    "Genitourinary":         "#cab2d6",
    "Pregnancy & Childbirth":"#ffff99",
    "Perinatal":             "#b15928",
    "Congenital":            "#8dd3c7",
    "Symptoms & Signs":      "#bebada",
    "Injuries":              "#fb8072",
    "External Causes":       "#80b1d3",
    "Health Service Contact":"#fdb462",
    "Other Conditions":      "#bbbbbb",
}
SUPER_COLORS = {
    "Cardio & Respiratory" : "#1f78b4",
    "Digestive & Renal"    : "#33a02c",
    "Musculoskeletal"      : "#fdbf6f",
    "Neurological"         : "#e6ab02",
    "Systemic"             : "#e7298a",
    "Cancer & Blood"       : "#d95f02",
    "Infections"           : "#1b9e77",
    "Reproductive"         : "#ff7f00",
    "Symptoms & Injuries"  : "#cab2d6",
    "Other"                : "#999999",
}

PLOTLY_LIGHT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="#222222", family="Source Sans Pro, Helvetica, Arial"),
    title_font_color="#111111",
    legend_font_color="#333333",
    xaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#d1d5db",
               linecolor="#9ca3af", color="#374151"),
    yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#d1d5db",
               linecolor="#9ca3af", color="#374151"),
)

def _apply_dark(fig):
    fig.update_layout(**PLOTLY_LIGHT)
    return fig

def fig_treemap():
    years = sorted(df["Year"].unique())
    fig = go.Figure()

    TREEMAP_SCALE = [
        [0.00, "#f08c4f"],
        [0.25, "#fbb893"],
        [0.50, "#fef3c7"],
        [0.75, "#a8c8f0"],
        [1.00, "#4a90e2"],
    ]

    for yr in years:
        sub = df[df["Year"] == yr].nlargest(40, "Burden").copy()
        sub["Burden_pct"] = sub["Burden"] / sub["Burden"].sum() * 100
        sub["Short"]      = sub["Diagnosis"].str.slice(0, 32)
        tm = px.treemap(
            sub, path=["Super_Chapter", "Chapter_Name", "Short"],
            values="Burden", color="Intensity",
            color_continuous_scale=TREEMAP_SCALE,
            range_color=(INT_LO, INT_HI),
            custom_data=["Burden_pct", "Admissions", "MeanLOS"],
        )
        tr = tm.data[0]
        tr.texttemplate = "<b>%{label}</b><br>%{customdata[0]:.1f}%"
        tr.textfont     = dict(size=12, color="#1f2937")
        tr.marker.line  = dict(width=1, color="white")
        tr.hovertemplate = ("<b>%{label}</b><br>"
                            "Burden share: %{customdata[0]:.2f}%<br>"
                            "Admissions: %{customdata[1]:,.0f}<br>"
                            "Mean LOS: %{customdata[2]:.1f} days<extra></extra>")
        tr.visible = (yr == LATEST_YEAR)
        fig.add_trace(tr)

    year_btns = []
    for i, yr in enumerate(years):
        vis = [False] * len(years)
        vis[i] = True
        year_btns.append(dict(
            label=f"{yr}/{(yr+1)%100:02d}", method="update",
            args=[{"visible": vis},
                  {"title.text": f"NHS Hospital Burden vs Per-patient Intensity - {yr}/{(yr+1)%100:02d}"}]
        ))

    fig.update_layout(
        title=dict(
            text=f"NHS Hospital Burden vs Per-patient Intensity - {LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}",
            x=0.5, font=dict(size=16)),
        margin=dict(t=120, l=10, r=10, b=10),
        coloraxis=dict(colorscale=TREEMAP_SCALE, cmin=INT_LO, cmax=INT_HI,
                       colorbar=dict(title="Per-patient<br>intensity")),
        height=640,
        updatemenus=[
            dict(buttons=year_btns, direction="down", showactive=True,
                 x=0.00, xanchor="left", y=1.14, yanchor="top",
                 bgcolor="#ffffff", bordercolor="#cbd5e1", borderwidth=1,
                 font=dict(color="#1f2937", size=11),
                 pad=dict(l=8, r=8, t=4, b=4),
                 active=years.index(LATEST_YEAR)),
        ],
        annotations=[
            dict(text="<b>Filter by Year</b>", x=0.00, xref="paper",
                 y=1.20, yref="paper", xanchor="left",
                 showarrow=False, font=dict(color="#374151", size=12)),
        ],
    )
    return _apply_dark(fig)

def heatmap_data():
    g = df.groupby(["Year", "Chapter_Name"], as_index=False)["Burden"].sum()
    yr_total = df.groupby("Year")["Burden"].sum().rename("YearTotal")
    g = g.merge(yr_total, on="Year")
    g["Share"] = g["Burden"] / g["YearTotal"] * 100
    pivot = g.pivot(index="Chapter_Name", columns="Year", values="Share").fillna(0)
    pivot = pivot.reindex(pivot.sum(axis=1).sort_values(ascending=False).index)
    return pivot

def fig_heatmap():
    pivot = heatmap_data()
    year_labels = [f"{y}/{(y+1)%100:02d}" for y in pivot.columns]
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=year_labels, y=pivot.index,
        colorscale="YlOrRd", zmin=0, zmax=float(pivot.values.max()),
        colorbar=dict(title="% of year<br>total Burden"),
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{z:.2f}% of year burden<extra></extra>"))
    fig.update_layout(
        title=dict(text="Temporal Heatmap - ICD-10 Chapter Share of NHS Hospital Burden (1998/99 - 2023/24)",
                   x=0.5, font=dict(size=15)),
        height=620,
        margin=dict(t=70, l=40, r=20, b=80),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=10)),
        annotations=[dict(
            text="Cell colour shows that chapter's share of total NHS bed-day demand in that financial year.",
            x=0.5, y=-0.18, xref="paper", yref="paper",
            showarrow=False, font=dict(size=11, color="#555555"))])
    return _apply_dark(fig), pivot

def fig_quadrant():
    sub = df_latest.copy()
    sub = sub[(sub["Burden"] > 0) & (sub["Intensity"] > 0)]
    med_b = sub["Burden"].median()
    med_i = sub["Intensity"].median()
    sub["Quadrant"] = np.where(
        (sub["Burden"] >= med_b) & (sub["Intensity"] >= med_i),
        "High volume - High per-patient cost",
        np.where((sub["Burden"] >= med_b) & (sub["Intensity"] < med_i),
        "High volume - Low per-patient cost",
        np.where((sub["Burden"] < med_b) & (sub["Intensity"] >= med_i),
        "Low volume - High per-patient cost",
        "Low volume - Low per-patient cost")))

    quad_colors = {
        "High volume - High per-patient cost": "#b2182b",
        "High volume - Low per-patient cost":  "#1b7837",
        "Low volume - High per-patient cost":  "#d6604d",
        "Low volume - Low per-patient cost":   "#4393c3",
    }

    fig = px.scatter(
        sub, x="Burden", y="Intensity",
        color="Quadrant", color_discrete_map=quad_colors,
        size="Admissions", size_max=28, log_x=True, log_y=True,
        hover_data={"Code":True, "Diagnosis":True, "MeanLOS":":.1f",
                    "Admissions":":,.0f", "Quadrant":False,
                    "Burden":":,.0f", "Intensity":":,.0f"},
        opacity=0.78,
    )
    fig.add_shape(type="line", x0=med_b, y0=sub["Intensity"].min(),
                  x1=med_b, y1=sub["Intensity"].max(),
                  line=dict(color="#64748b", dash="dash", width=1))
    fig.add_shape(type="line", x0=sub["Burden"].min(), y0=med_i,
                  x1=sub["Burden"].max(), y1=med_i,
                  line=dict(color="#64748b", dash="dash", width=1))

    top10 = sub.nlargest(10, "Burden")
    for _, r in top10.iterrows():
        fig.add_annotation(x=r["Burden"], y=r["Intensity"],
                           text=r["Code"], showarrow=False,
                           font=dict(size=9, color="#222222"),
                           yshift=10)
    fig.update_layout(
        title=dict(text=f"Strategic Quadrants - Burden vs Per-patient Intensity, {LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}",
                   x=0.5, font=dict(size=15)),
        height=580,
        margin=dict(t=70, l=60, r=20, b=90),
        xaxis=dict(title="Burden  (Admissions x Mean LOS, log scale)"),
        yaxis=dict(title="Intensity  (Waiting x Mean LOS, log scale)"),
        legend=dict(title_text="Quadrant", orientation="h", y=-0.24,
                    x=0.5, xanchor="center", font=dict(size=10)))
    return _apply_dark(fig)

def fig_stream():
    g = (df.groupby(["Year", "Super_Chapter"], as_index=False)["Burden"].sum())
    order = (g.groupby("Super_Chapter")["Burden"].sum()
               .sort_values(ascending=False).index.tolist())
    fig = go.Figure()
    for sc in order:
        sub = g[g["Super_Chapter"] == sc].sort_values("Year")
        fig.add_trace(go.Scatter(
            x=sub["Year"], y=sub["Burden"],
            stackgroup="one", mode="lines", name=sc,
            line=dict(width=0.3, color=SUPER_COLORS.get(sc, "#999")),
            fillcolor=SUPER_COLORS.get(sc, "#999"),
            hovertemplate=f"<b>{sc}</b><br>Year %{{x}}<br>Burden %{{y:,.0f}}<extra></extra>"))
    fig.update_layout(
        title=dict(text="Stacked Burden Stream - NHS Hospital Burden by Super-chapter, 1998/99 - 2023/24",
                   x=0.5, font=dict(size=15)),
        height=560,
        margin=dict(t=70, l=60, r=20, b=60),
        xaxis=dict(title="Financial year", tickmode="linear",
                   dtick=2, tickangle=-45),
        yaxis=dict(title="Total Burden (Admissions x Mean LOS)"),
        legend=dict(font=dict(size=10)))
    return _apply_dark(fig)

def fig_sunburst():
    sub = df_latest.nlargest(45, "Burden").copy()
    sub["Short"] = sub["Diagnosis"].str.slice(0, 34)
    SUNBURST_SCALE = [
        [0.00, "#f08c4f"], [0.25, "#fbb893"], [0.50, "#fef3c7"],
        [0.75, "#a8c8f0"], [1.00, "#4a90e2"],
    ]
    fig = px.sunburst(
        sub, path=["Super_Chapter", "Chapter_Name", "Short"],
        values="Burden", color="Intensity",
        color_continuous_scale=SUNBURST_SCALE,
        range_color=(INT_LO, INT_HI),
    )
    fig.update_traces(insidetextfont=dict(color="#1f2937"))
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Burden %{value:,.0f}<extra></extra>",
        insidetextorientation="radial",
    )
    fig.update_layout(
        title=dict(text=f"Sunburst Hierarchy - NHS Burden by ICD-10 Grouping, {LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}",
                   x=0.5, font=dict(size=15)),
        height=620,
        margin=dict(t=70, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title="Per-patient<br>Intensity"))
    return _apply_dark(fig)

print("building Plotly figures ...")
fig_t  = fig_treemap()
fig_h, heat_pivot = fig_heatmap()
fig_q  = fig_quadrant()
fig_a  = fig_stream()
fig_b  = fig_sunburst()

print("rendering supplementary PNGs ...")

pivot = heat_pivot
fig, ax = plt.subplots(figsize=(12, 6.2), dpi=170)
im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd",
               vmin=0, vmax=float(pivot.values.max()))
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([f"{y}/{(y+1)%100:02d}" for y in pivot.columns],
                   rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
cb = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.015)
cb.set_label("% of year total Burden", fontsize=9)
ax.set_title("Temporal Heatmap - ICD-10 Chapter Share of NHS Hospital Burden (1998/99 - 2023/24)",
             fontsize=12, weight="bold", pad=12)
covid_col = list(pivot.columns).index(2020) if 2020 in pivot.columns else None
if covid_col is not None:
    ax.axvline(covid_col - 0.5, color="blue", lw=0.8, alpha=0.4)
    ax.axvline(covid_col + 0.5, color="blue", lw=0.8, alpha=0.4)
    ax.annotate("COVID-19 year ->\nwatch the step-change",
                xy=(covid_col, -0.9), xytext=(covid_col - 3, -2.2),
                fontsize=8.5, color="blue",
                arrowprops=dict(arrowstyle="->", color="blue", lw=0.8),
                annotation_clip=False)
plt.tight_layout()
plt.savefig("supp_heatmap.png", bbox_inches="tight", facecolor="white")
plt.close()

sub = df_latest.copy()
sub = sub[(sub["Burden"] > 0) & (sub["Intensity"] > 0)]
med_b = sub["Burden"].median()
med_i = sub["Intensity"].median()

def quad(b, i):
    if b >= med_b and i >= med_i: return "HH"
    if b >= med_b and i <  med_i: return "HL"
    if b <  med_b and i >= med_i: return "LH"
    return "LL"
sub["Q"] = [quad(b, i) for b, i in zip(sub["Burden"], sub["Intensity"])]
quad_col = {"HH":"#d73027","HL":"#1a9850","LH":"#fc8d59","LL":"#91bfdb"}

fig, ax = plt.subplots(figsize=(10, 6.3), dpi=170)
for q, label in [("HH","High vol - High cost"),
                 ("HL","High vol - Low cost"),
                 ("LH","Low vol - High cost"),
                 ("LL","Low vol - Low cost")]:
    s = sub[sub["Q"] == q]
    ax.scatter(s["Burden"], s["Intensity"],
               s=np.clip(np.log10(s["Admissions"].replace(0,1)) ** 2 * 8, 8, 220),
               color=quad_col[q], alpha=0.6, edgecolor="white", lw=0.4, label=label)
ax.set_xscale("log"); ax.set_yscale("log")
ax.axvline(med_b, color="#888", ls="--", lw=0.8)
ax.axhline(med_i, color="#888", ls="--", lw=0.8)

ymax = sub["Intensity"].max(); xmax = sub["Burden"].max()
ymin = sub["Intensity"].min(); xmin = sub["Burden"].min()
ax.text(xmax * 0.5, ymax * 0.9, "HIGH VOLUME\nHIGH COST",
        color="#d73027", fontsize=10, weight="bold", ha="right")
ax.text(xmax * 0.5, ymin * 1.3, "HIGH VOLUME\nLOW COST",
        color="#1a9850", fontsize=10, weight="bold", ha="right", va="bottom")
ax.text(xmin * 3, ymax * 0.9, "LOW VOLUME\nHIGH COST",
        color="#fc8d59", fontsize=10, weight="bold", ha="left")
ax.text(xmin * 3, ymin * 1.3, "LOW VOLUME\nLOW COST",
        color="#1778b4", fontsize=10, weight="bold", ha="left", va="bottom")

top10 = sub.nlargest(10, "Burden")
for _, r in top10.iterrows():
    ax.annotate(r["Code"], xy=(r["Burden"], r["Intensity"]),
                xytext=(4, 4), textcoords="offset points",
                fontsize=8, color="#222")
ax.set_xlabel("Burden  (Admissions x Mean LOS, log scale)")
ax.set_ylabel("Intensity  (Waiting x Mean LOS, log scale)")
ax.set_title(f"Strategic Quadrants - Burden vs Intensity, {LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}",
             fontsize=12, weight="bold")
ax.legend(fontsize=8, loc="lower right", frameon=True)
ax.grid(True, which="major", alpha=0.25)
plt.tight_layout()
plt.savefig("supp_quadrant.png", bbox_inches="tight", facecolor="white")
plt.close()

g = df.groupby(["Year", "Super_Chapter"], as_index=False)["Burden"].sum()
order = (g.groupby("Super_Chapter")["Burden"].sum()
           .sort_values(ascending=False).index.tolist())
years = sorted(g["Year"].unique())
stacks = np.zeros((len(order), len(years)))
for i, sc in enumerate(order):
    s = g[g["Super_Chapter"] == sc].set_index("Year")["Burden"]
    for j, y in enumerate(years):
        stacks[i, j] = s.get(y, 0)

fig, ax = plt.subplots(figsize=(11, 5.4), dpi=170)
cols = [SUPER_COLORS.get(sc, "#999") for sc in order]
ax.stackplot(years, stacks, labels=order, colors=cols, alpha=0.92,
             edgecolor="white", linewidth=0.4)
ax.set_xlim(min(years), max(years))
ax.set_xlabel("Financial year")
ax.set_ylabel("Total Burden (Admissions x Mean LOS)")
ax.set_title("Stacked Burden Stream - NHS Hospital Burden by Super-chapter, 1998/99 - 2023/24",
             fontsize=12, weight="bold", pad=10)
ax.grid(axis="y", alpha=0.25)
ax.axvline(2020, color="red", lw=0.9, alpha=0.6)
ax.annotate("2020/21 - COVID", xy=(2020, ax.get_ylim()[1] * 0.94),
            xytext=(2014.5, ax.get_ylim()[1] * 0.96),
            fontsize=8.5, color="red",
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8))
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5),
          fontsize=8, frameon=False)
ax.set_facecolor("white")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("supp_stream.png", bbox_inches="tight", facecolor="white")
plt.close()

sub = df_latest.nlargest(40, "Burden").copy()
super_totals = sub.groupby("Super_Chapter")["Burden"].sum().sort_values(ascending=False)
chap_totals  = sub.groupby(["Super_Chapter", "Chapter_Name"])["Burden"].sum()

fig, ax = plt.subplots(figsize=(9, 9), dpi=170)
outer_vals   = super_totals.values
outer_cols   = [SUPER_COLORS.get(s, "#999") for s in super_totals.index]
outer_labels = super_totals.index.tolist()
inner_vals, inner_cols, inner_labels = [], [], []
for sc in super_totals.index:
    rows = chap_totals.loc[sc].sort_values(ascending=False)
    base = SUPER_COLORS.get(sc, "#999")
    for ch in rows.index:
        inner_vals.append(rows[ch])
        inner_cols.append(CHAPTER_COLORS.get(ch, base))
        inner_labels.append(ch)

size = 0.32
w1, _ = ax.pie(outer_vals, radius=1, colors=outer_cols,
               labels=outer_labels, labeldistance=1.08,
               textprops=dict(fontsize=8.5, color="#222"),
               wedgeprops=dict(width=size, edgecolor="white", linewidth=1.2))
w2, _ = ax.pie(inner_vals, radius=1 - size, colors=inner_cols,
               wedgeprops=dict(width=size, edgecolor="white", linewidth=0.8))
ax.set(aspect="equal")
ax.set_title(f"Sunburst Hierarchy - NHS Burden, {LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}\n"
             "Outer = Super-chapter,  Inner = ICD-10 Chapter",
             fontsize=12, weight="bold", pad=10)
plt.tight_layout()
plt.savefig("supp_sunburst.png", bbox_inches="tight", facecolor="white")
plt.close()

print("assembling index.html ...")

def div(fig, div_id):
    return pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       div_id=div_id, config={"displaylogo": False, "responsive": True})

div_treemap  = div(fig_t, "fig-treemap")
div_heatmap  = div(fig_h, "fig-heatmap")
div_quad     = div(fig_q, "fig-quadrant")
div_stream   = div(fig_a, "fig-stream")
div_sunburst = div(fig_b, "fig-sunburst")

stats = dict(
    rows       = len(df),
    years      = f"{int(df['Year'].min())}/{(int(df['Year'].min())+1)%100:02d} - "
                 f"{LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}",
    n_years    = df["Year"].nunique(),
    diagnoses  = df["Code"].nunique(),
    chapters   = df["Chapter_Name"].nunique(),
    super_chap = df["Super_Chapter"].nunique(),
)

LATEST_LABEL = f"{LATEST_YEAR}/{(LATEST_YEAR+1)%100:02d}"

TEMPLATE = Path("dashboard_template.html").read_text(encoding="utf-8")

replacements = {
    "{{YEARS}}":        stats["years"],
    "{{LATEST}}":       LATEST_LABEL,
    "{{N_YEARS}}":      str(stats["n_years"]),
    "{{ROWS}}":         f"{stats['rows']:,}",
    "{{DIAGNOSES}}":    f"{stats['diagnoses']:,}",
    "{{CHAPTERS}}":     str(stats["chapters"]),
    "{{SUPER_CHAP}}":   str(stats["super_chap"]),
    "{{DIV_TREEMAP}}":  div_treemap,
    "{{DIV_HEATMAP}}":  div_heatmap,
    "{{DIV_QUADRANT}}": div_quad,
    "{{DIV_STREAM}}":   div_stream,
    "{{DIV_SUNBURST}}": div_sunburst,
}

HTML = TEMPLATE
for k, v in replacements.items():
    HTML = HTML.replace(k, v)

out_path = Path("index.html")
out_path.write_text(HTML, encoding="utf-8")
print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
print("done.")
