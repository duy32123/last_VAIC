from pathlib import Path
import json
import zipfile
from xml.sax.saxutils import escape
import pytest


from scripts.build_btc_aircon_catalog import build, normalize_row, parse_area, parse_btu, parse_energy, parse_int_price, parse_noise, split_list
from advisor.adapters.btc_aircon import BtcAirconJsonlAdapter, CanonicalBtcAirconError


def make_workbook(path: Path):
    rows = [
        ["SKU","productidweb","model","Thương hiệu","Năm ra mắt","Giá gốc","Giá khuyến mãi","Phạm vi sử dụng","Công suất đầu ra","Inverter","Nhãn năng lượng","Độ ồn","Công nghệ làm lạnh","Tiện ích","Chuẩn chống nước, bụi","Số lượng"],
        ["SKU1","9999","M1","Brand",2025,"10.000.000","8.000.000","Từ 30 - 40m²","12000 BTU","Có Inverter","5 sao (Hiệu suất năng lượng 6.23)","Dàn lạnh: 45/34/29 dB - Dàn nóng: 51 dB","Fast | Fast | Quiet","Wifi | ","PM2.5 | Ion","Khoảng 7000 trang A4"],
        ["SKU1","123","M1B","Brand",2025,9000000,7000000,"Dưới 15m²","9000 BTU","Có","5 sao (Hiệu suất năng lượng 5.1)","Dàn lạnh: 40/30 dB - Dàn nóng: 50 dB","Fast","Wifi","Dust",99],
        ["SKU2","124","M2","Brand",2024,0,None,"bad area","không có số","-","Không","bad noise",None,None,None,10],
    ]
    def col_name(index: int) -> str:
        name = ""
        while index:
            index, rem = divmod(index - 1, 26)
            name = chr(65 + rem) + name
        return name
    sheet_rows = []
    for r_index, row in enumerate(rows, start=1):
        cells = []
        for c_index, value in enumerate(row, start=1):
            if value is None:
                continue
            ref = f"{col_name(c_index)}{r_index}"
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{r_index}">{"".join(cells)}</row>')
    sheet_xml = '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(sheet_rows) + '</sheetData></worksheet>'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        zf.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Máy lạnh" sheetId="1" r:id="rId1"/></sheets></workbook>')
        zf.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)


def test_parsers():
    assert parse_int_price("8.000.000đ") == 8000000
    assert parse_int_price(0) is None
    assert parse_area("Từ 30 - 40m²") == (30.0, 40.0, True)
    assert parse_area("Từ 15 - 20m²") == (15.0, 20.0, True)
    assert parse_area("Dưới 15m²") == (0.0, 15.0, True)
    assert parse_energy("5 sao (Hiệu suất năng lượng 6.23)") == (5, 6.23, True)
    assert parse_noise("Dàn lạnh: 45/34/29 dB - Dàn nóng: 51 dB") == (29.0, 45.0, 51.0, True)
    assert parse_btu("Công suất 12.000 BTU") == 12000
    assert parse_btu("Công suất 12000") is None
    assert split_list("A | B | A | ") == ["A", "B"]


def test_normalize_row_without_openpyxl_dependency():
    row = (
        "SKU3", "9999", "M3", "Brand", "2026", "12.000.000", "11.000.000",
        "Từ 15 - 20m²", "9.000 BTU", "Có",
        "5 sao (Hiệu suất năng lượng 6.23)",
        "Dàn lạnh: 45/34/29 dB - Dàn nóng: 51 dB",
        "Fast | Quiet", "Eco | Eco", "Wifi |", "PM2.5 | Ion", "Auto | Sleep",
        "2 năm", "10 năm", "R32", "Gift | Voucher", "Khoảng 7000 trang A4",
    )
    keys = [
        "sku", "product_web_id", "model_code", "brand", "product_year", "original_price", "promotion_price",
        "area", "capacity", "inverter", "energy", "noise", "cooling_technology",
        "energy_saving_technology", "features", "air_filter_features", "wind_modes",
        "warranty", "compressor_warranty", "gas_type", "promotions",
    ]
    cols = {key: index for index, key in enumerate(keys)}
    rec = normalize_row(row, cols, source_row=2)
    assert rec["product_id"] == "SKU3"
    assert rec["product_web_id"] is None
    assert rec["effective_price"] == 11000000
    assert rec["area_min_m2"] == 15.0 and rec["area_max_m2"] == 20.0
    assert rec["cooling_capacity_btu"] == 9000
    assert rec["energy_stars"] == 5 and rec["cspf"] == 6.23
    assert rec["indoor_noise_min_db"] == 29.0 and rec["indoor_noise_max_db"] == 45.0
    assert rec["stock_status"] == "unknown" and rec["stock_by_location"] == {}
    assert rec["data_quality"]["eligible_for_demo"] is True
    assert "Số lượng" not in rec


def test_build_synthetic_workbook(tmp_path):
    src = tmp_path / "Spec_cate_gia.xlsx"; make_workbook(src)
    allp = tmp_path / "all.jsonl"; elig = tmp_path / "eligible.json"; rep = tmp_path / "report.json"
    report = build(src, allp, elig, rep)
    lines = [json.loads(x) for x in allp.read_text(encoding="utf-8").splitlines()]
    assert report["input_rows"] == 3
    assert report["duplicate_sku_count"] == 1
    first = lines[0]
    assert first["product_id"] == "SKU1"
    assert first["product_web_id"] is None
    assert "placeholder_productidweb" in first["data_quality"]["warnings"]
    assert first["effective_price"] == 8000000
    assert first["stock_status"] == "unknown" and first["stock_by_location"] == {}
    assert "Số lượng" not in first
    assert first["air_filter_features"] == ["PM2.5", "Ion"]
    assert first["data_quality"]["eligible_for_demo"] is True
    assert len(json.loads(elig.read_text(encoding="utf-8"))) == 1


def test_loader_rejects_missing_product_id(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text(json.dumps({"product_id": "", "category": "air_conditioner", "stock_status": "unknown", "stock_by_location": {}, "source": {}, "data_quality": {}}), encoding="utf-8")
    with pytest.raises(CanonicalBtcAirconError):
        BtcAirconJsonlAdapter(p).load_records()
