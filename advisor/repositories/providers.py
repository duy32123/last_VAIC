from advisor.adapters.mock import MockProductAdapter
class CatalogRepository:
    def __init__(self, adapter=None): self.adapter=adapter or MockProductAdapter()
    def list_products(self, category): return [p for p in self.adapter.load() if p.category==category]
