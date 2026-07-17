from typing import Protocol, Iterable, Any
from advisor.domain.models import ProductNormalized
class BaseProductAdapter(Protocol):
    def load(self)->list[ProductNormalized]: ...
