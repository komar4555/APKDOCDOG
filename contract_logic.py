# contract_logic.py
# Основная логика парсинга/подсчётов (без зависимостей от python-docx).

import re
from datetime import datetime

INSTITUTIONS = [
    "Школа", "Детский сад", "Лицей", "Гимназия", "Прогимназия", "Интернат"
]

BRIEF_LABELS = [
    "1. Учреждение",
    "2. Класс/Группа",
    "3. Всего детей",
    "4. Альбомов",
    "5. Цена/Комплект",
    "6. Телефон",
    "7. ФИО (если есть)"
]

COMPLET_RANGE = [
    ("Планшет", 1600, 1900, 2, 2, 2),
    ("Минимум", 2000, 2300, 4, 4, 4),
    ("Классик", 2600, 2700, 10, 10, 10),
    ("Премиум", 2800, 2900, None, 12, 20)
]

def remove_leading_numbering(lines):
    return [re.sub(r'^\s*\d+\.\s*', '', line).strip() for line in lines]

def parse_line_safe(lines, idx):
    return lines[idx] if idx < len(lines) else ""

def extract_phones(line):
    phones = re.findall(r'((?:\+7|8|7)?\d{10,11})', line.replace(' ', '').replace('-', ''))
    phones_fmt = []
    for p in phones:
        p = p.lstrip("+")
        if p.startswith("8"):
            p = "7" + p[1:]
        elif p.startswith("9"):
            p = "7" + p
        phones_fmt.append("+" + p if len(p) == 11 else p)
    return list(dict.fromkeys(phones_fmt))

def detect_category(inst, klass, group):
    school_words = ["школа", "интернат", "прогимназия", "гимназия", "лицей"]
    if "сад" in (inst or "").lower():
        return "ДС"
    if any(word in (inst or "").lower() for word in school_words):
        digits = re.findall(r'\d+', klass or "")
        if digits:
            grade = int(digits[0])
            if 1 <= grade <= 4:
                return "МЛ"
            if 5 <= grade <= 11:
                return "СТ"
    return ""

def match_complect(price, category):
    try:
        p = int(price)
    except:
        return None, None
    for name, mn, mx, pages, prem_ds, prem_ml in COMPLET_RANGE:
        if mn <= p <= mx:
            if name == "Премиум":
                return (name, prem_ds) if category == "ДС" else (name, prem_ml)
            return name, pages
    return None, None

def get_default_price(komplekt, category):
    if not komplekt or not category:
        return ""
    k = komplekt.lower()
    if category == "МЛ":
        if "классик" in k: return "2600"
        if "премиум" in k: return "2800"
        if "планшет" in k: return "1700"
        if "минимум" in k: return "2100"
    return ""

def get_hours(album_count, complect):
    try:
        n = int(album_count)
    except:
        return ""
    if complect == "Планшет":
        return 1 if n <= 20 else 2 if n <= 39 else 3
    if complect == "Минимум":
        return 1 if n < 18 else 2 if n <= 28 else 3
    if complect in ("Классик", "Премиум"):
        return 1 if n < 18 else 2 if n <= 25 else 3
    return ""

def round_down_to_thousand(num):
    try:
        return int(num) // 1000 * 1000
    except:
        return 0

def clean_group_title(title):
    t = (title or "").strip()
    t = re.sub(r'(?i)\b(группа|группы|номер|№|no\.?)\b', '', t)
    t = re.sub(r'\d+', '', t)
    t = t.replace('"', '').replace("«", '').replace("»", '').replace("'", '')
    t = t.replace("(", '').replace(")", '')
    t = re.sub(r'\s{2,}', ' ', t).strip()
    return t[0].upper() + t[1:] if t else ""

def smart_brief_lines(brief):
    lines = [l.strip() for l in (brief or "").strip().split('\n') if l.strip()]
    lines = remove_leading_numbering(lines)
    if len(lines) == 1:
        parts = re.split(r'[;,]', lines[0])
        if len(parts) < 6: parts = re.split(r'\s{2,}', lines[0])
        if len(parts) < 6: parts = re.split(r'\s+', lines[0])
        lines = remove_leading_numbering([p.strip() for p in parts if p.strip()])
    if len(lines) > 7:
        skip = ['номер','школ','сад','учреждение','группа','класс',
                'количество','всего','альбом','вид','цена','стоимость',
                'телефон','ответств','фио','название']
        result, prev = [], False
        for line in lines:
            lwr = line.lower()
            if any(w in lwr for w in skip) or re.match(r'^\d+\.', lwr):
                prev = True; continue
            if prev or (not any(w in lwr for w in skip) and not re.match(r'^\d+\.', lwr)):
                result.append(line); prev = False
        if 5 <= len(result) <= 8:
            lines = result
        else:
            lines2 = [line for line in lines if not (any(w in line.lower() for w in skip) or re.match(r'^\d+\.', line.lower()))]
            if 5 <= len(lines2) <= 8: lines = lines2
    return lines

