import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from etl.generate_demo import generate
from etl.build_warehouse import build
from etl.normalize_olist import parse_date

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name)
        cls.raw=root/'raw';generate(cls.raw,count=300)
        cls.db=root/'dwh.sqlite';cls.exports=root/'exports';cls.stats=build(cls.raw,cls.db,cls.exports)
        cls.con=sqlite3.connect(cls.db)
    @classmethod
    def tearDownClass(cls): cls.con.close();cls.tmp.cleanup()
    def test_counts(self): self.assertEqual(self.stats['orders'],300)
    def test_grain_one_fact_per_order(self):
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM fact_orders').fetchone()[0],self.con.execute('SELECT COUNT(DISTINCT order_id) FROM fact_orders').fetchone()[0])
    def test_foreign_keys(self): self.assertEqual(self.con.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_order_value_formula(self):
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM fact_orders WHERE ABS(order_value-merchandise_value-freight_value)>0.001').fetchone()[0],0)
    def test_cancel_not_in_sla(self):
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM fact_orders WHERE status='canceled' AND is_late IS NOT NULL").fetchone()[0],0)
    def test_delivered_has_sla(self):
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM fact_orders WHERE status='delivered' AND is_late IS NULL").fetchone()[0],0)
    def test_counts_rollup(self):
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM stg_order_items').fetchone()[0],self.stats['items'])
    def test_exported_tables(self):
        for n in ['fact_orders','dim_date','dim_region','dim_service']: self.assertTrue((self.exports/(n+'.csv')).exists())
    def test_analytics_queries(self):
        import re
        txt=(Path(__file__).parents[1]/'sql'/'analytics_sqlite.sql').read_text(encoding='utf-8')
        self.assertEqual(len(re.findall(r'-- Q[1-8]:',txt)),8)
        for query in txt.split(';'):
            if query.strip(): self.con.execute(query)
    def test_missing_customer_rejected(self):
        bad=Path(self.tmp.name)/'bad'
        bad.mkdir(exist_ok=True)
        for f in self.raw.glob('*.csv'): (bad/f.name).write_bytes(f.read_bytes())
        p=bad/'orders.csv';txt=p.read_text(encoding='utf-8');txt=txt.replace('C00001','C99999')
        if txt!=p.read_text(encoding='utf-8'):
            p.write_text(txt,encoding='utf-8')
            with self.assertRaises(ValueError): build(bad,Path(self.tmp.name)/'bad.sqlite',Path(self.tmp.name)/'badout')
    def test_stable_demo(self):
        a=Path(self.tmp.name)/'seedA';b=Path(self.tmp.name)/'seedB'
        generate(a,10);generate(b,10)
        self.assertEqual((a/'orders.csv').read_bytes(),(b/'orders.csv').read_bytes())
    def test_source_date(self): self.assertEqual(parse_date('2018-09-30 12:00:00'),'2018-09-30')

if __name__=='__main__': unittest.main()
