from advisor.domain.models import SimpleModel, NLUResult
class SessionState(SimpleModel):
    session_id:str; nlu:NLUResult|None=None; messages:list[dict]=[]
class InMemorySessionRepository:
    def __init__(self): self.sessions={}
    def get(self,sid): return self.sessions.get(sid) or SessionState(session_id=sid)
    def save(self,state): self.sessions[state.session_id]=state
    def delete(self,sid): self.sessions.pop(sid,None)
class SlotManager:
    def __init__(self,config): self.config=config
    def missing(self,nlu):
        out=[]
        for slot in self.config['required_slots']:
            val=nlu.hard_constraints.get(slot) if slot.startswith('budget') else nlu.context.get(slot)
            if val is None: out.append(slot)
        return out
    def question(self,slot): return self.config.get('slot_questions',{}).get(slot, f'Vui lòng cho biết {slot}?')
    def enrich(self,nlu):
        miss=self.missing(nlu); nlu.missing_required_slots=miss; nlu.next_question=self.question(miss[0]) if miss else None; return nlu
