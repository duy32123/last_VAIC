import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from advisor.services.advisor import AdvisorService
svc=AdvisorService(); sid='demo'
for msg in ['Tôi cần máy lạnh dưới 20 triệu cho phòng ngủ 18m2, tiết kiệm điện và ít ồn.','Đà Nẵng.']:
    res=svc.handle_message(sid,msg)
    print(res.model_dump_json(indent=2))
