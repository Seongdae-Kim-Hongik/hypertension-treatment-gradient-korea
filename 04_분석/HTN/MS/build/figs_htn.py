# -*- coding: utf-8 -*-
#  Fig 1 (a) 전 기간 잔차 공간 RR 지도 (b) 조율·연령표준화율 추이 · Fig 2 (a) EHSA (b) 세 창 핫스팟 횟수 · Fig 3 강건 5개 변수의 모형별 RR
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from PIL import Image
from numbers_htn import load, ROB
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
SHP = os.path.expandvars("$ST_DATA_ROOT") + "/기타/R_Studio/FBD_DATA_ZIP/final.shp"
MM = 1 / 25.4; W = 170 * MM; DPI = 1200; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 7, "legend.fontsize": 7, "legend.title_fontsize": 7, "axes.linewidth": 0.5, "pdf.fonttype": 42})
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
G = gpd.read_file(SHP); G["region"] = G.region.map(NFC); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.sigungu_cd.astype(str).str[:2]; SIDO = G.dissolve("sido")   # 결합은 시군구 코드(cd)로만, 이름 결합 금지 규칙
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
rd = lambda f: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
PANEL_LABEL_PT = 48
def letter(ax, ch, dx=0.0, dy=1.03):   # 그림 좌표로 변환해 fig.text 하나의 상수로
    fig = ax.figure; x, y = fig.transFigure.inverted().transform(ax.transAxes.transform((dx, dy)))
    fig.text(x, y, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="bottom", ha="left")
def mapax(ax):   # 북침 = 채움 삼각형 + N 24 pt(3배), 축척 0-50-100 km(22호 CANM 그림과 같은 구현)
    from matplotlib.patches import Polygon, Rectangle
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    bx, by, bh = x0 + 0.60 * W_, y0 + 0.04 * H_, 0.010 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + k, by + bh + 0.008 * H_, t, ha="center", va="bottom", fontsize=7)
    ax.text(bx + 100000 + 0.012 * W_, by + bh / 2, "km", ha="left", va="center", fontsize=7)
    nx, ny, nw, nh = x0 + 0.93 * W_, y0 + 0.40 * H_, 0.054 * W_, 0.21 * H_
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=24, fontweight="bold")
def save(fig, k):
    p = os.path.join(FIG, f"Main_Fig{k}.png"); fig.savefig(p, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.02); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(DPI, DPI)); im.save(os.path.join(OUTF, f"Fig{k}.tif"), dpi=(DPI, DPI), compression="tiff_lzw")
    return im.size

