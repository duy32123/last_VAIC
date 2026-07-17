import time, uuid, logging
from advisor.config.loader import load_category
from advisor.repositories.providers import CatalogRepository
from advisor.nlu.rule_based import RuleBasedVietnameseNLU
from advisor.conversation.session import InMemorySessionRepository, SlotManager
from advisor.filtering.engine import HardFilterEngine
from advisor.ranking.engine import RankingEngine
from advisor.retrieval.inmemory import InMemoryRetriever
from advisor.guardrails.composer import DeterministicResponseComposer
from advisor.domain.models import AdviceResponse
log=logging.getLogger('advisor')
class AdvisorService:
    def __init__(self,sessions=None,catalog=None,nlu=None):
        self.sessions=sessions or InMemorySessionRepository(); self.catalog=catalog or CatalogRepository(); self.nlu=nlu or RuleBasedVietnameseNLU(); self.retriever=InMemoryRetriever(); self.composer=DeterministicResponseComposer()
    def handle_message(self,session_id,text):
        trace_id=str(uuid.uuid4()); t=time.perf_counter(); state=self.sessions.get(session_id); prev=state.nlu
        nlu=self.nlu.parse(text,prev); cfg=load_category(nlu.category or 'air_conditioner'); nlu=SlotManager(cfg).enrich(nlu)
        state.nlu=nlu; state.messages.append({'role':'user','content':'[masked]'}); self.sessions.save(state)
        if nlu.missing_required_slots:
            return AdviceResponse(status='needs_clarification',nlu=nlu,question=nlu.next_question,missing_slots=nlu.missing_required_slots,trace_id=trace_id)
        products=self.catalog.list_products(nlu.category); eligible,rejections=HardFilterEngine(cfg).evaluate(products,nlu); ranked=RankingEngine(cfg).rank(eligible,nlu)
        recs,warnings=self.composer.compose(ranked,rejections); ctx=self.retriever.retrieve(text,nlu.category)
        log.info({'trace_id':trace_id,'session_id':'***','candidate_count':len(products),'eligible_count':len(eligible),'latency_ms':round((time.perf_counter()-t)*1000,2),'rejections':[r.model_dump() for r in rejections]})
        return AdviceResponse(status='recommendations_ready',nlu=nlu,recommendations=recs,retrieved_context=ctx,guardrail_warnings=warnings,rejection_summary=rejections,trace_id=trace_id)
