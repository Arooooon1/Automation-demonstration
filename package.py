"""Create result cards from actual run output; Pillow needed only for cards."""
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
s = json.loads((root / 'results/summary.json').read_text(encoding='utf-8'))
assert s['catalog'] == dict(input_rows=12, supplier_files=3, unique_products=8, duplicates=2, rejected=2)
assert s['enquiries']['total_saved'] == 3
assert s['sales']['revenue'] == '130900'
assert s['sales']['units'] == 50
font_path = 'C:/Windows/Fonts/arial.ttf'
def font(size): return ImageFont.truetype(font_path, size)
cards = [
    ('01-catalog', 'Объединение прайс-листов', [('Файлов поставщиков', s['catalog']['supplier_files']), ('Исходных строк', s['catalog']['input_rows']), ('Товаров в каталоге', s['catalog']['unique_products']), ('Повторов объединено', s['catalog']['duplicates']), ('Ошибок вынесено в отчёт', s['catalog']['rejected'])], 'Python · CSV · Decimal'),
    ('02-enquiries', 'Обработка заявок', [('Входящих событий', s['enquiries']['received']), ('Заявок в базе', s['enquiries']['total_saved']), ('Повторов пропущено', s['enquiries']['duplicate_updates']), ('Некорректных заявок', s['enquiries']['invalid_updates'])], 'Python · SQLite · Telegram-style JSON / офлайн'),
    ('03-sales', 'Отчёт по продажам', [('Исходных строк', s['sales']['input_rows']), ('Строк принято', s['sales']['accepted']), ('Продано единиц', s['sales']['units']), ('Выручка, ₽', s['sales']['revenue']), ('Лидер по выручке', s['sales']['top_product'])], 'Python · CSV · Decimal'),
]
for name, title, metrics, tools in cards:
    im = Image.new('RGB', (1400, 1000), '#101820')
    d = ImageDraw.Draw(im)
    d.text((70,55), 'IDEA TO ACTION / AUTOMATION LAB', font=font(23), fill='#73dfc2')
    d.text((70,125), title, font=font(52), fill='white')
    d.text((70,210), 'ДЕМО · ТЕСТОВЫЕ ДАННЫЕ · РЕЗУЛЬТАТ ЗАПУСКА', font=font(24), fill='#abb8c4')
    for i, (label, value) in enumerate(metrics):
        y = 300+i*100
        d.line((70,y+75,1330,y+75), fill='#30414c', width=2)
        d.text((80,y), label, font=font(32), fill='#c6d2dc')
        value = str(value)
        d.text((1310-d.textlength(value,font=font(40)), y-4), value, font=font(40), fill='#73dfc2')
    d.text((70,865), tools, font=font(25), fill='white')
    d.text((70,925), 'Карточка по summary.json. Не скриншот клиентской системы.', font=font(22), fill='#abb8c4')
    im.save(root / 'results' / (name+'.png'))
with zipfile.ZipFile(root.parent / 'automation-demos.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            z.write(p, Path('automation-demos') / p.relative_to(root))
print('Checks passed. Three cards and archive generated.')
