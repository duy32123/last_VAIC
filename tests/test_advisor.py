import json, subprocess, sys
from pathlib import Path
import pytest
from advisor.domain.models import ProductNormalized,Source,StockStatus
from advisor.adapters.normalization import normalize_price, normalize_area
from advisor.adapters.mock import MockProductAdapter
from advisor.adapters.json_csv import JsonProductAdapter, DuplicateProductIdError
from advisor.nlu.rule_based import RuleBasedVietnameseNLU
from advisor.config.loader import load_category
from advisor.conversation.session import SlotManager
from advisor.filtering.engine import HardFilterEngine
from advisor.ranking.engine import RankingEngine
from advisor.services.advisor import AdvisorService

def test_schema_null_price_not_zero_and_currency():
    p=ProductNormalized(product_id='x',category='c',name='n',price=None,source=Source(type='t',record_id='x'))
    assert p.price is None
    with pytest.raises(Exception): ProductNormalized(product_id='x',category='c',name='n',currency='USD',source=Source(type='t'))
def test_unknown_stock_not_in_stock():
    nlu=RuleBasedVietnameseNLU().parse('máy lạnh dưới 20 triệu phòng ngủ 18m2 Đà Nẵng')
    cfg=load_category('air_conditioner'); nlu=SlotManager(cfg).enrich(nlu)
    p=MockProductAdapter().load()[0]; p.stock=[]
    elig,rejs=HardFilterEngine(cfg).evaluate([p],nlu)
    assert not elig and 'unavailable_at_location' in rejs[0].reason_codes
def test_unit_normalization():
    assert normalize_price('20 triệu')==20000000
    assert normalize_price('20.000.000')==20000000
    assert normalize_price('20,000,000')==20000000
    assert normalize_area('18 m²')==18
def test_adapter_mapping_and_duplicate(tmp_path):
    data=[{'product_code':'A','category':'air_conditioner','product_name':'A','selling_price':'1 triệu','technical_specs':{}},{'product_code':'A','category':'air_conditioner','product_name':'B','selling_price':'2 triệu','technical_specs':{}}]
    p=tmp_path/'c.json'; p.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(DuplicateProductIdError): JsonProductAdapter(p,'advisor/config/mappings/catalog.yaml').load()
    p.write_text(json.dumps(data[:1]),encoding='utf-8')
    assert JsonProductAdapter(p,'advisor/config/mappings/catalog.yaml').load()[0].price==1000000
def test_nlu_scenario_and_slot_merge():
    nlu=RuleBasedVietnameseNLU(); first=nlu.parse('Tôi cần máy lạnh dưới 20 triệu cho phòng ngủ 18m2, tiết kiệm điện và ít ồn.')
    cfg=load_category('air_conditioner'); first=SlotManager(cfg).enrich(first)
    assert first.hard_constraints['budget_max']==20000000 and first.context['room_area_m2']==18 and first.missing_required_slots==['location']
    second=SlotManager(cfg).enrich(nlu.parse('Đà Nẵng.',first))
    assert second.context['location']=='Đà Nẵng' and second.missing_required_slots==[]
def test_no_rank_until_slots_complete():
    res=AdvisorService().handle_message('s1','Tôi cần máy lạnh dưới 20 triệu cho phòng ngủ 18m2, tiết kiệm điện và ít ồn.')
    assert res.status=='needs_clarification' and not res.recommendations
def test_hard_filter_rejections():
    svc=AdvisorService(); svc.handle_message('s2','máy lạnh dưới 20 triệu phòng ngủ 18m2 tiết kiệm điện ít ồn')
    res=svc.handle_message('s2','Đà Nẵng')
    reasons={r.product_id:r.reason_codes for r in res.rejection_summary}
    assert reasons['AC004']==['over_budget_or_missing_price']
    assert reasons['AC005']==['over_budget_or_missing_price']
    assert 'unavailable_at_location' in reasons['AC006']
    assert 'unsuitable_or_missing_capacity' in reasons['AC007']
def test_deterministic_ranking_and_top3_and_sum():
    svc=AdvisorService(); svc.handle_message('s3','máy lạnh dưới 20 triệu phòng ngủ 18m2 tiết kiệm điện ít ồn')
    res=svc.handle_message('s3','Đà Nẵng')
    assert [r.product_id for r in res.recommendations]==['AC002','AC001','AC003']
    assert len(res.recommendations)==3
    for r in res.recommendations: assert abs(sum(r.score_breakdown.values())-r.total_score)<1e-6
    svc2=AdvisorService(); svc2.handle_message('s4','máy lạnh dưới 20 triệu phòng ngủ 18m2')
    n=svc2.sessions.get('s4').nlu; n.soft_preferences={'cheap_price':2.0}; svc2.sessions.save(svc2.sessions.get('s4'))
    res2=svc2.handle_message('s4','Đà Nẵng')
    assert res2.recommendations[0].product_id=='AC003'
def test_claims_have_sources_and_guardrails_no_fake_promo():
    svc=AdvisorService(); svc.handle_message('s5','máy lạnh dưới 20 triệu phòng ngủ 18m2 tiết kiệm điện ít ồn')
    res=svc.handle_message('s5','Đà Nẵng')
    for rec in res.recommendations:
        assert rec.factual_claims
        assert all(c.source for c in rec.factual_claims)
        assert not any(c.field=='promotion' for c in rec.factual_claims)
def test_audit_missing_fields(tmp_path):
    f=tmp_path/'catalog.csv'; f.write_text('product_code,category,selling_price,odd\nA,air_conditioner,,x\n',encoding='utf-8')
    out=tmp_path/'audit.json'
    cp=subprocess.run([sys.executable,'-m','advisor.audit','--catalog',str(f),'--mapping','advisor/config/mappings/catalog.yaml','--output',str(out)],capture_output=True,text=True)
    assert cp.returncode==0 and out.exists(); assert 'odd' in json.loads(out.read_text(encoding='utf-8'))['unknown_fields']
def test_full_e2e_conversation_latency():
    svc=AdvisorService(); a=svc.handle_message('s6','Tôi cần máy lạnh dưới 20 triệu cho phòng ngủ 18m2, tiết kiệm điện và ít ồn.')
    b=svc.handle_message('s6','Đà Nẵng.')
    assert a.status=='needs_clarification' and a.question=='Anh/chị cần kiểm tra sản phẩm tại khu vực nào?'
    assert b.status=='recommendations_ready' and len(b.recommendations)==3
