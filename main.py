# main.py — Kivy-приложение (Android/ПК). Генерация .docx через docx_simple.

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, DictProperty
from kivy.clock import Clock
from kivy.utils import platform
from datetime import datetime
import os

from contract_logic import (
    INSTITUTIONS,
    BRIEF_LABELS,
    strict_parse_brief,
    detect_category,
    match_complect,
    get_hours,
    round_down_to_thousand,
)
from docx_simple import replace_in_docx

try:
    from plyer import filechooser, sharing
except ImportError:
    filechooser = None
    sharing = None

try:
    if platform == 'android':
        from android.permissions import request_permissions, Permission
    else:
        request_permissions = None
        Permission = None
except ImportError:
    request_permissions = None
    Permission = None

CONFIG_TEMPLATE_PATH_FILE = "last_template.txt"
CONFIG_SAVE_DIR_FILE = "last_save_dir.txt"


class Root(BoxLayout):
    preview_html = StringProperty("")
    log_text = StringProperty("")
    date_text = StringProperty(datetime.now().strftime("%d %B %Y г."))
    template_status = StringProperty("❌ Шаблон не выбран")
    citata_on = BooleanProperty(False)
    brief_data = DictProperty({})
    template_path = StringProperty("")
    last_save_dir = StringProperty("")

    def on_kv_post(self, base_widget):
        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, *_):
        if platform == 'android' and request_permissions and Permission:
            try:
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except Exception:
                pass
        self.load_last_template()
        self.load_last_save_dir()
        self.template_status = (
            f"✅ Шаблон: {os.path.basename(self.template_path)}"
            if self.template_path and os.path.exists(self.template_path)
            else "❌ Шаблон не выбран"
        )
        self.parse_brief()

    def log(self, msg):
        self.log_text += msg + "\n"

    def set_citata(self, value):
        self.citata_on = value
        self.update_preview()

    def load_last_template(self):
        try:
            if os.path.exists(CONFIG_TEMPLATE_PATH_FILE):
                with open(CONFIG_TEMPLATE_PATH_FILE, 'r', encoding='utf-8') as f:
                    p = f.read().strip()
                    if p and os.path.exists(p):
                        self.template_path = p
        except Exception:
            pass

    def load_last_save_dir(self):
        try:
            if os.path.exists(CONFIG_SAVE_DIR_FILE):
                with open(CONFIG_SAVE_DIR_FILE, 'r', encoding='utf-8') as f:
                    d = f.read().strip()
                    if d and os.path.isdir(d):
                        self.last_save_dir = d
        except Exception:
            pass

    def choose_template(self):
        if not filechooser:
            self.log("❗ filechooser недоступен — запустите на Android/desktop с plyer")
            return
        try:
            filechooser.open_file(filters=[("DOCX", "*.docx")], on_selection=self._on_template_chosen)
        except Exception as e:
            self.log(f"❗ Ошибка выбора файла: {e}")

    def _on_template_chosen(self, selection):
        if selection:
            self.template_path = selection[0]
            try:
                with open(CONFIG_TEMPLATE_PATH_FILE, 'w', encoding='utf-8') as f:
                    f.write(self.template_path)
            except Exception:
                pass
            self.template_status = f"✅ Шаблон: {os.path.basename(self.template_path)}"
            self.log(f"Шаблон выбран: {self.template_path}")

    def reset_form(self):
        self.ids.fio.text = ""
        self.ids.vk.text = ""
        self.ids.prepay.text = ""
        self.ids.pages.text = ""
        self.ids.hours.text = ""
        self.ids.brief.text = ""
        self.ids.institution.text = 'Авто'
        self.citata_on = False
        self.date_text = datetime.now().strftime("%d %B %Y г.")
        self.brief_data = {}
        self.preview_html = ""
        self.log_text = ""

    def parse_brief(self, *_):
        self.log_text = ""
        btxt = self.ids.brief.text
        user_type = self.ids.institution.text if self.ids.institution.text != "Авто" else None
        data = strict_parse_brief(btxt, user_type)
        category = detect_category(data.get('тип_учреждения', ''), data.get('класс', ''), data.get('номер_группы', ''))
        data['категория'] = category
        complect, pages = match_complect(data.get('стоимость_одного_альбома',''), category)
        data['комплект'] = complect or ''
        data['страницы_комплекта'] = pages or ''
        data['часы'] = get_hours(data.get('кол_альбомов',''), complect) if complect else ''
        self.brief_data = data
        self.update_preview()

    def update_preview(self):
        d = self.brief_data or {}
        cat = d.get('категория','')
        compl = d.get('комплект','')
        if d.get('тип_учреждения','') and d.get('номер_учреждения',''):
            inst_line = f"Учреждение: [b]{d.get('тип_учреждения','')} №{d.get('номер_учреждения','')}[/b]"
        elif d.get('тип_учреждения','') or d.get('номер_учреждения',''):
            txt = d.get('тип_учреждения','') or d.get('номер_учреждения','')
            inst_line = f"Учреждение: [color=#ff4444][b]{txt} (неполные данные)[/b][/color]"
        else:
            inst_line = "Учреждение: [color=#ff4444][b]не определено![/b][/color]"

        try:
            base_price = int(d.get('стоимость_одного_альбома','') or 0)
        except:
            base_price = 0
        price = base_price + (200 if (self.citata_on and base_price) else 0)

        try:
            alb = int(d.get('кол_альбомов', 0) or 0)
        except:
            alb = 0
        total = price * alb
        prepay_in = self.ids.prepay.text
        if not prepay_in:
            prepay_val = round_down_to_thousand(total * 0.3)
        else:
            try:
                prepay_val = int(prepay_in)
            except:
                prepay_val = round_down_to_thousand(total * 0.3)
        rest = total - prepay_val

        pages = self.ids.pages.text or (d.get('страницы_комплекта') or "")
        hours = self.ids.hours.text or (d.get('часы') or "")
        fio = self.ids.fio.text or d.get('фамилия','')
        vk = self.ids.vk.text

        if cat == "ДС":
            klass_for_file = d.get('номер_группы','')
        else:
            klass_for_file = d.get('класс_for_file','')
        fname = f"{d.get('номер_учреждения','')} {klass_for_file} {d.get('кол_альбомов','')} {base_price}.docx" \
            .replace('  ', ' ').replace('""','').replace(' .','.').replace('..','.')
        fname = fname.upper()

        lines = [
            inst_line,
            f"Класс/Группа: [b]{d.get('класс','')}[/b]",
            f"Категория: [b]{cat}[/b]" if cat else "",
            f"Комплект: [b]{compl}[/b]" if compl else "",
            f"Кол-во детей: [b]{d.get('кол_детей','')}[/b]",
            f"Кол-во альбомов: [b]{d.get('кол_альбомов','')}[/b]",
            f"Стоимость одного альбома: [b]{price}[/b]" + (" (с цитатами)" if self.citata_on else ""),
            f"Количество страниц: [b]{pages}[/b]",
            f"Количество часов: [b]{hours}[/b]",
            f"ФИО: [b]{fio}[/b]",
            f"Телефон: [b]{d.get('телефон','')}[/b]",
            (f"VK: [b]{vk}[/b]" if vk else ""),
            f"Общая сумма: [b]{total}[/b]",
            f"Предоплата: [b]{prepay_val}[/b]",
            f"Остаток: [b]{rest}[/b]",
            f"Дата: [b]{self.date_text}[/b]",
            f"Название файла: [color=#2c73d2][b]{fname}[/b][/color]",
        ]
        self.preview_html = "\n".join([s for s in lines if s])

    def generate(self):
        if not self.template_path or not os.path.exists(self.template_path):
            self.log("❗ Шаблон не выбран")
            return

        d = self.brief_data or {}
        try:
            base_price = int(d.get('стоимость_одного_альбома','') or 0)
        except:
            base_price = 0
        price = base_price + (200 if (self.citata_on and base_price) else 0)
        try:
            alb = int(d.get('кол_альбомов', 0) or 0)
        except:
            alb = 0
        total = price * alb
        prepay_in = self.ids.prepay.text
        if not prepay_in:
            prepay_val = round_down_to_thousand(total * 0.3)
        else:
            try:
                prepay_val = int(prepay_in)
            except:
                prepay_val = round_down_to_thousand(total * 0.3)
        rest = total - prepay_val

        fio = self.ids.fio.text or d.get('фамилия','')
        vk = self.ids.vk.text
        pages = self.ids.pages.text or (d.get('страницы_комплекта') or "")
        hours = self.ids.hours.text or (d.get('часы') or "")

        values = {
            "учреждение": f"{d.get('тип_учреждения','')} №{d.get('номер_учреждения','')}".strip(),
            "класс": d.get("класс", ""),
            "кол_детей": d.get("кол_детей", ""),
            "кол_альбомов": d.get("кол_альбомов", ""),
            "стоимость_одного_альбома": base_price,
            "общая_сумма": total,
            "предоплата": prepay_val,
            "остаток": rest,
            "фамилия": fio,
            "телефон": d.get("телефон", ""),
            "ссылка_ВК": vk,
            "кол_страниц": pages,
            "колвочасов": hours,
            "дата": self.date_text,
            "номер_договора": d.get("номер_договора", ""),
            "когдасъёмка": d.get("когдасъёмка", ""),
            "ц": ", Цитаты" if self.citata_on else ""
        }

        cat = d.get('категория','')
        klass_for_file = d.get('номер_группы','') if cat == "ДС" else d.get('класс_for_file','')
        short_name = f"{d.get('номер_учреждения','')} {klass_for_file} {d.get('кол_альбомов','')} {base_price}.docx" \
            .replace('  ', ' ').replace('""','').replace(' .','.').replace('..','.')
        short_name = short_name.upper()

        def _save_to(selection):
            if not selection:
                return
            path = selection[0]
            try:
                replace_in_docx(self.template_path, path, values)
                try:
                    with open(CONFIG_SAVE_DIR_FILE, 'w', encoding='utf-8') as f:
                        f.write(os.path.dirname(path))
                except Exception:
                    pass
                self.log(f"✅ Договор сохранён: {path}")
                try:
                    if sharing:
                        sharing.share(file_path=path)
                except Exception:
                    pass
            except Exception as e:
                self.log(f"❗ Ошибка: {e}")

        if filechooser:
            try:
                filechooser.save_file(on_selection=_save_to, filename=short_name)
            except Exception as e:
                self.log(f"❗ Ошибка сохранения: {e}")
        else:
            path = os.path.abspath(short_name)
            try:
                replace_in_docx(self.template_path, path, values)
                self.log(f"✅ Договор сохранён: {path}")
            except Exception as e:
                self.log(f"❗ Ошибка: {e}")

class ContractKivyApp(App):
    def build(self):
        return Builder.load_file("main.kv")

if __name__ == "__main__":
    ContractKivyApp().run()
