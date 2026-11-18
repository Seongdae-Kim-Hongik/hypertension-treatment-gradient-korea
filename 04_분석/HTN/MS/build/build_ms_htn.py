import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from jkms_engine import JKMS
import content_htn as C
HERE = os.path.dirname(os.path.abspath(__file__)); JHD = os.path.dirname(HERE); OUT = os.path.join(JHD, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_htn.json"), encoding="utf-8"))
DRAFT = os.path.join(JHD, "draft", "01_manuscript.md")
ZENODO = open(os.path.join(OUT, "zenodo_doi.txt")).read().strip()
TITLE = C.TITLE; RUNNING = C.RUNNING
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
ORCID = "0000-0002-1525-0091"
MARGIN = Cm(2.54)
N_TAB, N_FIG = 1, 3
FIGS = os.path.join(HERE, "figs")
AI = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript."

class TX(JKMS):
    """원고 서식: 여백 2.54 cm, 자동 쪽번호 오른쪽 위(머리글), 줄번호 연속(심사 편의)."""
    def _emit(self, p, text, sz=12, bold=False, italic=False):   # 음수 마이너스 = U+2212
        return super()._emit(p, re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text), sz, bold, italic)
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        for s in self.doc.sections:
            s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = MARGIN
            for e in s._sectPr.findall(qn("w:footerReference")): s._sectPr.remove(e)   # 바닥글 없음(빈 바닥글에 LibreOffice가 줄번호를 찍음)
            hp = s.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for kind, txt in (("begin", None), ("instr", "PAGE"), ("end", None)):
                r = hp.add_run(); r.font.size = Pt(10); r.font.name = "Times New Roman"
                if kind == "instr": it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._element.append(it)
                else: fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._element.append(fc)

def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: " {{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def strip(t): return re.sub(r"\{\{[^}]+\}\}|<[^>]+>", "", re.sub(r"\s*\[@[^\]]+\]", "", t))

def spref_old(r):   # Springer: Smith JJ. The world of science. Am J Sci. 1999;36:234–5. https://doi.org/…  7명 이상 = 6명 + et al.
    def abbrp(pg):
        m = re.match(r"^([A-Za-z]*)(\d+)\s*[-–]+\s*([A-Za-z]*)(\d+)$", pg)
        if not m: return pg
        p1, a, p2, b = m.groups()
        if len(a) == len(b):
            k = 0
            while k < len(a) - 1 and a[k] == b[k]: k += 1
            b = b[k:]
        return f"{p1}{a}–{b}"
    if r["type"] == "web": return f"{r['authors']}. {r['title']}. {r['year']}. {r['url']}. Accessed {r['accessed']}."
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:6]) + ", et al"
    vol = str(r.get("vol", "")).strip(); pg = abbrp(str(r.get("pages", "")).strip())
    s = f"{a}. {r['title'].rstrip('.')}. {r['journal']}. {r['year']}"
    if vol: s += f";{vol}"
    if pg: s += f":{pg}"
    s += "."
    if r.get("doi"): s += f" https://doi.org/{r['doi']}"
    return s

def spref(r):   # AMA 11판: 저자 6명 이하 전부, 7명 이상 = 3명 + et al. 쪽 범위 전체. doi:
    if r["type"] == "web": return f"{r['authors']}. {r['title']}. Published {r['year']}. Accessed {r['accessed']}. {r['url']}"
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    vol = str(r.get("vol", "")).strip(); pg = re.sub(r"\s*[-–]+\s*", "-", str(r.get("pages", "")).strip())
    s = f"{a}. {r['title'].rstrip('.')}. {r['journal']}. {r['year']}"
    if vol: s += f";{vol}"
    if pg: s += f":{pg}"
    s += "."
    if r.get("doi"): s += f" doi:{r['doi']}"
    return s

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("urban_population_share", "Urban population share, %"), ("clinics_per_100k", "Clinics per 100,000"),
            ("public_sports_facilities_per_100k", "Public sports facilities per 100,000"), ("walking_practice_rate", "Walking practice, %"), ("moderate_pa_rate", "Moderate or vigorous activity, %"),
            ("screening_normalB_obesity_share", "Obesity management at screening, %"), ("high_risk_drinking_rate", "High-risk drinking, %")]
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    rows = [["__H__", "Treated persons"],
            ["  District-years, No."] + [f"{T[c]['n']:,}" for c in cols],
            ["  Treated person-years, million"] + [f"{T[c]['cases']/1e6:.1f}" for c in cols],
            ["  Person-years, million"] + [f"{T[c]['py']/1e6:.1f}" for c in cols],
            ["  Crude rate per 100,000"] + [f"{T[c]['crude']:,.0f}" for c in cols],
            ["  Age-standardized rate per 100,000<sup>a</sup>"] + [f"{T[c]['asr']:,.0f}" for c in cols],
            ["  District STR, median<sup>b</sup>"] + [f"{T[c]['sir_med']:.2f}" for c in cols],
            ["  District STR, P10-P90<sup>b</sup>"] + [f"{T[c]['sir_p10']:.2f}-{T[c]['sir_p90']:.2f}" for c in cols],
            ["__H__", "District characteristics, mean (SD)"]]
    for v, lab in TAB1_COV: rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:.1f} ({T[c]['cov'][v][1]:.1f})" for c in cols])
    foot = (f"<sup>a</sup>Direct standardization to the 2015 national population in ten age groups; window values are means of annual rates ({N['asr_2011']:,.0f} in 2011 and {N['asr_2024']:,.0f} in 2024). "
            "<sup>b</sup>Observed over indirectly age-standardized expected counts summed over the window. P10-P90, 10th-90th percentile; SD, standard deviation; STR, standardized treatment ratio.")
    return ("Table 1 People treated for hypertension and district characteristics by calendar window, Korea, 2011-2024", ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, foot)

