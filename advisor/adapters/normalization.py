import re, unicodedata

def strip_accents(s:str)->str:
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower().replace('đ','d').replace('Đ','d')) if unicodedata.category(c)!='Mn')
def normalize_price(value):
    if value is None or value=='': return None
    if isinstance(value,(int,float)): return int(value)
    s=str(value).lower().strip().replace('đ','').replace('vnd','')
    mult=1000000 if 'triệu' in s or 'trieu' in strip_accents(s) else 1
    nums=re.findall(r'\d+(?:[\.,]\d+)*',s)
    if not nums: raise ValueError(f'Cannot normalize price: {value}')
    n=nums[0]
    if mult>1 and (',' in n or '.' in n) and len(n.split('.')[-1])<=2: return int(float(n.replace(',','.'))*mult)
    return int(re.sub(r'[\.,]','',n))*mult
def normalize_area(value):
    if value is None or value=='': return None
    if isinstance(value,(int,float)): return float(value)
    m=re.search(r'\d+(?:[\.,]\d+)?',str(value).lower().replace('m²','m2'))
    if not m: raise ValueError(f'Cannot normalize area: {value}')
    return float(m.group(0).replace(',','.'))
def normalize_location(s):
    return strip_accents(s or '').replace(' ','_')
