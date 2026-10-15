"""Three reproducible portfolio demos. Python 3, standard library only.
Run: python run.py. All inputs are synthetic, no external services contacted.
"""
import csv
import json
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
DATA = ROOT / 'data'


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def catalog():
    products, errors, duplicate_count = {}, [], 0
    paths = sorted((DATA / 'prices').glob('*.csv'))
    total = 0
    for path in paths:
        for row in read_csv(path):
            total += 1
            sku = row['sku'].strip().upper()
            try:
                price = Decimal(row['price'].replace(',', '.'))
                if not price.is_finite() or price <= 0 or not sku:
                    raise ValueError('Invalid product')
            except (InvalidOperation, ValueError):
                errors.append(dict(file=path.name, sku=sku, reason='Invalid or missing price/SKU'))
                continue
            if sku in products:
                duplicate_count += 1
            # Explicit business rule: keep the lowest valid supplier price per SKU.
            if sku not in products or price < products[sku]['price']:
                products[sku] = dict(sku=sku, name=' '.join(row['name'].split()), price=price, supplier=path.stem)
    write_csv(OUT / 'catalog.csv', ['sku', 'name', 'price', 'supplier'], sorted(products.values(), key=lambda p:p['sku']))
    write_csv(OUT / 'catalog-errors.csv', ['file', 'sku', 'reason'], errors)
    return dict(input_rows=total, supplier_files=len(paths), unique_products=len(products), duplicates=duplicate_count, rejected=len(errors))


def enquiries():
    # Replay real Telegram-style update envelopes offline. SQLite replaces a live sheet.
    updates = json.loads((DATA / 'telegram-updates.json').read_text(encoding='utf-8'))
    db_path = OUT / 'enquiries.sqlite'
    db = sqlite3.connect(db_path)
    db.execute('CREATE TABLE IF NOT EXISTS enquiries(update_id INTEGER PRIMARY KEY, name TEXT, contact TEXT, task TEXT)')
    added, duplicates, rejected = 0, 0, 0
    for update in updates:
        try:
            name, contact, task = [v.strip() for v in update['message']['text'].split('|', 2)]
            if not all((name, contact, task)):
                raise ValueError('Empty field')
        except (KeyError, ValueError):
            rejected += 1
            continue
        cursor = db.execute('INSERT OR IGNORE INTO enquiries VALUES (?, ?, ?, ?)', (update['update_id'], name, contact, task))
        added += cursor.rowcount
        duplicates += 1 - cursor.rowcount
    db.commit()
    rows = [dict(zip(['update_id', 'name', 'contact', 'task'], row)) for row in db.execute('SELECT * FROM enquiries ORDER BY update_id')]
    write_csv(OUT / 'enquiries.csv', ['update_id', 'name', 'contact', 'task'], rows)
    db.close()
    return dict(received=len(updates), newly_saved=added, duplicate_updates=duplicates, invalid_updates=rejected, total_saved=len(rows), mode='OFFLINE: no Telegram or Google Sheets connection')


def sales():
    grouped, rejected = {}, []
    rows = read_csv(DATA / 'sales.csv')
    for row in rows:
        try:
            qty, price = int(row['quantity']), Decimal(row['unit_price'])
            if qty <= 0 or not price.is_finite() or price < 0:
                raise ValueError('Invalid amount')
        except (ValueError, InvalidOperation):
            rejected.append(row)
            continue
        item = grouped.setdefault(row['product'], dict(product=row['product'], units=0, revenue=Decimal(0)))
        item['units'] += qty
        item['revenue'] += qty * price
    ranking = sorted(grouped.values(), key=lambda r:r['revenue'], reverse=True)
    write_csv(OUT / 'sales-report.csv', ['product', 'units', 'revenue'], ranking)
    write_csv(OUT / 'sales-errors.csv', ['product', 'quantity', 'unit_price'], rejected)
    return dict(input_rows=len(rows), accepted=len(rows)-len(rejected), rejected=len(rejected), units=sum(p['units'] for p in ranking), revenue=str(sum((p['revenue'] for p in ranking), Decimal(0))), currency='RUB', top_product=ranking[0]['product'] if ranking else None)


def main():
    OUT.mkdir(exist_ok=True)
    results = dict(catalog=catalog(), enquiries=enquiries(), sales=sales())
    (OUT / 'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
