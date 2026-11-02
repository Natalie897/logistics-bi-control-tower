"""Deterministic synthetic logistics data. All identifiers and records are fictional."""
from pathlib import Path
import csv
import random
from datetime import datetime, timedelta, date

ROOT = Path(__file__).resolve().parents[1]
REGIONS = [('SP','Southeast',0.85),('RJ','Southeast',1.02),('MG','Southeast',1.05),('RS','South',1.10),('PR','South',0.96),('BA','Northeast',1.28),('PE','Northeast',1.35),('CE','Northeast',1.40),('PA','North',1.51),('DF','Central-West',1.07)]
TYPES = [('economy',8,0.65),('standard',5,1.0),('express',2,1.6)]

def write(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

def generate(output_dir=ROOT/'data'/'demo', count=3600, seed=20261102):
    rng=random.Random(seed)
    output_dir=Path(output_dir)
    customers=[]
    for n in range(1,701):
        state,area,mult=rng.choices(REGIONS,weights=[23,10,13,10,12,7,8,5,5,7])[0]
        customers.append((f'C{n:05}', state,area))
    customer_map={c[0]:(c[1],c[2]) for c in customers}
    orders=[];items=[]
    base=date(2025,1,1)
    for n in range(1,count+1):
        oid=f'O{n:06}'
        cid=rng.choice(customers)[0]
        state,_=customer_map[cid]
        delay_mult=next(i[2] for i in REGIONS if i[0]==state)
        service,target,costmult=rng.choices(TYPES,weights=[2,6,2])[0]
        order_date=base+timedelta(days=rng.randrange(365))
        promised_date=order_date+timedelta(days=target)
        cancellation=rng.random()<0.045
        if cancellation:
            status='canceled'; delivered_date=''
        else:
            status='delivered'
            drift=rng.choices([-2,-1,0,1,2,3,5,8],weights=[3,7,27,21,17,12,9,4])[0]
            drift+=round((delay_mult-1)*4)
            actual=max(1,target+drift)
            delivered_date=(order_date+timedelta(days=actual)).isoformat()
        n_items=rng.choices([1,2,3,4],weights=[60,26,10,4])[0]
        freight=round((7.0+costmult*5.2+n_items*1.7)*delay_mult,2)
        orders.append((oid,cid,order_date.isoformat(),promised_date.isoformat(),delivered_date,status,service,freight))
        for line_no in range(1,n_items+1):
            price=round(rng.uniform(16,185)+(30 if service=='express' else 0),2)
            items.append((oid,line_no,f'SKU{rng.randint(1,90):03}',price,1))
    write(output_dir/'customers.csv',['customer_id','state','macro_region'],customers)
    write(output_dir/'orders.csv',['order_id','customer_id','order_date','promised_date','delivered_date','status','service_type','freight_value'],orders)
    write(output_dir/'order_items.csv',['order_id','line_no','sku','unit_price','quantity'],items)
    return {'orders':len(orders),'items':len(items),'customers':len(customers)}

if __name__=='__main__':
    print('SYNTHETIC DEMO:',generate())
