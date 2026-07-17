#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

MISSING_STRINGS = {"", "-", "null", "đang cập nhật", "hãng không công bố"}
SHEET_NAME = "Máy lạnh"
CATEGORY = "air_conditioner"

ALIASES = {
    "sku": ["sku"], "product_web_id": ["productidweb", "product id web"],
    "model_code": ["model", "model_code", "mã model", "mã sản phẩm"], "brand": ["thương hiệu", "hãng", "brand"],
    "product_year": ["năm ra mắt", "năm sản xuất", "product_year"], "original_price": ["giá gốc"],
    "promotion_price": ["giá khuyến mãi", "giá khuyến mại"], "area": ["phạm vi sử dụng"],
    "capacity": ["công suất đầu ra", "công suất làm lạnh"], "inverter": ["inverter", "công nghệ inverter"],
    "energy": ["nhãn năng lượng", "nhãn năng lượng tiết kiệm điện"], "noise": ["độ ồn", "độ ồn trung bình"],
    "type": ["loại máy", "kiểu máy"], "cooling_technology": ["công nghệ làm lạnh"],
    "energy_saving_technology": ["công nghệ tiết kiệm điện"], "features": ["tiện ích", "tính năng"],
    "air_filter_features": ["chuẩn chống nước, bụi", "lọc bụi", "kháng khuẩn khử mùi"],
    "wind_modes": ["chế độ gió"], "warranty": ["bảo hành", "thời gian bảo hành"],
    "compressor_warranty": ["bảo hành máy nén"], "gas_type": ["loại gas", "gas"],
    "promotions": ["khuyến mãi", "ưu đãi"],
}


def norm_header(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "").strip().lower())

def clean_str(v: Any) -> str | None:
    if v is None: return None
    if isinstance(v, float) and v.is_integer(): v = int(v)
    s = str(v).strip()
    return None if norm_header(s) in MISSING_STRINGS else s

def parse_int_price(v: Any) -> int | None:
    s = clean_str(v)
    if not s: return None
    if isinstance(v, (int, float)):
        n = int(v)
    else:
        m = re.sub(r"[^0-9-]", "", s)
        if not m or m == "-": return None
        n = int(m)
    return n if n > 0 else None

def parse_year(v: Any) -> int | None:
    s = clean_str(v)
    if not s: return None
    m = re.search(r"(20\d{2})", s)
    return int(m.group(1)) if m else None

def parse_area(v: Any) -> tuple[float | None, float | None, bool]:
    s = clean_str(v)
    if not s: return None, None, False
    low = s.lower().replace(",", ".")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", low)]
    if "dưới" in low and nums: return 0.0, nums[0], True
    if len(nums) >= 2: return nums[0], nums[1], True
    return None, None, False

def parse_energy(v: Any) -> tuple[int | None, float | None, bool]:
    s = clean_str(v)
    if not s or norm_header(s) == "không": return None, None, False
    star = re.search(r"(\d+)\s*sao", s, re.I)
    perf = re.search(r"(?:hiệu suất năng lượng|cspf)[^0-9]*(\d+(?:[\.,]\d+)?)", s, re.I)
    return (int(star.group(1)) if star else None, float(perf.group(1).replace(",", ".")) if perf else None, bool(star or perf))

def parse_noise(v: Any) -> tuple[float | None, float | None, float | None, bool]:
    s = clean_str(v)
    if not s: return None, None, None, False
    low = s.lower().replace(",", ".")
    indoor = re.search(r"dàn lạnh\s*:\s*([^\-]+)", low)
    outdoor = re.search(r"dàn nóng\s*:\s*([^\-]+)", low)
    indoor_nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", indoor.group(1) if indoor else "")]
    outdoor_nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", outdoor.group(1) if outdoor else "")]
    return (min(indoor_nums) if indoor_nums else None, max(indoor_nums) if indoor_nums else None, outdoor_nums[0] if outdoor_nums else None, bool(indoor_nums or outdoor_nums))

def parse_btu(v: Any) -> int | None:
    s = clean_str(v)
    if not s or not re.search(r"btu", s, re.I): return None
    m = re.search(r"(\d[\d\.,]*)\s*btu", s, re.I)
    return int(re.sub(r"[^0-9]", "", m.group(1))) if m else None

