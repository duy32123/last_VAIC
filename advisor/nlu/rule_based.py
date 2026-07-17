import re
from advisor.domain.models import NLUResult
from advisor.adapters.normalization import strip_accents, normalize_price, normalize_area
class RuleBasedVietnameseNLU:
    def parse(self,text,previous=None):
        base=previous.model_copy(deep=True) if previous else NLUResult(category='air_conditioner',parse_confidence=0.3)
        s=strip_accents(text)
        if 'may lanh' in s or 'dieu hoa' in s: base.category='air_conditioner'; base.parse_confidence=max(base.parse_confidence,0.8)
        m=re.search(r'(duoi|toi da|khoang)\s+(\d+(?:[\.,]\d+)?(?:\s*trieu)?|\d[\d\.,]+)',s)
        if m: base.hard_constraints['budget_max']=normalize_price(m.group(2))
        m=re.search(r'(\d+(?:[\.,]\d+)?)\s*m\s*2',s)
        if m: base.context['room_area_m2']=normalize_area(m.group(0))
        if 'phong ngu' in s: base.context['room_type']='bedroom'
        if 'it on' in s or 'chay em' in s or 'em' in s: base.soft_preferences['low_noise']=0.9
        if 'tiet kiem dien' in s: base.soft_preferences['energy_saving']=0.8
        if 'da nang' in s: base.context['location']='Đà Nẵng'
        return base
