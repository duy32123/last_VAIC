from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from advisor.domain.models import ProductNormalized, Source, SpecValue, StockEntry, StockStatus

CANONICAL_REQUIRED_KEYS = {"product_id", "category", "stock_status", "stock_by_location", "source", "data_quality"}


class CanonicalBtcAirconError(ValueError):
    pass


def validate_canonical_aircon_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = CANONICAL_REQUIRED_KEYS - record.keys()
    if missing:
        raise CanonicalBtcAirconError(f"Canonical BTC air-conditioner record missing keys: {sorted(missing)}")
    if not record.get("product_id"):
        raise CanonicalBtcAirconError("Canonical BTC air-conditioner record missing product_id")
    if record.get("stock_status") != "unknown":
        raise CanonicalBtcAirconError("BTC Phase 1 records must keep stock_status='unknown'")
    if record.get("stock_by_location") not in ({}, None):
        raise CanonicalBtcAirconError("BTC Phase 1 records must not synthesize stock_by_location")
    return record


def canonical_aircon_to_product(record: dict[str, Any]) -> ProductNormalized:
    validate_canonical_aircon_record(record)
    specs: dict[str, SpecValue] = {}
    for key, value in record.items():
        if key in {"product_id", "category", "brand", "model_code", "effective_price", "original_price", "source", "data_quality"}:
            continue
        specs[key] = SpecValue(value=value, raw_value=value, source=Source(type="btc_excel", record_id=record["product_id"], field=key))
    return ProductNormalized(
        product_id=record["product_id"],
        category=record.get("category") or "air_conditioner",
        brand=record.get("brand"),
        model=record.get("model_code"),
        name=record["product_id"],
        price=record.get("effective_price"),
        original_price=record.get("original_price"),
        stock=[StockEntry(status=StockStatus.UNKNOWN, source=Source(type="btc_excel", record_id=record["product_id"], field="stock_status"))],
        specs=specs,
        source=Source(type="btc_excel", record_id=record["product_id"]),
        field_sources={"price": Source(type="btc_excel", record_id=record["product_id"], field="effective_price")},
        data_quality=record.get("data_quality") or {},
        raw_record=record,
    )


class BtcAirconJsonlAdapter:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    records.append(validate_canonical_aircon_record(record))
                except json.JSONDecodeError as exc:
                    raise CanonicalBtcAirconError(f"Invalid JSONL at {self.path}:{line_no}: {exc}") from exc
        return records

    def load(self) -> list[ProductNormalized]:
        return [canonical_aircon_to_product(record) for record in self.load_records()]
