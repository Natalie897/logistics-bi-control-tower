"""Validated ETL: staging CSV -> SQLite star schema -> Power BI export files."""
from pathlib import Path
from collections import defaultdict
from datetime import date, timedelta
import csv
import sqlite3
import argparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'demo'
FIELDS={
'customers.csv':['customer_id','state','macro_region'],
'orders.csv':['order_id','customer_id','order_date','promised_date','delivered_date','status','service_type','freight_value'],
'order_items.csv':['order_id','line_no','sku','unit_price','quantity']}

def rows(path,expected):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=expected: raise ValueError(f'Invalid columns in {path}: {reader.fieldnames}')
        return list(reader)

def valid_date(s): return date.fromisoformat(s)
def make_date_key(d): return int(d.strftime('%Y%m%d'))

def build(input_dir=DATA,db_path=ROOT/'data'/'warehouse'/'logistics.sqlite',export_dir=ROOT/'data'/'powerbi'):
    input_dir=Path(input_dir);db_path=Path(db_path);export_dir=Path(export_dir)
    inputs={filename:rows(input_dir/filename, cols) for filename,cols in FIELDS.items()}
    customers=inputs['customers.csv']; orders=inputs['orders.csv']; items=inputs['order_items.csv']
    cm={r['customer_id']:r for r in customers}
    if len(cm)!=len(customers): raise ValueError('Duplicate customer_id')
    om={r['order_id']:r for r in orders}
    if len(om)!=len(orders): raise ValueError('Duplicate order_id')
    rollup=defaultdict(lambda:[0,0.0]); item_keys=set()
    for r in items:
        oid=r['order_id']; line=int(r['line_no']); price=float(r['unit_price']); qty=int(r['quantity'])
        if oid not in om or qty<1 or price<0 or (oid,line) in item_keys: raise ValueError('Invalid order item: '+str(r))
        item_keys.add((oid,line)); rollup[oid][0]+=qty;rollup[oid][1]+=price*qty
    states=sorted({(c['state'],c['macro_region']) for c in customers});by_state={}
    for state,area in states:
        if state in by_state and by_state[state]!=area: raise ValueError('Inconsistent macro_region for state '+state)
        by_state[state]=area
    region_key={name:i+1 for i,name in enumerate(sorted(by_state))}
    service_types=sorted({o['service_type'] for o in orders})
    service_key={name:i+1 for i,name in enumerate(service_types)}
    date_values=set()
    for r in orders:
        if not r['order_date']: raise ValueError('Missing purchase date')
        date_values.add(valid_date(r['order_date']))
    # Contiguous calendar is necessary for Power BI time intelligence.
    start,end=min(date_values),max(date_values)
    date_values={start+timedelta(days=i) for i in range((end-start).days+1)}
    # Contiguous calendar is necessary for Power BI time intelligence.
    start,end=min(date_values),max(date_values)
    date_values={start+timedelta(days=i) for i in range((end-start).days+1)}
    db_path.parent.mkdir(parents=True,exist_ok=True)
    if db_path.exists(): db_path.unlink()
    con=sqlite3.connect(db_path)
    try:
        con.executescript((ROOT/'sql'/'sqlite_schema.sql').read_text(encoding='utf-8'))
        with con:
            con.executemany('INSERT INTO stg_customers VALUES (?,?,?)',[(r['customer_id'],r['state'],r['macro_region']) for r in customers])
            con.executemany('INSERT INTO stg_orders VALUES (?,?,?,?,?,?,?,?)',[tuple(r[k] for k in FIELDS['orders.csv']) for r in orders])
            con.executemany('INSERT INTO stg_order_items VALUES (?,?,?,?,?)',[(r['order_id'],r['line_no'],r['sku'],r['unit_price'],r['quantity']) for r in items])
            con.executemany('INSERT INTO dim_date VALUES (?,?,?,?,?,?)',[(make_date_key(d),d.isoformat(),d.year,d.month,d.strftime('%Y-%m'),d.strftime('%A')) for d in sorted(date_values)])
            con.executemany('INSERT INTO dim_region VALUES (?,?,?)',[(region_key[s],s,by_state[s]) for s in sorted(by_state)])
            con.executemany('INSERT INTO dim_service VALUES (?,?)',[(service_key[s],s) for s in service_types])
            facts=[]
            for r in orders:
                oid=r['order_id'];
                if r['customer_id'] not in cm: raise ValueError('Unknown customer '+r['customer_id'])
                if oid not in rollup: raise ValueError('Order without items: '+oid)
                ordered=valid_date(r['order_date']); promised=valid_date(r['promised_date']); delivered=valid_date(r['delivered_date']) if r['delivered_date'] else None
                if promised<ordered: raise ValueError('Promised date before purchase')
                if r['status'] not in ('delivered','canceled'): raise ValueError('Unsupported status '+r['status'])
                if r['status']=='delivered' and delivered is None: raise ValueError('Delivered status without delivery date')
                if r['status']=='canceled' and delivered is not None: raise ValueError('Canceled order has delivery date')
                if delivered and delivered<ordered: raise ValueError('Delivery before order')
                freight=float(r['freight_value'])
                if freight<0: raise ValueError('Negative freight')
                qty,merchandise=rollup[oid]; merchandise=round(merchandise,2)
                days=(delivered-ordered).days if delivered else None
                lag=(delivered-promised).days if delivered else None
                is_late=int(lag>0) if lag is not None else None
                facts.append((oid,make_date_key(ordered),region_key[cm[r['customer_id']]['state']],
                 service_key[r['service_type']],r['customer_id'],r['status'],promised.isoformat(),
                 delivered.isoformat() if delivered else None,qty,merchandise,round(freight,2),
                 round(merchandise+freight,2),days,lag,is_late))
            con.executemany('INSERT INTO fact_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',facts)
        assert con.execute('SELECT COUNT(*) FROM fact_orders').fetchone()[0]==len(orders)
        assert con.execute('PRAGMA foreign_key_check').fetchall()==[]
        export_dir.mkdir(parents=True,exist_ok=True)
        for name in ['fact_orders','dim_date','dim_region','dim_service']:
            cur=con.execute('SELECT * FROM '+name)
            with (export_dir/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f);w.writerow([c[0] for c in cur.description]);w.writerows(cur.fetchall())
        report={'orders':len(orders),'customers':len(customers),'items':len(items),
            'delivered':con.execute("SELECT COUNT(*) FROM fact_orders WHERE status='delivered'").fetchone()[0],
            'late_delivered':con.execute("SELECT COUNT(*) FROM fact_orders WHERE is_late=1").fetchone()[0],
            'order_value_sum':round(con.execute('SELECT SUM(order_value) FROM fact_orders').fetchone()[0],2)}
        return report
    finally: con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',default=str(DATA));p.add_argument('--db',default=str(ROOT/'data'/'warehouse'/'logistics.sqlite'))
    p.add_argument('--export-dir',default=str(ROOT/'data'/'powerbi'))
    a=p.parse_args();print(build(a.input_dir,a.db,a.export_dir))
