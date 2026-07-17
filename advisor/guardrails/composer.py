from advisor.domain.models import RecommendationResult, ProductSummary, FactualClaim
class DeterministicResponseComposer:
    def compose(self,ranked,rejections):
        recs=[]; warnings=[]
        for i,(total,pid,p,bd) in enumerate(ranked[:3],1):
            claims=[]; prov={}
            if p.price is not None and (src:=p.field_sources.get('price')):
                claims.append(FactualClaim(field='price',value=p.price,text=f'Giá hiện tại là {p.price:,} đồng'.replace(',', '.'),source=src)); prov['price']=src
            else: warnings.append(f'{pid}: chưa có dữ liệu giá')
            for key,label in [('noise_db','Độ ồn'),('energy_efficiency','Hiệu suất điện'),('capacity_btu','Công suất')]:
                sv=p.specs.get(key)
                if sv and sv.source:
                    claims.append(FactualClaim(field=f'specs.{key}',value=sv.value,text=f'{label}: {sv.value} {sv.unit or ""}'.strip(),source=sv.source)); prov[key]=sv.source
            st=p.stock[0] if p.stock else None
            if st and st.source:
                claims.append(FactualClaim(field='stock',value=st.status.value,text=f'Tồn kho khu vực: {st.status.value}',source=st.source)); prov['stock']=st.source
            best=max(bd,key=bd.get); worst=min(bd,key=bd.get)
            recs.append(RecommendationResult(rank=i,product_id=pid,product_summary=ProductSummary(name=p.name,brand=p.brand,model=p.model,price=p.price),total_score=total,score_breakdown=bd,matched_reasons=[f'Điểm mạnh nhất theo dữ liệu chuẩn hoá: {best}', 'Đáp ứng ngân sách, diện tích phòng và tồn kho khu vực.'],tradeoffs=[f'Đánh đổi chính: {worst} thấp hơn các tiêu chí còn lại.'],warnings=['Dữ liệu synthetic/mock, cần audit dữ liệu BTC trước production.'],factual_claims=claims,recommendation_confidence=0.85 if len(claims)>=4 else 0.65,provenance=prov))
        return recs,warnings
