from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Literal
import copy, json
class SimpleModel:
    def __init__(self, **kwargs):
        anns={}
        for c in reversed(self.__class__.mro()): anns.update(getattr(c,'__annotations__',{}))
        for k,v in self.__class__.__dict__.items():
            if k in anns: setattr(self,k,copy.deepcopy(v))
        for k in anns:
            if k in kwargs: setattr(self,k,kwargs[k])
            elif not hasattr(self,k): setattr(self,k,None)
    def model_copy(self, deep=False): return copy.deepcopy(self) if deep else copy.copy(self)
    def _dump(self,v):
        if isinstance(v,SimpleModel): return v.model_dump()
        if isinstance(v,list): return [self._dump(x) for x in v]
        if isinstance(v,dict): return {k:self._dump(x) for k,x in v.items()}
        if isinstance(v,Enum): return v.value
        if hasattr(v,'isoformat'): return v.isoformat()
        return v
    def model_dump(self): return {k:self._dump(v) for k,v in self.__dict__.items()}
    def model_dump_json(self, indent=None): return json.dumps(self.model_dump(),ensure_ascii=False,indent=indent)
class StockStatus(str, Enum):
    UNKNOWN='unknown'; IN_STOCK='in_stock'; OUT_OF_STOCK='out_of_stock'
class Source(SimpleModel):
    type: str; record_id: str|None=None; field: str|None=None; retrieved_at: datetime|None=None
class SpecValue(SimpleModel):
    value: Any=None; raw_value: Any=None; unit: str|None=None; source: Source|None=None
class StockEntry(SimpleModel):
    location: str|None=None; status: StockStatus=StockStatus.UNKNOWN; quantity: int|None=None; source: Source|None=None
class Promotion(SimpleModel):
    promotion_id: str; description: str; source: Source
class Review(SimpleModel):
    rating: float|None=None; snippet: str|None=None; source: Source|None=None
class ProductNormalized(SimpleModel):
    product_id: str; category: str; brand: str|None=None; model: str|None=None; name: str
    price: int|None=None; original_price: int|None=None; currency: str='VND'
    stock: list[StockEntry]=[]; promotions: list[Promotion]|None=None
    specs: dict[str, SpecValue]={}; description: str|None=None; reviews: list[Review]=[]
    source: Source; field_sources: dict[str, Source]={}; data_quality: dict[str, Any]={}
    raw_record: dict[str, Any]|None=None; retrieved_at: datetime|None=None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.currency!='VND': raise ValueError('Only VND is supported in MVP')
        for f in ('brand','model','description'):
            if getattr(self,f,None)=='': setattr(self,f,None)
class NLUResult(SimpleModel):
    category: str|None='air_conditioner'; hard_constraints: dict[str, Any]={}
    soft_preferences: dict[str, float]={}; context: dict[str, Any]={}
    missing_required_slots: list[str]=[]; next_question: str|None=None; parse_confidence: float=0.0
class FactualClaim(SimpleModel):
    field: str; value: Any=None; text: str; source: Source
class ProductSummary(SimpleModel):
    name: str; brand: str|None=None; model: str|None=None; price: int|None=None
class RecommendationResult(SimpleModel):
    rank:int; product_id:str; product_summary:ProductSummary; total_score:float; score_breakdown:dict[str, float]
    matched_reasons:list[str]; tradeoffs:list[str]; warnings:list[str]=[]
    factual_claims:list[FactualClaim]; recommendation_confidence:float; provenance:dict[str, Source]={}
class RejectionSummary(SimpleModel):
    product_id:str; reason_codes:list[str]; used_data:dict[str, Any]={}; sources:dict[str, Source]={}; warnings:list[str]=[]
class AdviceResponse(SimpleModel):
    status: Literal['needs_clarification','recommendations_ready']; nlu: NLUResult; question: str|None=None; missing_slots:list[str]=[]
    recommendations:list[RecommendationResult]=[]; retrieved_context:list[dict[str,Any]]=[]
    guardrail_warnings:list[str]=[]; rejection_summary:list[RejectionSummary]=[]; trace_id:str|None=None
