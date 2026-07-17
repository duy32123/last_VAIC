import csv,json
from pathlib import Path
from advisor.domain.models import ProductNormalized,Source,SpecValue,StockEntry,StockStatus
from .normalization import normalize_price
class DuplicateProductIdError(ValueError): pass
class MappingAdapterMixin:
    def __init__(self,path,mapping_path): self.path=Path(path); self.mapping=json.load(open(mapping_path,encoding='utf-8'))
    def _mapped(self,row): return {dst:row.get(src) for src,dst in self.mapping.items()}
    def _to_product(self,row):
        m=self._mapped(row); pid=m.get('product_id'); errs=[]
        try: price=normalize_price(m.get('price'))
        except Exception as e: price=None; errs.append(str(e))
        specs={}
        raw_specs=m.get('specs') or {}
        if isinstance(raw_specs,str):
            try: raw_specs=json.loads(raw_specs)
            except Exception: raw_specs={}
        for k,v in raw_specs.items(): specs[k]=SpecValue(value=v, raw_value=v, source=Source(type='input_file',record_id=pid,field=f'specs.{k}'))
        stock=[]; raw_stock=m.get('stock') or []
        if isinstance(raw_stock,str):
            try: raw_stock=json.loads(raw_stock)
            except Exception: raw_stock=[]
        for s in raw_stock:
            stock.append(StockEntry(location=s.get('location'), status=StockStatus(s.get('status','unknown')), source=Source(type='input_file',record_id=pid,field='stock')))
        return ProductNormalized(product_id=pid,category=m.get('category') or 'unknown',brand=m.get('brand'),model=m.get('model'),name=m.get('name') or pid,price=price,original_price=normalize_price(m.get('original_price')) if m.get('original_price') else None,stock=stock,specs=specs,source=Source(type='input_file',record_id=pid),field_sources={'price':Source(type='input_file',record_id=pid,field='price')},data_quality={'normalization_errors':errs},raw_record=row)
    def _dedupe(self,products):
        seen=set()
        for p in products:
            if p.product_id in seen: raise DuplicateProductIdError(p.product_id)
            seen.add(p.product_id)
        return products
class JsonProductAdapter(MappingAdapterMixin):
    def load(self): return self._dedupe([self._to_product(r) for r in json.load(open(self.path,encoding='utf-8'))])
class CsvProductAdapter(MappingAdapterMixin):
    def load(self): return self._dedupe([self._to_product(r) for r in csv.DictReader(open(self.path,encoding='utf-8'))])
