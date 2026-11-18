# build_refs_htn.py — journal 고혈압 판 참고문헌 메타데이터 캐시(refs_htn.json). 네트워크는 이 스크립트에서만.
#  키 = 원고 원천(draft md + content_htn.py)의 [@key]. manifest(ALL_refs.csv) PMID → PubMed esummary, 없으면 DOI → Crossref. 웹 문헌은 WEB 사전.
import os, re, json, time, urllib.request, urllib.parse, glob
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CE = os.path.dirname(HERE)
man = pd.read_csv(os.path.join(CE, "refs", "manifest", "ALL_refs.csv"), dtype=str).fillna("")
man["pmid"] = man.pmid.str.replace(r"\.0$", "", regex=True); M = man.set_index("key")
src = open(os.path.join(HERE, "content_htn.py"), encoding="utf-8").read() + "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(CE, "draft", "*.md")))
src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
keys = sorted({k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")})
WEB = {
 "web:nhis2026regional": dict(type="web", authors="National Health Insurance Service", title="Regional medical care utilization statistics: number of persons treated for major diseases by district of residence, hypertensive diseases (I10-I15), 2011-2024", url="https://kosis.kr", year=2026, accessed="20 October 2026"),
 "web:mois2026population": dict(type="web", authors="Ministry of the Interior and Safety", title="Resident registration population by district, sex, and 5-year age group, 2011-2024", url="https://jumin.mois.go.kr", year=2026, accessed="20 October 2026"),
}
JABBR = {"Political Science Research and Methods": "Polit. Sci. Res. Methods", "Journal of Hydrology": "J. Hydrol.", "Geographical Analysis": "Geogr. Anal.", "Econometrica": "Econometrica", "Statistical Science": "Stat. Sci.", "Statistics and Computing": "Stat. Comput."}
out = {}
miss = [k for k in keys if not k.startswith("web:") and k not in M.index]; assert not miss, miss
pm = [k for k in keys if not k.startswith("web:") and M.loc[k, "pmid"]]
for i in range(0, len(pm), 150):
    ids = ",".join(M.loc[k, "pmid"] for k in pm[i:i + 150])
    d = json.load(urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ids, timeout=60))["result"]
    for k in pm[i:i + 150]:
        r = d[M.loc[k, "pmid"]]
        au = [a["name"] for a in r["authors"] if a.get("authtype", "Author") == "Author"] or [a["name"] for a in r["authors"]]
        doi = next((a["value"] for a in r["articleids"] if a["idtype"] == "doi"), "") or M.loc[k, "doi"]
        pages = r.get("pages", "") or (r.get("elocationid", "").replace("pii: ", "").split(" doi")[0] if r.get("elocationid", "").startswith("pii:") else "")
        out[k] = dict(type="journal", authors=au, title=r["title"].rstrip("."), journal=r["source"], year=int(r["pubdate"][:4]), vol=r.get("volume", ""), issue=r.get("issue", ""), pages=pages, doi=doi, pmid=M.loc[k, "pmid"], verified="PubMed esummary " + time.strftime("%Y-%m-%d"))
    time.sleep(0.4)
for k in keys:
    if k.startswith("web:"): out[k] = WEB[k]; continue
    if k in out: continue
    doi = M.loc[k, "doi"]; assert doi, k
    m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "research (wwwwrte@gmail.com)"}), timeout=60))["message"]
    au = [f"{a.get('family','')} {''.join(x[0] for x in re.split(r'[ -]', a.get('given','')) if x)}".strip() for a in m.get("author", [])]
    jt = (m.get("short-container-title") or m.get("container-title") or [""])[0]; jt = JABBR.get((m.get("container-title") or [""])[0], jt)
    yr = (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0][0]
    out[k] = dict(type="journal", authors=au, title=re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0]), journal=jt, year=int(yr), vol=m.get("volume", ""), issue=m.get("issue", ""), pages=m.get("page", "") or m.get("article-number", ""), doi=doi, verified="Crossref " + time.strftime("%Y-%m-%d"))
    time.sleep(0.3)
JN = {"Polit. Sci. Res. Methods": "Polit Sci Res Methods", "Geogr. Anal.": "Geogr Anal", "The American Statistician": "Am Stat", "Stat. Sci.": "Stat Sci",
      "Journal of the Royal Statistical Society Series B: Statistical Methodology": "J R Stat Soc Series B Stat Methodol"}
FIXP = {"mann1945nonparametric": "245-259"}
def fullp(p):
    m = re.match(r"^(\d+)-(\d+)$", str(p))
    if not m: return p
    a, b = m.groups(); return p if len(b) >= len(a) else f"{a}-{a[:len(a)-len(b)]+b}"
for k, v in out.items():
    if v.get("type") != "journal": continue
    v["journal"] = JN.get(v["journal"], v["journal"]).replace(".", "")
    v["pages"] = FIXP.get(k, fullp(v.get("pages", "")))
    if v["title"].isupper(): v["title"] = v["title"].capitalize()
json.dump(out, open(os.path.join(HERE, "refs_htn.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(keys), "keys;", sum(v["type"] == "journal" for v in out.values()), "journal,", sum(v["type"] == "web" for v in out.values()), "web")
