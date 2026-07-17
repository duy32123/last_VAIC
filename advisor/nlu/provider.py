from typing import Protocol
from advisor.domain.models import NLUResult
class NLUProvider(Protocol):
    def parse(self, text:str, previous:NLUResult|None=None)->NLUResult: ...
