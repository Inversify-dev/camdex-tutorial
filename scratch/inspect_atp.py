import docx

doc = docx.Document('papers/ATP Difficult Questions NM.docx')
for i, p in enumerate(doc.paragraphs[:25]):
    t = p.text.strip()
    if t:
        print(f"P{i}: {t}")