GROUPS = [("Physical activity and environment", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "community_gyms_per_100k", "village_sports_facilities_per_100k", "green_area_share", "cars_per_capita"]),
          ("Cardiometabolic behaviors and detection", ["screening_normalB_obesity_share", "current_smoking_rate", "high_risk_drinking_rate", "perceived_stress_rate", "good_self_rated_health_rate", "nutrition_label_use_rate", "screening_uptake"]),
          ("Social structure", ["older_single_household_share", "employment_rate", "regular_employee_share"]),
          ("Forced controls", ["urban_population_share", "clinics_per_100k", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"walking_practice_rate": "Walking practice", "moderate_pa_rate": "Moderate or vigorous activity", "public_sports_facilities_per_100k": "Public sports facilities", "community_gyms_per_100k": "Public community gyms",
         "village_sports_facilities_per_100k": "Village sports facilities", "green_area_share": "Green area share", "cars_per_capita": "Registered cars per capita",
         "screening_normalB_obesity_share": "Obesity management at screening", "current_smoking_rate": "Current smoking", "high_risk_drinking_rate": "High-risk drinking", "perceived_stress_rate": "Perceived stress",
         "good_self_rated_health_rate": "Good self-rated health", "nutrition_label_use_rate": "Nutrition label use", "screening_uptake": "Health screening uptake",
         "older_single_household_share": "Older single-person households", "employment_rate": "Employment rate", "regular_employee_share": "Regular employment",
         "urban_population_share": "Urban population share", "clinics_per_100k": "Clinics", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal independence", "pop80_share": "Population aged 80 years or older"}
def table2():   # 표 안 유의 표시는 값으로만(별표·Yes/No 판정 열 금지, 06 §6-C) → 'subset-stable' 판정은 각주로
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"]
    stable = [LABEL[v].lower() for g, vs in GROUPS[:-1] for v in vs if N["mv"].get(v) and N["mv"][v]["robust"]]
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k = N["s43"][("KH_typeIV", v)]
            rows.append([f"  {LABEL[v]}", f"{m['IRR']:.3f} ({m['lo']:.3f}-{m['hi']:.3f})", f"{100*mv['cred_frac']:.0f}" if mv else "NA", f"{k[0]:.3f} ({k[1]:.3f}-{k[2]:.3f})"])
    foot = (f"RRs per 1 standard deviation with 95% CrIs from a negative binomial model with a Besag-York-Mollié 2 district effect and random-walk and independent year effects (n = {N['n_rows']:,} district-years); credible means the CrI excludes 1 before rounding. "
            f"<sup>a</sup>Share of the 200 covariate-subset specifications containing the covariate with a credible RR; subset-stable (credible in at least 75% with the same sign in at least 95%): {', '.join(stable[:-1])}, and {stable[-1]}. "
            f"<sup>b</sup>With a Knorr-Held type IV space-time interaction (ΔWAIC {C.dW('KH_typeIV'):,.0f}). CrI, credible interval; NA, not applicable (forced controls); RR, rate ratio; WAIC, widely applicable information criterion.")
    return ("Table 1 District correlates of age-standardized hypertension treatment, principal and space-time interaction models", ["Covariate", "Principal RR (95% CrI)", "Credible, %<sup>a</sup>", "Type IV RR (95% CrI)<sup>b</sup>"], rows, foot)

FIGCAP = {
 1: "Geography and trend of hypertension treatment in Korea. a Residual spatial rate ratio (RR) by district, 2011-2024, shown as the posterior mean of the exponentiated Besag-York-Mollié 2 district effect from the principal model. Solid and dashed outlines, hot and cold spots (posterior probability RR > 1 above 0.95 or below 0.05); thick lines, province boundaries. b National crude and directly age-standardized (2015 population) treatment rates per 100 population",
 2: "Persistence of the district pattern. a Emerging hot spot analysis of empirical Bayes-smoothed standardized treatment ratios, 2011-2024 (Getis-Ord Gi* with Mann-Kendall trend); numbers of districts in parentheses. b Number of the three calendar windows in which each district was a hot or cold spot in the principal model refitted in each window",
 3: "Subset-stable district correlates across models. Rate ratios per 1 standard deviation (SD) with 95% credible intervals from the principal model, Knorr-Held type II and IV models, and the principal model for treated infectious diseases (comparison outcome)",
}
def foot_row(J, text, sz=10, ls=16):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=8.5):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=True); foot_row(J, t[3], 8, 13); J.counting = c

