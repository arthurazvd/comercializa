"""Testes abrangentes para xlsx_export.py - cobre todas as ramificações (happy/sad paths)."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from core.xlsx_export import (
    col_label,
    xml_text,
    _append_excel_cell,
    _append_excel_row,
    worksheet,
    make_xlsx,
)


class TestColLabel:

    def test_col_label_single_letters(self):
        assert col_label(1) == 'A'
        assert col_label(26) == 'Z'

    def test_col_label_double_letters(self):
        assert col_label(27) == 'AA'
        assert col_label(52) == 'AZ'
        assert col_label(53) == 'BA'
        assert col_label(702) == 'ZZ'

    def test_col_label_triple_letters(self):
        assert col_label(703) == 'AAA'
        assert col_label(18278) == 'ZZZ'


class TestXmlText:

    def test_xml_text_escapes_special_chars(self):
        assert xml_text('A & B') == 'A &amp; B'
        assert xml_text('A < B') == 'A &lt; B'
        assert xml_text('A > B') == 'A &gt; B'
        assert xml_text('"quote"') == '&quot;quote&quot;'
        assert xml_text("'apostrophe'") == '&apos;apostrophe&apos;'

    def test_xml_text_normal_string(self):
        assert xml_text('Texto normal') == 'Texto normal'
        assert xml_text('123') == '123'

    def test_xml_text_empty_string(self):
        assert xml_text('') == ''


class TestAppendExcelCell:

    def test_append_cell_none_value(self):
        out = []
        _append_excel_cell(out, 'A1', None, 1, False)
        assert out == []

    def test_append_cell_integer(self):
        out = []
        _append_excel_cell(out, 'A1', 42, 1, False)
        assert len(out) == 1
        assert '<c r="A1" s="1"><v>42</v></c>' in out[0]

    def test_append_cell_float(self):
        out = []
        _append_excel_cell(out, 'A1', 3.14, 1, False)
        assert '<c r="A1" s="1"><v>3.14</v></c>' in out[0]

    def test_append_cell_decimal(self):
        out = []
        _append_excel_cell(out, 'A1', Decimal('10.50'), 1, False)
        assert '<c r="A1" s="1"><v>10.50</v></c>' in out[0]

    def test_append_cell_boolean(self):
        out = []
        _append_excel_cell(out, 'A1', True, 1, False)
        assert '<c r="A1" t="inlineStr" s="1"><is><t>True</t></is></c>' in out[0]

    def test_append_cell_currency(self):
        out = []
        _append_excel_cell(out, 'A1', Decimal('10.50'), 1, True)
        assert '<c r="A1" s="5"><v>10.50</v></c>' in out[0]

    def test_append_cell_string(self):
        out = []
        _append_excel_cell(out, 'A1', 'Texto', 1, False)
        assert '<c r="A1" t="inlineStr" s="1"><is><t>Texto</t></is></c>' in out[0]

    def test_append_cell_string_escapes_xml(self):
        out = []
        _append_excel_cell(out, 'A1', 'A & B < C', 1, False)
        assert 'A &amp; B &lt; C' in out[0]

    def test_append_cell_date(self):
        out = []
        _append_excel_cell(out, 'A1', date(2024, 1, 15), 1, False)
        assert '<c r="A1" t="inlineStr" s="1"><is><t>2024-01-15</t></is></c>' in out[0]

    def test_append_cell_datetime(self):
        out = []
        _append_excel_cell(out, 'A1', datetime(2024, 1, 15, 10, 30), 1, False)
        assert '2024-01-15T10:30:00' in out[0]


class TestAppendExcelRow:

    def test_append_row_alternating_shades(self):
        out = []
        _append_excel_row(out, ['A', 'B', 'C'], 3, {})
        assert 's="3"' in out[1]

        out = []
        _append_excel_row(out, ['A', 'B', 'C'], 4, {})
        assert 's="4"' in out[1]

    def test_append_row_applies_currency_style(self):
        out = []
        _append_excel_row(out, [Decimal('10'), 'Texto'], 3, {0: 'currency'})
        assert 's="5"' in out[1]
        assert 's="3"' in out[2]


class TestWorksheet:

    def test_worksheet_basic_structure(self):
        headers = ['Col1', 'Col2']
        rows = [['A', 'B'], ['C', 'D']]
        xml = worksheet('Teste', headers, rows)

        assert '<?xml version="1.0"' in xml
        assert '<worksheet xmlns=' in xml
        assert '<sheetViews>' in xml
        assert 'ySplit="2"' in xml
        assert '<sheetFormatPr' in xml
        assert '<cols>' in xml
        assert '<sheetData>' in xml
        assert 'Teste' in xml
        assert 'Col1' in xml
        assert 'Col2' in xml
        assert '<autoFilter' in xml
        assert '<mergeCells' in xml

    def test_worksheet_title_row(self):
        xml = worksheet('Título', ['A'], [['B']])
        assert '<mergeCell ref="A1:A1"/>' in xml
        assert '<row r="1"' in xml
        assert 'Título' in xml

    def test_worksheet_header_row(self):
        xml = worksheet('T', ['A', 'B'], [['C', 'D']])
        assert '<row r="2"' in xml
        assert 's="2"' in xml

    def test_worksheet_data_rows(self):
        xml = worksheet('T', ['A'], [['B'], ['C']])
        assert '<row r="3"' in xml
        assert '<row r="4"' in xml

    def test_worksheet_column_widths(self):
        xml = worksheet(
            'T', ['Curto', 'Muito Longo Cabeçalho'], [['X'], ['Y']])
        assert 'width=' in xml

    def test_worksheet_with_currency_types(self):
        xml = worksheet('T', ['Valor'], [[Decimal('10.50')]], {0: 'currency'})
        assert 's="5"' in xml

    def test_worksheet_empty_rows(self):
        xml = worksheet('T', ['A'], [])
        assert '<row r="3"' not in xml
        assert '<autoFilter ref="A2:A2"/>' in xml


class TestMakeXlsx:

    def test_make_xlsx_single_sheet(self):
        sheets = [('Sheet1', ['A', 'B'], [['1', '2']], {})]
        xlsx_bytes = make_xlsx(sheets)
        assert xlsx_bytes[:4] == b'PK\x03\x04'

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            assert '[Content_Types].xml' in zf.namelist()
            assert '_rels/.rels' in zf.namelist()
            assert 'xl/workbook.xml' in zf.namelist()
            assert 'xl/styles.xml' in zf.namelist()
            assert 'xl/worksheets/sheet1.xml' in zf.namelist()

    def test_make_xlsx_multiple_sheets(self):
        sheets = [
            ('Sheet1', ['A'], [['1']], {}),
            ('Sheet2', ['B'], [['2']], {}),
            ('Sheet3', ['C'], [['3']], {}),
        ]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            assert 'xl/worksheets/sheet1.xml' in zf.namelist()
            assert 'xl/worksheets/sheet2.xml' in zf.namelist()
            assert 'xl/worksheets/sheet3.xml' in zf.namelist()
            workbook = zf.read('xl/workbook.xml').decode('utf-8')
            assert workbook.count('<sheet ') == 3

    def test_make_xlsx_sheet_name_truncated(self):
        long_name = 'A' * 40
        sheets = [(long_name, ['A'], [['1']], {})]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            workbook = zf.read('xl/workbook.xml').decode('utf-8')
            assert 'name="A' in workbook
            assert len([c for c in workbook if c == 'A']) < 40

    def test_make_xlsx_styles_xml(self):
        sheets = [('S', ['A'], [['1']], {})]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            styles = zf.read('xl/styles.xml').decode('utf-8')
            assert 'numFmtId="164"' in styles
            assert 'R$' in styles
            assert 'cellXfs' in styles

    def test_make_xlsx_content_types(self):
        sheets = [('S', ['A'], [['1']], {})]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            content_types = zf.read('[Content_Types].xml').decode('utf-8')
            assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml' in content_types
            assert 'spreadsheetml.styles+xml' in content_types
            assert 'spreadsheetml.worksheet+xml' in content_types

    def test_make_xlsx_relationships(self):
        sheets = [('S', ['A'], [['1']], {})]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            rels = zf.read('xl/_rels/workbook.xml.rels').decode('utf-8')
            assert 'relationships/worksheet' in rels
            assert 'relationships/styles' in rels

    def test_make_xlsx_empty_sheets(self):
        sheets = [('Empty', ['A'], [], {})]
        xlsx_bytes = make_xlsx(sheets)

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            sheet1 = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            assert '<row r="3"' not in sheet1


@pytest.mark.django_db
class TestXlsxExportIntegration:
    """Testes de integração com export_views (precisam de banco)."""

    def test_stock_export_generates_valid_xlsx(self):
        from django.test import Client
        from tests.factories import CategoryFactory, ProductFactory

        client = Client()
        category = CategoryFactory()
        ProductFactory(category=category, stock=10, sku='TEST-001')

        # URL correta: /api/stock-export/ (não /api/stock/export/)
        response = client.get("/api/stock-export/")
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        content = response.content
        assert content[:4] == b'PK\x03\x04'

        with ZipFile(BytesIO(content)) as zf:
            assert 'xl/worksheets/sheet1.xml' in zf.namelist()
            assert 'xl/worksheets/sheet2.xml' in zf.namelist()

    def test_finance_export_generates_valid_xlsx(self):
        from django.test import Client
        from tests.factories import (
            CategoryFactory, ProductFactory, SaleFactory, SaleItemFactory,
        )

        client = Client()
        category = CategoryFactory()
        product = ProductFactory(category=category, stock=10)
        sale = SaleFactory()
        SaleItemFactory(sale=sale, product=product, quantity=5)

        # URL correta: /api/reports/finance/export/
        response = client.get("/api/reports/finance/export/")
        assert response.status_code == 200

        content = response.content
        assert content[:4] == b'PK\x03\x04'

        with ZipFile(BytesIO(content)) as zf:
            sheet_count = sum(
                1 for name in zf.namelist()
                if name.startswith('xl/worksheets/sheet')
            )
            assert sheet_count == 7

    def test_xlsx_escapes_formula_injection(self):
        from core.xlsx_export import xml_text

        assert xml_text('=SUM(1,2)') == '=SUM(1,2)'
        assert xml_text('@SUM(1,2)') == '@SUM(1,2)'
        assert xml_text('+1+2') == '+1+2'


class TestXlsxExportEdgeCases:

    def test_worksheet_with_special_chars_in_data(self):
        rows = [['A & B', 'C < D', 'E > F', '"Quotes"', "'Apostrophe'"]]
        xml = worksheet('Test', ['Col1', 'Col2', 'Col3', 'Col4', 'Col5'], rows)

        assert '&amp;' in xml
        assert '&lt;' in xml
        assert '&gt;' in xml
        assert '&quot;' in xml
        assert '&apos;' in xml

    def test_worksheet_unicode_content(self):
        rows = [['日本語', '中文', '한국어', 'العربية']]
        xml = worksheet('Test', ['Col'], rows)
        assert '日本語' in xml

    def test_make_xlsx_large_dataset(self):
        headers = [f'Col{i}' for i in range(20)]
        rows = [[f'Row{r}Col{c}' for c in range(20)] for r in range(1000)]
        sheets = [('Large', headers, rows, {})]

        xlsx_bytes = make_xlsx(sheets)
        assert len(xlsx_bytes) > 10000

        with ZipFile(BytesIO(xlsx_bytes)) as zf:
            sheet1 = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            assert 'Row999Col19' in sheet1
