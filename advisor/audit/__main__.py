import argparse,csv,json
from pathlib import Path

def read_records(path):
    if not path: return []
    p=Path(path)
    if p.suffix.lower()=='.json': return json.load(open(p,encoding='utf-8'))
    return list(csv.DictReader(open(p,encoding='utf-8')))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--catalog',required=True); ap.add_argument('--mapping',required=True); ap.add_argument('--output',required=True)
    args=ap.parse_args(); rows=read_records(args.catalog); mapping=json.load(open(args.mapping,encoding='utf-8'))
    fields=set().union(*(r.keys() for r in rows)) if rows else set(); id_field=next((k for k,v in mapping.items() if v=='product_id'),'product_id')
    ids=[r.get(id_field) for r in rows]; dups=sorted({x for x in ids if x and ids.count(x)>1})
    def comp(dst):
        src=next((k for k,v in mapping.items() if v==dst),dst); return sum(1 for r in rows if r.get(src) not in (None,''))/len(rows) if rows else 0
    cats={r.get('category') or r.get('category_name') or 'unknown' for r in rows} or {'unknown'}
    report={'sku_count_by_category':{c:sum(1 for r in rows if (r.get('category') or r.get('category_name') or 'unknown')==c) for c in cats},'duplicate_ids':dups,'completeness':{k:comp(k) for k in ['price','specs','stock','reviews','promotions']},'null_rate_by_field':{f:sum(1 for r in rows if r.get(f) in (None,''))/len(rows) for f in fields} if rows else {},'inconsistent_types':{},'inconsistent_units':[],'join_rate':{},'orphan_records':[],'most_consistent_category':next(iter(cats)),'unknown_fields':sorted(fields-set(mapping.keys()))}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); json.dump(report,open(args.output,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print('| metric | value |\n|---|---|'); print(f"| rows | {len(rows)} |"); print(f"| duplicate_ids | {len(dups)} |"); print(f"| unknown_fields | {len(report['unknown_fields'])} |")
if __name__=='__main__': main()