def strict_parse_brief(brief, user_institution=None):
    lines = smart_brief_lines(brief)
    data, found = {'_lines': lines}, False

    # 1–3: поиск типа учреждения и номера
    for line in lines[:3]:
        lwr = line.lower()
        if re.search(r'\bдс\b', lwr) or re.search(r'\bсад\b', lwr):
            num = re.search(r'(\d+)', line)
            data['тип_учреждения'] = "Детский сад"
            data['номер_учреждения'] = num.group(1) if num else ""
            found = True; break
        if re.search(r'\b(сош|сш|средняя\s*школа)\b', lwr):
            num = re.search(r'(\d+)', line)
            data['тип_учреждения'] = "Школа"
            data['номер_учреждения'] = num.group(1) if num else ""
            found = True; break
        for ins in INSTITUTIONS:
            if ins.lower() in lwr:
                num = re.search(r'(\d+)', line)
                data['тип_учреждения'] = ins
                data['номер_учреждения'] = num.group(1) if num else ""
                found = True; break
        if found: break

    if not found:
        if lines and re.fullmatch(r'\d+', lines[0]):
            data['тип_учреждения'] = user_institution or "Школа"
            data['номер_учреждения'] = lines[0]
        elif user_institution:
            num = re.search(r'(\d+)', lines[0]) if lines else None
            data['тип_учреждения'] = user_institution
            data['номер_учреждения'] = num.group(1) if num else ""
        else:
            data['тип_учреждения'] = ""
            data['номер_учреждения'] = ""

    # класс/группа
    group_line = parse_line_safe(lines, 1)
    m = re.search(r'(\d+)', group_line)
    group = m.group(1) if m else ""
    title_match = re.search(r'["«](.+?)["»]', group_line)
    title = clean_group_title(title_match.group(1) if title_match else re.sub(r'(?i)\b(группа|группы|номер|№|no\.?)\b|\d+', '', group_line))

    if data.get('тип_учреждения') and "сад" in data['тип_учреждения'].lower():
        data['класс'] = f'Группа {group} "{title}"' if title else f'Группа {group}'
        data['номер_группы'] = group
        data['название_группы'] = title
    else:
        kls = ''.join(re.findall(r'[0-9]+[А-Яа-яA-Za-zЁё]', group_line.replace(' ', '').replace('"', '')))
        if not kls:
            kls = ''.join(re.findall(r'[A-Za-zА-Яа-яЁё0-9]+', group_line.replace(' ', '').replace('"', '')))
        data['класс'] = kls
        digits_list = re.findall(r'\d+', kls)
        data['номер_класса'] = digits_list[0] if kls and digits_list else ""

    digits = re.findall(r'\d+', parse_line_safe(lines, 2))
    data['кол_детей'] = digits[0] if digits else ""
    digits = re.findall(r'\d+', parse_line_safe(lines, 3))
    data['кол_альбомов'] = digits[0] if digits else ""
    price_str = parse_line_safe(lines, 4).replace(' ', '')
    price = re.search(r'(\d{3,5})', price_str)
    data['стоимость_одного_альбома'] = price.group(1) if price else ""

    # автоцена по комплекту, если цена не указана
    komplekt = ""
    if not data['стоимость_одного_альбома']:
        for k in ["классик", "премиум", "планшет", "минимум"]:
            if k in price_str.lower():
                komplekt = k.capitalize()
                break
        data['стоимость_одного_альбома'] = get_default_price(
            komplekt,
            detect_category(data.get('тип_учреждения',''), data.get('класс',''), data.get('номер_группы',''))
        )
        data['комплект'] = komplekt

    tel_line = parse_line_safe(lines, 5)
    all_phones = []
    for l in lines:
        all_phones += extract_phones(l)
    data['телефон'] = ", ".join(all_phones)
    fio = lines[6].strip() if len(lines) >= 7 and lines[6].strip() else re.sub(r'\d+|\+7|8|7', '', tel_line).strip(", .")
    data['фамилия'] = fio

    if (data.get('тип_учреждения','').lower() in ['школа','лицей','гимназия','прогимназия','интернат']):
        data['когдасъёмка'] = "Съёмка в студии проходит в будние дни."
    elif data.get('тип_учреждения','').lower().find('сад') != -1:
        data['когдасъёмка'] = "Съёмка в студии проходит в выходные дни."
    else:
        data['когдасъёмка'] = ""

    data['дата'] = datetime.now().strftime("%d %B %Y г.")
    data['номер_договора'] = datetime.now().strftime("%d%m%y")
    data['класс_for_file'] = (data['класс'].replace("Группа", "").replace('"','').replace("«",'').replace("»",'').replace("'",'').strip().upper() if data.get('класс') else "")
    return data
