from advisor.domain.models import Source

def get_path(obj,path):
    cur=obj
    for part in path.split('.'):
        cur = getattr(cur,part) if not isinstance(cur,dict) else cur.get(part)
        if cur is None: return None
    return cur
class RankingEngine:
    def __init__(self,config): self.config=config
    def weights(self,prefs):
        weights={k:v['weight'] for k,v in self.config['ranking_features'].items()}
        if prefs.get('low_noise'): weights['noise']*=1+prefs['low_noise']
        if prefs.get('energy_saving'): weights['energy_efficiency']*=1+prefs['energy_saving']
        if prefs.get('cheap_price'): weights['price']*=1+prefs['cheap_price']
        total=sum(weights.values()); return {k:v/total for k,v in weights.items()}
    def normalize(self,value,cfg):
        if value is None: return cfg.get('missing_penalty',0.0)
        mn,mx=cfg['min'],cfg['max']; score=(float(value)-mn)/(mx-mn); score=max(0,min(1,score))
        return 1-score if cfg['direction']=='lower_is_better' else score
    def rank(self,products,nlu):
        w=self.weights(nlu.soft_preferences); rows=[]
        for p in products:
            bd={}; total=0
            for name,cfg in self.config['ranking_features'].items():
                val=get_path(p,cfg['path']); sc=self.normalize(val,cfg); bd[name]=round(sc*w[name],6); total+=bd[name]
            rows.append((round(total,6),p.product_id,p,bd))
        rows.sort(key=lambda x:(-x[0],x[1])); return rows