# Fig 1
S6 = rd("S6_spatial_RR.csv"); S6["fbd_region"] = S6.fbd_region.map(NFC); assert len(S6) == 229
BR = [0, 0.8, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 99]; LB = ["<0.80", "0.80-0.89", "0.90-0.94", "0.95-0.99", "1.00-1.04", "1.05-1.09", "1.10-1.19", "≥1.20"]
PAL = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
fig = plt.figure(figsize=(W, 3.9)); a0 = fig.add_axes([0.0, 0.17, 0.50, 0.80]); a1 = fig.add_axes([0.62, 0.30, 0.36, 0.60])
d = S6.set_index("sigungu_cd"); gg = G.copy(); gg["v"] = gg.cd.map(d.RR); gg["c"] = gg.cd.map(d["class"]); assert gg.v.notna().all()
gg.plot(ax=a0, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(a0)
gg[gg.c == "coldspot"].boundary.plot(ax=a0, color="#2171B5", linewidth=0.6, linestyle=(0, (2.0, 1.2))); gg[gg.c == "hotspot"].boundary.plot(ax=a0, color="black", linewidth=0.6); letter(a0, "a")
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=0.8, label="Hot spot"), Patch(facecolor="none", edgecolor="#2171B5", linewidth=0.8, linestyle="--", label="Cold spot")]
a0.legend(handles=h, title="Residual spatial RR", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
yrs = sorted(N["asr"]); P = pd.read_csv(os.path.join(B, "panel_HTN_std3.csv")); y = P.groupby("year")[["cases", "offset"]].sum(); cr = 1e5 * y.cases / y.offset
a1.plot(yrs, [cr[t] / 1000 for t in yrs], color="#404040", marker="o", ms=2.5, lw=0.9, label="Crude")
a1.plot(yrs, [N["asr"][t] / 1000 for t in yrs], color="#b2182b", marker="s", ms=2.5, lw=0.9, label="Age-standardized")
a1.set_xticks([2011, 2014, 2017, 2020, 2024]); a1.set_ylim(10, 17); a1.set_ylabel("Treated persons per 100 population"); a1.set_xlabel("Year")
a1.spines[["top", "right"]].set_visible(False); a1.legend(frameon=False, loc="upper left"); letter(a1, "b", dx=-0.2, dy=1.16)
s1 = save(fig, 1)

# Fig 2
EH = rd("S11_ehsa.csv"); EH["fbd_region"] = EH.fbd_region.map(NFC)
CATS = [f"{a} {b}" for b in ("hot", "cold") for a in ("New", "Consecutive", "Intensifying", "Persistent", "Diminishing", "Sporadic", "Oscillating", "Historical")] + ["No pattern"]
EPAL = {"New hot": "#fdd0a2", "Consecutive hot": "#fdae6b", "Intensifying hot": "#a50f15", "Persistent hot": "#de2d26", "Diminishing hot": "#fc9272", "Sporadic hot": "#fee0d2", "Oscillating hot": "#d6a5c9", "Historical hot": "#bcbddc",
        "New cold": "#c6dbef", "Consecutive cold": "#9ecae1", "Intensifying cold": "#08519c", "Persistent cold": "#3182bd", "Diminishing cold": "#6baed6", "Sporadic cold": "#deebf7", "Oscillating cold": "#a1d99b", "Historical cold": "#c7e9c0", "No pattern": "#f7f7f7"}
WM = rd("S4b_window_spatialRR.csv"); WM["fbd_region"] = WM.fbd_region.map(NFC)
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); nc = WM[WM["class"] == "coldspot"].groupby("sigungu_cd").size()
assert int((nh == 3).sum()) == N["hot_all_windows"]
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 4.3)); fig.subplots_adjust(left=0.0, right=1.0, top=0.95, bottom=0.30, wspace=0.02)
gg = G.copy(); gg["c"] = gg.cd.map(EH.set_index("sigungu_cd").EHSA); assert gg.c.notna().all()
gg.plot(ax=a0, color=[EPAL[c] for c in gg.c], edgecolor="#a0a0a0", linewidth=LW); mapax(a0); letter(a0, "a")
cnt = EH.EHSA.value_counts(); pres = [c for c in CATS if c in cnt.index]
a0.legend(handles=[Patch(facecolor=EPAL[c], edgecolor="#777777", linewidth=LW, label=f"{c} ({cnt[c]})") for c in pres], title="Category (districts)", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
hh = gg.cd.map(nh).fillna(0).astype(int); cc = gg.cd.map(nc).fillna(0).astype(int)
gg["k"] = np.where((hh > 0) & (cc > 0), 9, hh - cc)   # 9 = 창에 따라 핫·콜드 모두
KP = {-3: "#2166AC", -2: "#67A9CF", -1: "#D1E5F0", 0: "#f7f7f7", 1: "#FDDBC7", 2: "#EF8A62", 3: "#B2182B", 9: "#c2a5cf"}
KL = {-3: "Cold spot in 3 windows", -2: "Cold spot in 2", -1: "Cold spot in 1", 0: "Neither", 1: "Hot spot in 1", 2: "Hot spot in 2", 3: "Hot spot in 3 windows", 9: "Hot and cold in different windows"}
gg.plot(ax=a1, color=[KP[k] for k in gg.k], edgecolor="#a0a0a0", linewidth=LW); mapax(a1); letter(a1, "b")
kc = gg.k.value_counts()
a1.legend(handles=[Patch(facecolor=KP[k], edgecolor="#777777", linewidth=LW, label=f"{KL[k]} ({kc.get(k, 0)})") for k in (3, 2, 1, 0, -1, -2, -3, 9) if kc.get(k, 0)], title="Windows 2011-2015, 2016-2019, 2020-2024", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
s2 = save(fig, 2)

# Fig 3
LAB = {"public_sports_facilities_per_100k": "Public sports facilities", "walking_practice_rate": "Walking practice", "moderate_pa_rate": "Moderate or vigorous activity",
       "screening_normalB_obesity_share": "Obesity management at screening", "high_risk_drinking_rate": "High-risk drinking"}
ORD = ["public_sports_facilities_per_100k", "walking_practice_rate", "moderate_pa_rate", "screening_normalB_obesity_share", "high_risk_drinking_rate"]
assert set(ORD) == set(ROB)
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "#000000", "o"),
       ("Knorr-Held type II", lambda v: N["s43"][("KH_typeII", v)][:3], "#2166AC", "s"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)][:3], "#B2182B", "D"),
       ("Infectious diseases (comparison outcome)", lambda v: N["nco"][("INFECT", v)][:3], "#7f7f7f", "^")]
fig, ax = plt.subplots(figsize=(W, 3.0)); fig.subplots_adjust(left=0.30, right=0.98, top=0.98, bottom=0.22)
off = np.linspace(-0.27, 0.27, len(MOD))
for i, v in enumerate(ORD):
    for (lab, f, col, mk), o in zip(MOD, off):
        e, lo, hi = f(v); ax.plot([lo, hi], [i + o] * 2, color=col, lw=0.8); ax.plot(e, i + o, marker=mk, color=col, ms=3.2, mew=0, ls="none")
ax.axvline(1, color="#404040", lw=0.5, ls=":"); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis()
xt = [0.985, 0.990, 0.995, 1.000, 1.005, 1.010]; ax.set_xticks(xt); ax.set_xticklabels([f"{x:.3f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 SD (95% credible interval)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=c, marker=m, lw=0.8, ms=3.2, mew=0, label=l) for l, _, c, m in MOD], loc="upper center", bbox_to_anchor=(0.35, -0.16), ncol=2, frameon=False)
s3 = save(fig, 3)
for k, s in zip((1, 2, 3), (s1, s2, s3)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/DPI*25.4:.0f} x {s[1]/DPI*25.4:.0f} mm")