def data_statement():
    return ("All source data are publicly available aggregate statistics, as cited in the Methods and listed in the Supplemental Material. The processed district-year analytic data are available from the author on reasonable request.")
def code_statement():
    return (f"The analysis code and the scripts that generate every number, table, and figure are archived on Zenodo (https://doi.org/{ZENODO}); the record and its files are openly available.")

def put_fig(J, k):
    from PIL import Image
    src = os.path.join(FIGS, f"Main_Fig{k}.png"); sm = os.path.join(FIGS, f"_embed_Fig{k}.png")
    im = Image.open(src); w = 2000; im.resize((w, int(im.height * w / im.width))).save(sm, dpi=(300, 300))
    c = J.counting; J.counting = False
    p = J.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if getattr(J, "_pb", False): p.paragraph_format.page_break_before = True; J._pb = False
    p.add_run().add_picture(sm, width=Cm(16))
    J.para(f"<b>Figure {k}.</b> {FIGCAP[k]}.", before=4, after=8); J.counting = c

AFTER = {"Treated persons and trends": [("f", 1)], "Spatial pattern and persistence": [("f", 2)],
         "District correlates in the principal model": [("t", 2)], "Space-time interaction and other sensitivity analyses": [("f", 3)]}
def build(bw=0, aw=0, tw=0):
    D = read_draft(); J = TX(cite="bracket")
    # 제목 면
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim", before=6)
    J.para("Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea")
    J.para(f"<b>Corresponding author:</b> Seongdae Kim, {ADDRESS}. E-mail: kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.para(f"<b>Short title:</b> {RUNNING}", before=6)
    J.para(f"<b>Total word count:</b> {tw:,} words (title page through the last table, excluding the Supplemental Material); abstract {aw} words. <b>Tables:</b> {N_TAB}. <b>Figures:</b> {N_FIG}.", before=6)
    # 초록·키워드
    J.page_break(); J.head("Abstract", 1)
    for p in D["Abstract"]:
        if p.startswith("Keywords:"): J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6); continue
        lab, rest = p.split(": ", 1); assert lab in ("Background", "Methods", "Results", "Conclusions"); J.para(f"<b>{lab}:</b> {rest}")
    # 본문
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for h, p in C.METHODS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for h, p in C.RESULTS:
        J.head(h, 2); J.para(pandoc_cites(p), indent=True)
        for kind, k in AFTER.get(h, []):
            if kind == "t": J.page_break(); put_table(J, table2())
            else: put_fig(J, k)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### Perspectives"): J.head("Perspectives", 1); continue
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.page_break(); J.head("Article Information", 1)
    for h, t in (("Acknowledgments", "None."), ("Sources of Funding", "None."),
                 ("Disclosures", "None."),
                 ("Ethics approval", "The study used published aggregate statistics only and was approved by the Institutional Review Board of Hongik University (7002340-202511-HR-012, 4 November 2025; continuing review 7002340-202611-HR-040, 3 November 2026), which waived informed consent. The study was performed in accordance with the Declaration of Helsinki."),
                 ("Data availability", data_statement()), ("Code availability", code_statement()),
                 ("Author contributions", "Seongdae Kim conceived and designed the study, curated the data, performed the analysis, interpreted the results, and wrote and revised the manuscript. The author read and approved the final manuscript."),
                 ("Supplemental Material", "Supplementary Methods; Additional Results; Tables S1-S5; STROBE and RECORD checklist.")):
        J.head(h, 2); J.para(t)
    J.page_break(); J.head("References", 1)
    for n, k in enumerate(J.cites, 1): J.para(f"{n}. {spref(REFS[k])}")
    J.page_break(); J.head("Novelty and Relevance", 1)
    for p in D["Novelty and Relevance"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        for b in p.split("\n"): J.para("\u2022 " + b.lstrip("- ").strip())
    return J, D

def docx_bw(path):   # 본문(Introduction~Statements 직전, 소제목 포함, 그림 캡션 제외)과 전체(초록~참고문헌, 표·캡션 포함, 제목 면 제외)
    from docx import Document
    d = Document(path); ps = [x.text for x in d.paragraphs]; i = ps.index("Introduction"); j = ps.index("Article Information")
    body = sum(len(x.split()) for x in ps[i:j] if not x.startswith("Fig. "))
    a = ps.index("Abstract"); r = ps.index("References")
    tot = sum(len(x.split()) for x in ps) + sum(len(c.text.split()) for t in d.tables for rw in t.rows for c in {id(x._tc): x for x in rw.cells}.values())
    return body, tot
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_htn_ms", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path); P = d.paragraphs
        for i, p in enumerate(P):
            if p.text.strip() == orphan:
                while i > 0 and P[i - 1].text.strip() in heads: i -= 1   # 연속 제목 묶음의 첫 제목 앞에서 나눔
                q = P[i]
                if 'w:type="page"' in q._p.xml: return   # 이미 나눔이 있으면 반복하지 않음
                r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); q._p.insert(1 if q._p.pPr is not None else 0, r); break
        d.save(path); print("orphan fixed:", orphan)

