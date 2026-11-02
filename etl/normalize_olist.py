"""OPTIONAL: Normalize downloaded Olist CSVs to our agreed demo schema.

Uses order-level item aggregation and does not invent shipping methods:
service_type='not_provided', as shipping service isn't in Olist.
Delivery SLA here is Olist's *estimated delivery date*, not carrier contract SLA.
"""
import csv
from pathlib import Path
from collections import defaultdict
from etl.generate_demo import write

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['olist_customers_dataset.csv','olist_orders_dataset.csv','olist_order_items_dataset.csv']
REGION_MAP={'SP':'Southeast','RJ':'Southeast','MG':'Southeast','ES':'Southeast',
'RS':'South','SC':'South','PR':'South','BA':'Northeast','PE':'Northeast','CE':'Northeast',
'RN':'Northeast','PB':'Northeast','PI':'Northeast','AL':'Northeast','SE':'Northeast','MA':'Northeast',
'PA':'North','AM':'North','AC':'North','RR':'North','RO':'North','AP':'North','TO':'North',
'DF':'Central-West','GO':'Central-West','MT':'Central-West','MS':'Central-West'}

def parse_date(value):
    return (value or '')[:10]

def normalize(source=ROOT/'data'/'raw_olist', dest=ROOT/'data'/'olist_normalized'):
    source=Path(source);dest=Path(dest)
    absent=[f for f in REQUIRED if not (source/f).is_file()]
    if absent: raise FileNotFoundError('Скачайте Olist CSV в data/raw_olist/: '+', '.join(absent))
    def read(name):
        with (source/name).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
    cust=read(REQUIRED[0]); orig_orders=read(REQUIRED[1]); orig_items=read(REQUIRED[2]);
    customer_rows=[(r['customer_id'],r['customer_state'],REGION_MAP.get(r['customer_state'],'Other')) for r in cust]
    item_rows=[]; freight_by_order=defaultdict(float)
    for r in orig_items:
        oid=r['order_id']; freight_by_order[oid]+=float(r.get('freight_value') or 0)
        item_rows.append((oid,int(r['order_item_id']),r['product_id'],float(r['price']),1))
    order_rows=[]
    for r in orig_orders:
        oid=r['order_id']; status=r['order_status']
        if status not in ('delivered','canceled'):
            # Other Olist statuses aren't equivalent to cancellation; skip to keep KPI comparable.
            continue
        if oid not in freight_by_order or not parse_date(r['order_purchase_timestamp']) or not parse_date(r['order_estimated_delivery_date']):
            continue
        if status=='delivered' and not parse_date(r['order_delivered_customer_date']):
            continue
        if oid not in freight_by_order or not parse_date(r['order_purchase_timestamp']) or not parse_date(r['order_estimated_delivery_date']):
            continue
        if status=='delivered' and not parse_date(r['order_delivered_customer_date']):
            continue
        order_rows.append((oid,r['customer_id'],parse_date(r['order_purchase_timestamp']),
           parse_date(r['order_estimated_delivery_date']),parse_date(r['order_delivered_customer_date']),
           status,'not_provided',round(freight_by_order.get(oid,0),2)))
    selected={r[0] for r in order_rows}
    item_rows=[r for r in item_rows if r[0] in selected]
    write(dest/'customers.csv',['customer_id','state','macro_region'],customer_rows)
    write(dest/'orders.csv',['order_id','customer_id','order_date','promised_date','delivered_date','status','service_type','freight_value'],order_rows)
    write(dest/'order_items.csv',['order_id','line_no','sku','unit_price','quantity'],item_rows)
    return {'orders':len(order_rows),'items':len(item_rows),'customers':len(customer_rows)}

if __name__=='__main__': print(normalize())