def parse_bool_inverter(v: Any) -> bool | None:
    s = clean_str(v)
    if not s: return None
    low = s.lower()
    if "inverter" in low or low in {"có", "yes", "true", "1"}: return True
    if low in {"không", "no", "false", "0"}: return False
    return None

def split_list(v: Any) -> list[str]:
    s = clean_str(v)
    if not s: return []
    seen, out = set(), []
    for item in (x.strip() for x in s.split("|")):
        if item and item not in seen: seen.add(item); out.append(item)
    return out

def find_col(headers: dict[str, int], key: str) -> int | None:
    for alias in ALIASES[key]:
        if norm_header(alias) in headers: return headers[norm_header(alias)]
    return None

def cell(row: tuple[Any, ...], cols: dict[str, int | None], key: str) -> Any:
    idx = cols.get(key)
    return row[idx] if idx is not None and idx < len(row) else None

def normalize_row(row: tuple[Any, ...], cols: dict[str, int | None], source_row: int) -> dict[str, Any]:
    warnings: list[str] = []
    sku = clean_str(cell(row, cols, "sku"))
    web = clean_str(cell(row, cols, "product_web_id"))
    if web == "9999": web = None; warnings.append("placeholder_productidweb")
    original = parse_int_price(cell(row, cols, "original_price")); promo = parse_int_price(cell(row, cols, "promotion_price"))
    if promo and original and promo > original: warnings.append("promotion_price_gt_original_price")
    area_min, area_max, area_ok = parse_area(cell(row, cols, "area"))
    if clean_str(cell(row, cols, "area")) and not area_ok: warnings.append("area_parse_failed")
    stars, cspf, energy_ok = parse_energy(cell(row, cols, "energy"))
    if clean_str(cell(row, cols, "energy")) and not energy_ok: warnings.append("energy_parse_failed")
    nmin, nmax, nout, noise_ok = parse_noise(cell(row, cols, "noise"))
    if clean_str(cell(row, cols, "noise")) and not noise_ok: warnings.append("noise_parse_failed")
    rec = {
        "product_id": sku, "product_web_id": web, "model_code": clean_str(cell(row, cols, "model_code")), "category": CATEGORY,
        "brand": clean_str(cell(row, cols, "brand")), "product_year": parse_year(cell(row, cols, "product_year")),
        "original_price": original, "promotion_price": promo, "effective_price": promo or original,
        "area_min_m2": area_min, "area_max_m2": area_max, "cooling_capacity_btu": parse_btu(cell(row, cols, "capacity")),
        "inverter": parse_bool_inverter(cell(row, cols, "inverter")), "energy_stars": stars, "cspf": cspf,
        "indoor_noise_min_db": nmin, "indoor_noise_max_db": nmax, "outdoor_noise_db": nout,
        "air_conditioner_type": clean_str(cell(row, cols, "type")),
        "cooling_technology": split_list(cell(row, cols, "cooling_technology")), "energy_saving_technology": split_list(cell(row, cols, "energy_saving_technology")),
        "features": split_list(cell(row, cols, "features")), "air_filter_features": split_list(cell(row, cols, "air_filter_features")), "wind_modes": split_list(cell(row, cols, "wind_modes")),
        "warranty": clean_str(cell(row, cols, "warranty")), "compressor_warranty": clean_str(cell(row, cols, "compressor_warranty")), "gas_type": clean_str(cell(row, cols, "gas_type")),
        "promotions": split_list(cell(row, cols, "promotions")), "stock_status": "unknown", "stock_by_location": {},
        "source": {"type": "btc_excel", "sheet": SHEET_NAME, "source_row": source_row, "sku": sku},
        "data_quality": {"eligible_for_demo": False, "missing_fields": [], "warnings": warnings},
    }
    required = ["product_id","product_year","effective_price","area_min_m2","area_max_m2","inverter","energy_stars","cspf","indoor_noise_min_db","indoor_noise_max_db"]
    missing = [f for f in required if rec.get(f) is None or rec.get(f) == ""]
    if not (rec["features"] or rec["cooling_technology"] or rec["energy_saving_technology"]): missing.append("features_or_technology")
    rec["data_quality"]["missing_fields"] = missing
    rec["data_quality"]["eligible_for_demo"] = bool(sku and rec["product_year"] and rec["product_year"] >= 2025 and rec["effective_price"] and area_ok and rec["inverter"] is not None and stars is not None and cspf is not None and nmin is not None and nmax is not None and not ("features_or_technology" in missing))
    return rec