ABBR_FIX = {"BYM2": "Besag-York-Mollié 2", "CrI": "credible interval", "CrIs": "credible intervals", "ICD-10": "International Classification of Diseases, 10th revision", "RR": "rate ratio", "RRs": "rate ratios",
            "SD": "standard deviation", "STR": "standardized treatment ratio", "WAIC": "widely applicable information criterion", "ΔWAIC": "difference in widely applicable information criterion", "STROBE": "Strengthening the Reporting of Observational Studies in Epidemiology",
            "RECORD": "Reporting of studies Conducted using Observational Routinely-collected health Data", "P10-P90": "10th-90th percentile", "NA": "not applicable"}
def _unused_abbreviations(path_ms):
    from docx import Document
    txt = "\n".join(p.text for p in Document(path_ms).paragraphs) + "\n" + "\n".join(c.text for t in Document(path_ms).tables for r in t.rows for c in r.cells)
    used = sorted({k for k in ABBR_FIX if re.search(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", txt)} - {"CrIs", "RRs"}, key=str.lower)
    A = TX(cite="bracket"); A.para("<b>List of abbreviations</b>"); A.para(f"Manuscript: {TITLE}", before=6)
    for k in used: A.para(f"{k}, {ABBR_FIX[k]}")
    return A, used

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript.docx"); D = read_draft()
    aw = sum(len(strip(x).split()) for x in D["Abstract"] if not x.startswith("Keywords:"))
    J, D = build(); J.doc_title = "Manuscript"; J.save(p); bw, tw = docx_bw(p)
    J, D = build(bw, aw, tw); J.doc_title = "Manuscript"; J.save(p); bw2, tw2 = docx_bw(p)
    J, D = build(bw2, aw, tw2); J.doc_title = "Manuscript"; J.save(p); bw3, tw3 = docx_bw(p); assert tw3 == tw2, (tw2, tw3); tw2 = tw3
    heads = {"Abstract", "Introduction", "Methods", "Results", "Discussion", "Perspectives", "Article Information", "Acknowledgments", "Sources of Funding", "Disclosures", "References", "Strengths and limitations", "Ethics approval", "Data availability", "Code availability", "Author contributions", "Supplemental Material", "Novelty and Relevance", "What Is New?", "What Is Relevant?", "Clinical/Pathophysiological Implications?"} | {h for h, _ in C.METHODS + C.RESULTS}
    fix_orphans(p, heads)
    open(os.path.join(OUT, "wordcount.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\ntotal_words={tw2}\nrefs={len(J.cites)}\ntables={N_TAB}\nfigures={N_FIG}\n")
    print(f"body {bw} | abstract {aw} | total {tw2} | refs {len(J.cites)}")
