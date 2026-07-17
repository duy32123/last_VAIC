from typing import Protocol
class Retriever(Protocol):
    def retrieve(self,query:str,category:str,limit:int=4)->list[dict]: ...
class InMemoryRetriever:
    docs=[
      {'document_id':'POLICY_WARRANTY','content':'Mock policy: sản phẩm máy lạnh có thông tin bảo hành theo phiếu của nhà sản xuất trong dữ liệu demo.','source':{'type':'mock_policy','record_id':'POLICY_WARRANTY'},'tags':['bảo hành','warranty']},
      {'document_id':'FAQ_INSTALL','content':'Mock FAQ: chi phí lắp đặt phụ thuộc vị trí và vật tư phát sinh; cần xác nhận lại khi có dữ liệu thật.','source':{'type':'mock_faq','record_id':'FAQ_INSTALL'},'tags':['lắp đặt']},
      {'document_id':'FAQ_INSTALLMENT','content':'Mock FAQ: trả góp là tuỳ chọn, chưa có dữ liệu khuyến mãi/trả góp thật.','source':{'type':'mock_faq','record_id':'FAQ_INSTALLMENT'},'tags':['trả góp']},
      {'document_id':'POLICY_DELIVERY','content':'Mock policy: giao hàng theo tồn kho khu vực trong dữ liệu demo.','source':{'type':'mock_policy','record_id':'POLICY_DELIVERY'},'tags':['giao hàng']},]
    def retrieve(self,query,category,limit=4):
        return [dict(d, retrieval_score=1.0/(i+1)) for i,d in enumerate(self.docs[:limit])]