def load_workbook_rows(path: Path) -> tuple[list[str], Iterable[tuple[int, tuple[Any, ...]]]]:
    try: from openpyxl import load_workbook
    except ImportError as e: raise SystemExit("Missing dependency openpyxl. Install requirements.txt before running BTC catalog build.") from e
    wb = load_workbook(path, read_only=True, data_only=True)
    if SHEET_NAME not in wb.sheetnames: raise SystemExit(f'Missing required sheet "{SHEET_NAME}" in {path}')
    ws = wb[SHEET_NAME]
    rows = ws.iter_rows(values_only=True)
    headers = [str(x or "") for x in next(rows)]
    return headers, ((i, r) for i, r in enumerate(rows, start=2))

def build(input_path: Path, all_path: Path, eligible_path: Path, report_path: Path) -> dict[str, Any]:
    if not input_path.exists(): raise SystemExit(f"BTC input workbook not found: {input_path}. Place Spec_cate_gia.xlsx at this path; no synthetic BTC data was created.")
    headers, rows = load_workbook_rows(input_path)
    hmap = {norm_header(h): i for i, h in enumerate(headers)}; cols = {k: find_col(hmap, k) for k in ALIASES}
    if cols["sku"] is None: raise SystemExit(f'Required column "SKU" not found in sheet "{SHEET_NAME}"')
    records = [normalize_row(r, cols, i) for i, r in rows]
    seen, deduped, dupes = set(), [], 0
    for rec in records:
        pid = rec["product_id"]
        if pid in seen: dupes += 1; rec["data_quality"]["warnings"].append("duplicate_sku_skipped"); continue
        seen.add(pid); deduped.append(rec)
    all_path.parent.mkdir(parents=True, exist_ok=True); eligible_path.parent.mkdir(parents=True, exist_ok=True); report_path.parent.mkdir(parents=True, exist_ok=True)
    with all_path.open("w", encoding="utf-8") as f:
        for rec in deduped: f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    eligible = [r for r in deduped if r["data_quality"]["eligible_for_demo"]]
    eligible_path.write_text(json.dumps(eligible, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    warn_counts = Counter(w for r in deduped for w in r["data_quality"]["warnings"])
    prices = sorted(r["effective_price"] for r in deduped if r["effective_price"])
    canonical_fields = [k for k in deduped[0] if k not in {"source","data_quality"}] if deduped else []
    report = {"input_rows": len(records), "valid_sku_count": sum(1 for r in deduped if r["product_id"]), "unique_sku_count": len({r["product_id"] for r in deduped if r["product_id"]}), "duplicate_sku_count": dupes, "products_with_effective_price": len(prices), "products_by_year": dict(sorted(Counter(str(r["product_year"]) for r in deduped if r["product_year"]).items())), "completeness": {f: sum(1 for r in deduped if r.get(f) not in (None, "", [])) for f in canonical_fields}, "eligible_count": len(eligible), "parse_errors_by_type": {k:v for k,v in warn_counts.items() if k.endswith("_parse_failed")}, "promotion_price_gt_original_price_count": warn_counts["promotion_price_gt_original_price"], "placeholder_productidweb_count": warn_counts["placeholder_productidweb"], "price_distribution": {"min": prices[0] if prices else None, "median": statistics.median(prices) if prices else None, "max": prices[-1] if prices else None}, "warnings_by_type": dict(sorted(warn_counts.items()))}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return report

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--input", required=True); p.add_argument("--output", required=True); p.add_argument("--eligible-output", required=True); p.add_argument("--report", required=True)
    a = p.parse_args(argv); report = build(Path(a.input), Path(a.output), Path(a.eligible_output), Path(a.report))
    print(json.dumps({"input_rows": report["input_rows"], "eligible_count": report["eligible_count"]}, ensure_ascii=False))
    return 0
if __name__ == "__main__": raise SystemExit(main())
