import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
import squarify

df = pd.read_csv("nhs_all_years_processed.csv")
YR = 2020

INT_LO = float(df["Intensity"].quantile(0.10))
INT_HI = float(df["Intensity"].quantile(0.90))

cmap = LinearSegmentedColormap.from_list("tm", [
    (0.00, "#f08c4f"), (0.25, "#fbb893"), (0.50, "#fef3c7"),
    (0.75, "#a8c8f0"), (1.00, "#4a90e2")])
norm = Normalize(vmin=INT_LO, vmax=INT_HI)

sub = df[df["Year"] == YR].nlargest(40, "Burden").copy()
sub["Pct"]   = sub["Burden"] / sub["Burden"].sum() * 100
sub["Short"] = sub["Diagnosis"].str.slice(0, 30)

sup_g = sub.groupby("Super_Chapter")["Burden"].sum().sort_values(ascending=False)

fig = plt.figure(figsize=(14, 9), dpi=170)
ax  = fig.add_axes([0.02, 0.04, 0.84, 0.88])
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_axis_off()

sup_rects = squarify.squarify(
    squarify.normalize_sizes(sup_g.values, 100, 100), 0, 0, 100, 100)

for sup, sr in zip(sup_g.index, sup_rects):
    sx, sy, sw, sh = sr["x"], sr["y"], sr["dx"], sr["dy"]
    ax.add_patch(patches.Rectangle((sx, sy), sw, sh,
        facecolor="none", edgecolor="#333", linewidth=2.4, zorder=4))
    ax.text(sx + 1.0, sy + sh - 0.6, sup, ha="left", va="top",
            fontsize=11, fontweight="bold", color="#1f2937", zorder=6)

    chap_g = (sub[sub["Super_Chapter"] == sup]
              .groupby("Chapter_Name")["Burden"].sum()
              .sort_values(ascending=False))
    pad = max(2.6, sh * 0.07)
    iw, ih = sw, max(sh - pad, 1)
    chap_rects = squarify.squarify(
        squarify.normalize_sizes(chap_g.values, iw, ih), sx, sy, iw, ih)

    for chap, cr in zip(chap_g.index, chap_rects):
        cx, cy, cw, ch = cr["x"], cr["y"], cr["dx"], cr["dy"]
        ax.add_patch(patches.Rectangle((cx, cy), cw, ch,
            facecolor="none", edgecolor="#444", linewidth=1.2, zorder=3))
        if cw > 5 and ch > 3:
            ax.text(cx + 0.6, cy + ch - 0.4, chap, ha="left", va="top",
                    fontsize=9, fontweight="bold", color="#1f2937", zorder=5)
            cpad = min(2.2, ch * 0.18)
        else:
            cpad = 0.4
        leaves = sub[(sub["Super_Chapter"] == sup) &
                     (sub["Chapter_Name"] == chap)].sort_values("Burden", ascending=False)
        if leaves.empty: continue
        lh_inner = max(ch - cpad, 0.6)
        leaf_rects = squarify.squarify(
            squarify.normalize_sizes(leaves["Burden"].values, cw, lh_inner),
            cx, cy, cw, lh_inner)
        for (_, row), lr in zip(leaves.iterrows(), leaf_rects):
            lx, ly, lw, lhh = lr["x"], lr["y"], lr["dx"], lr["dy"]
            colour = cmap(norm(row["Intensity"]))
            ax.add_patch(patches.Rectangle((lx, ly), lw, lhh,
                facecolor=colour, edgecolor="white", linewidth=0.8, zorder=2))
            if lw > 4 and lhh > 2:
                fs = 7.5 if (lw < 7 or lhh < 4) else 8.5
                ax.text(lx + 0.4, ly + lhh - 0.3,
                        f"{row['Short']}\n{row['Pct']:.1f}%",
                        ha="left", va="top", fontsize=fs, color="#1f2937", zorder=6)

fig.text(0.43, 0.965,
         f"NHS Hospital Burden vs Per-patient Intensity - {YR}/{(YR+1)%100:02d}",
         ha="center", va="top", fontsize=15, fontweight="bold", color="#111")

cax = fig.add_axes([0.88, 0.10, 0.022, 0.78])
sm  = plt.cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
cb = fig.colorbar(sm, cax=cax)
cb.outline.set_linewidth(0.5)
cb.set_label("Per-patient\nintensity", fontsize=9, color="#374151", labelpad=8)
cb.ax.tick_params(labelsize=8, colors="#374151")

fig.savefig("supp_treemap.png", facecolor="white", bbox_inches="tight")
print("wrote supp_treemap.png")
