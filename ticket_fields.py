"""Parse Chinese/Korean spreadsheet fields without treating IDs, notes or seat masks as rows."""
import re
import unicodedata
VALID_SECTIONS={str(n) for a,b in [(101,114),(201,210),(301,322),(401,424)] for n in range(a,b+1)}|{f'F{n}' for n in range(1,21)}|{f'T{n:02}' for n in list(range(1,8))+list(range(11,18))}
ROW=r'(?:\d{1,2}(?:\s*[/~\-至到]\s*\d{1,2})*|[A-Z](?:\(\d{1,2}\))?|[一二三四五六七八九十]{1,3})'

def normalize_row(value):
    text=unicodedata.normalize('NFKC',str(value)).strip()
    text=re.sub(r'^(?:票上排数|排数|排號|排号|排|row)\s*[:：]?\s*','',text,flags=re.I)
    text=re.sub(r'(?:排|열)\s*$','',text).strip()
    if not re.fullmatch(ROW,text,re.I):return ''
    if re.fullmatch('[一二三四五六七八九十]+',text):
        if not re.fullmatch(r'(?:[一二三四五六七八九]|[一二三四五六七八九]?十[一二三四五六七八九]?)',text):return ''
        digits={c:i for i,c in enumerate('零一二三四五六七八九')}
        if '十' in text:
            a,b=text.split('十');return str((digits.get(a,1)*10)+digits.get(b,0))
        return str(digits[text])
    return re.sub(r'\s+','',text).upper()

def extract_text_fields(raw):
    text=unicodedata.normalize('NFKC',raw).replace('|',' ')
    # A combined location, or a labelled section, takes precedence over a serial such as T11.
    candidates=list(re.finditer(r'(?<![A-Z0-9])(?:F(?:20|1\d|[1-9])|T(?:0[1-7]|1[1-7]))(?!\d)',text,re.I))
    section_match=next((m for m in candidates if re.match(r'\s*(?:区(?!域)|區(?!域)|구역)',text[m.end():])),None)
    if section_match is None:section_match=next((m for m in candidates if re.search(r'(?:区域|區域|区|section|FLOOR)\s*[:：]?\s*$',text[:m.start()],re.I)),None)
    if section_match is None:
        section_match=next((m for m in re.finditer(r'(?<![A-Z0-9])\d{3}(?![\d,])',text) if m[0] in VALID_SECTIONS and re.search(r'(?:区域|區域|区|section)\s*[:：]?\s*$',text[:m.start()],re.I)),None)
    if section_match is None:section_match=candidates[0] if candidates else None
    if section_match is None:
        section_match=next((m for m in re.finditer(r'(?<![A-Z0-9])\d{3}(?![\d,])',text) if m[0] in VALID_SECTIONS),None)
    section=section_match[0].upper() if section_match else 'UNRESOLVED'
    tail=text[section_match.end():] if section_match else ''
    # Prefer 排数/排号 labels and the first printed row after the section, never a later 实际排 note.
    labelled=re.search(r'(?:票上排数|排数|排號|排号|row)\s*[:：]?\s*('+ROW+r')',text,re.I)
    after=re.match(r'\s*(?:(?:区|區|구역)\s*)?(?:第\s*)?('+ROW+r')(?=\s|排|열|$)',tail,re.I)
    row=normalize_row(labelled[1] if labelled else after[1] if after else '')
    seat_label=re.search(r'(?:座位号|座位號|座号|座號|座位|seat)\s*[:：]?\s*([^|;；]+)',text,re.I)
    seat_text=seat_label[1] if seat_label else tail
    seat=re.search(r'(?<![A-Z0-9])(?:[0-9]\s*)?X(?:\s*/\s*(?:[0-9]\s*)?X)?(?![A-Z0-9])',seat_text,re.I)
    date=re.search(r'202[67]\s*[-/.]?\s*0?1\s*[-/.]?\s*1[56](?!\d)',text)
    if not date:date=re.search(r'(?<!\d)(?:0?1|11)\s*[./月]\s*1[56](?:\s*日)?',text)
    return dict(section=section,row=row,seat_as_printed=re.sub(r'\s+','',seat[0]).upper() if seat else '',date_as_printed=date[0] if date else '')
