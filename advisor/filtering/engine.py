from advisor.domain.models import RejectionSummary, StockStatus
from advisor.adapters.normalization import normalize_location
class HardFilterEngine:
    def __init__(self,config): self.config=config
    def evaluate(self,products,nlu):
        elig=[]; rejs=[]
        budget=nlu.hard_constraints.get('budget_max'); area=nlu.context.get('room_area_m2'); loc=nlu.context.get('location')
        minb=area*self.config['capacity_rule']['btu_per_m2_min']; maxb=area*self.config['capacity_rule']['btu_per_m2_max']
        for p in products:
            reasons=[]; used={}; sources={}; warnings=[]
            used['price']=p.price; sources['price']=p.field_sources.get('price') or p.source
            if p.price is None or p.price>budget: reasons.append('over_budget_or_missing_price')
            cap=p.specs.get('capacity_btu'); used['capacity_btu']=cap.value if cap else None
            if cap and cap.source: sources['capacity_btu']=cap.source
            if cap is None or cap.value is None or not(minb<=float(cap.value)<=maxb): reasons.append('unsuitable_or_missing_capacity')
            st=next((s for s in p.stock if normalize_location(s.location)==normalize_location(loc)),None)
            used['stock_status']=st.status.value if st else 'unknown'
            if st and st.source: sources['stock']=st.source
            if st is None or st.status!=StockStatus.IN_STOCK: reasons.append('unavailable_at_location')
            for cs in self.config.get('critical_specs',[]):
                if cs not in p.specs or p.specs[cs].value is None: warnings.append(f'missing_critical_spec:{cs}')
            if reasons: rejs.append(RejectionSummary(product_id=p.product_id,reason_codes=sorted(set(reasons)),used_data=used,sources=sources,warnings=warnings))
            else: elig.append(p)
        return elig,rejs
