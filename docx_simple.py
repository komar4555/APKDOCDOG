# docx_simple.py
# Простая замена плейсхолдеров {ключ} в .docx без python-docx/lxml.
# ВАЖНО: плейсхолдеры в шаблоне должны быть цельной строкой (не разбиты форматированием).

import zipfile, shutil, os, tempfile

XML_PARTS = (
    "word/document.xml",
    "word/header1.xml", "word/header2.xml", "word/header3.xml",
    "word/footer1.xml", "word/footer2.xml", "word/footer3.xml",
)

def replace_in_docx(template_path: str, out_path: str, values: dict):
    # копируем шаблон → выходной .docx
    shutil.copyfile(template_path, out_path)

    tmpdir = tempfile.mkdtemp(prefix="docx_")
    try:
        # распаковать docx как zip
        with zipfile.ZipFile(out_path, 'r') as zin:
            zin.extractall(tmpdir)

        # заменить плейсхолдеры в основных частях
        for rel in XML_PARTS:
            p = os.path.join(tmpdir, rel)
            if not os.path.exists(p):
                continue
            with open(p, "r", encoding="utf-8") as f:
                xml = f.read()
            for k, v in values.items():
                token = "{" + k + "}"
                xml = xml.replace(token, str(v))
            with open(p, "w", encoding="utf-8") as f:
                f.write(xml)

        # собрать обратно в docx
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root, _, files in os.walk(tmpdir):
                for name in files:
                    full = os.path.join(root, name)
                    arc = os.path.relpath(full, tmpdir)
                    zout.write(full, arc)
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except:
            pass
