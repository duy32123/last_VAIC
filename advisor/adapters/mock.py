from datetime import datetime, timezone
from advisor.domain.models import ProductNormalized, Source, StockEntry, StockStatus, SpecValue, Review, Promotion
NOW=datetime(2026,7,17,tzinfo=timezone.utc)
def src(pid, field, typ='mock_catalog'): return Source(type=typ, record_id=pid, field=field, retrieved_at=NOW)
def spec(pid,k,v,raw=None,unit=None): return SpecValue(value=v, raw_value=raw if raw is not None else v, unit=unit, source=src(pid,f'specs.{k}'))
class MockProductAdapter:
    def load(self):
        rows=[
('AC001','CoolAir','Silent 9000','CoolAir Silent 9000',15990000,9000,21,5.1,4.4,'in_stock','Êm nhất trong nhóm đủ điều kiện'),
('AC002','EcoWind','Saver 9500','EcoWind Saver 9500',16990000,9500,28,6.2,4.6,'in_stock','Tiết kiệm điện nhất'),
('AC003','ValueCool','Basic 10000','ValueCool Basic 10000',12990000,10000,34,4.6,4.1,'in_stock','Giá tốt nhất'),
('AC004','Premium','Pro 12000','Premium Pro 12000',21990000,12000,24,5.8,4.8,'in_stock','Vượt ngân sách'),
('AC005','Luxury','Ultra 10000','Luxury Ultra 10000',25990000,10000,20,6.0,4.9,'in_stock','Vượt ngân sách'),
('AC006','Stockless','DN 9000','Stockless DN 9000',14990000,9000,25,5.5,4.2,'out_of_stock','Hết hàng Đà Nẵng'),
('AC007','Missing','Spec 9000','Missing Spec 9000',13990000,None,23,5.2,4.0,'in_stock','Thiếu công suất'),
('AC008','BigRoom','Large 18000','BigRoom Large 18000',18990000,18000,30,5.0,4.3,'in_stock','Sai công suất cho 18m2'),]
        ps=[]
        for pid,brand,model,name,price,cap,noise,eff,rev,st,desc in rows:
            specs={'noise_db':spec(pid,'noise_db',noise,unit='dB'),'energy_efficiency':spec(pid,'energy_efficiency',eff,unit='CSPF'),'review_score':spec(pid,'review_score',rev,unit='stars')}
            if cap is not None: specs['capacity_btu']=spec(pid,'capacity_btu',cap,unit='BTU')
            p=ProductNormalized(product_id=pid,category='air_conditioner',brand=brand,model=model,name=name,price=price,currency='VND',stock=[StockEntry(location='Đà Nẵng',status=StockStatus(st),source=src(pid,'stock','mock_stock'))],promotions=None,specs=specs,description=desc,reviews=[Review(rating=rev,snippet=desc,source=src(pid,'reviews','mock_review'))],source=src(pid,'record'),field_sources={'price':src(pid,'price','mock_price')},data_quality={'synthetic':True},raw_record={'synthetic_mock':True},retrieved_at=NOW)
            ps.append(p)
        return ps
