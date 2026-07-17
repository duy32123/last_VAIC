try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except Exception:  # pragma: no cover - lets core run in dependency-limited sandboxes
    class FastAPI:
        def __init__(self,*a,**k): self.routes=[]
        def get(self,*a,**k): return lambda f:f
        def post(self,*a,**k): return lambda f:f
        def delete(self,*a,**k): return lambda f:f
    class BaseModel:
        def __init__(self, **kwargs):
            for k,v in kwargs.items(): setattr(self,k,v)
from advisor.services.advisor import AdvisorService
app=FastAPI(title='Data-agnostic Product Advisor MVP')
service=AdvisorService()
class MessageIn(BaseModel):
    message:str
@app.get('/health')
def health(): return {'status':'ok','mock_data':True}
@app.post('/v1/conversations/{session_id}/messages')
def post_message(session_id:str,body:MessageIn): return service.handle_message(session_id,body.message)
@app.get('/v1/conversations/{session_id}')
def get_session(session_id:str): return service.sessions.get(session_id)
@app.delete('/v1/conversations/{session_id}')
def delete_session(session_id:str): service.sessions.delete(session_id); return {'deleted':True}
