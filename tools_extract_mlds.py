# tools_extract_mlds.py
import re
import csv
from pathlib import Path
import pdfplumber

PDF_PATH = Path("Ucheb_plan_MLDS_mag1_och_04.04.2025.pdf")  # положи pdf рядом со скриптом или поправь путь
OUT_CSV = Path("data/mlds_skeleton.csv")

# Индексы типа: Б1.О.01, Б1.В.ДВ.02.02, Б2.О.01(П), Б3.01 и т.п.
IDX_RE = re.compile(r"(Б\d\.(?:О|В)(?:\.ДВ)?\.\d+(?:\.\d+)?(?:\([^)]+\))?|Б3\.\d+)\s+(.+)$")

def main():
    rows = []
    with pdfplumber.open(str(PDF_PATH)) as pdf:
        for pno, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                m = IDX_RE.match(line)
                if m:
                    index_code = m.group(1).strip()
                    name = m.group(2).strip()

                    # отрежем “мусор” справа, если попались компетенции или хвост
                    name = re.sub(r"\s{2,}.*$", "", name)

                    rows.append({
                        "plan": "MLDS",
                        "index_code": index_code,
                        "name": name,
                        "semester": "",        # заполнишь позже из таблицы
                        "credits": "",         # заполнишь позже
                        "course_type": "",     # mandatory/elective
                        "department": "",
                        "competencies": "",
                        "aliases": "",
                        "source": f"MLDS PDF p.{pno+1}",
                        "description": "",
                        "learning_outcomes": "",
                    })

    # уберём дубли по index_code+name
    uniq = {}
    for r in rows:
        key = (r["index_code"], r["name"])
        uniq[key] = r
    rows = list(uniq.values())

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Saved: {OUT_CSV} (rows={len(rows)})")

if __name__ == "__main__":
    main()