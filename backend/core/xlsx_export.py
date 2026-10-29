"""Exportação XLSX Office Open XML usando somente a biblioteca padrão.

Sem dependência extra de planilhas; estilos, filtros e congelamento de cabeçalho.
As células de texto são sempre escapadas e não são interpretadas como fórmulas.
"""
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED


def col_label(number):
    result = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xml_text(value):
    return escape(str(value), {'"': '&quot;', "'": '&apos;'})


def worksheet(title, headers, rows, types=None):
    """Planilha com cabeçalho colorido, colunas dimensionadas, filtros e formato monetário."""
    types = types or {}
    widths = [min(48, max(14, len(str(h)) + 4,
                *(min(len(str(row[i])) + 2, 48) for row in rows if i < len(row))))
              for i, h in enumerate(headers)]
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           '<sheetViews><sheetView workbookViewId="0"><pane ySplit="2" topLeftCell="A3" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
           '<sheetFormatPr defaultRowHeight="20"/>', '<cols>']
    out += [f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, 1)]
    out.append('</cols><sheetData>')
    width_end = col_label(len(headers))
    out.append('<row r="1" ht="34" customHeight="1"><c r="A1" t="inlineStr" s="1"><is><t>'
               + xml_text(title) + '</t></is></c></row>')
    out.append('<row r="2" ht="30" customHeight="1">')
    for i, header in enumerate(headers, 1):
        out.append(f'<c r="{col_label(i)}2" s="2" t="inlineStr"><is><t>{xml_text(header)}</t></is></c>')
    out.append('</row>')
    for r, row in enumerate(rows, 3):
        out.append(f'<row r="{r}">')
        for c, value in enumerate(row, 1):
            if value is None:
                continue
            coordinate = f'{col_label(c)}{r}'
            shade = 3 if r % 2 else 4
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                style = 5 if types.get(c - 1) == 'currency' else shade
                out.append(f'<c r="{coordinate}" s="{style}"><v>{value}</v></c>')
            else:
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                out.append(f'<c r="{coordinate}" t="inlineStr" s="{shade}"><is><t>{xml_text(value)}</t></is></c>')
        out.append('</row>')
    last = max(2, len(rows) + 2)
    out.append(f'</sheetData><autoFilter ref="A2:{width_end}{last}"/>')
    out.append(f'<mergeCells count="1"><mergeCell ref="A1:{width_end}1"/></mergeCells>')
    out.append('</worksheet>')
    return ''.join(out)


def make_xlsx(sheets):
    """sheets = [(title, headers, rows, {column_zero_based: 'currency'}), ...]."""
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        sheets_xml = ''.join(
            f'<sheet name="{xml_text(name[:31])}" sheetId="{index}" r:id="rId{index}"/>'
            for index, (name, *_rest) in enumerate(sheets, 1)
        )
        archive.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets) + 1))
            + '</Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
        archive.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            + sheets_xml + '</sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
            + f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            + '</Relationships>')
        archive.writestr('xl/styles.xml', '<?xml version="1.0" encoding="UTF-8"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<numFmts count="1"><numFmt numFmtId="164" formatCode="&quot;R$&quot; #,##0.00"/></numFmts>'
            '<fonts count="3"><font><sz val="11"/><color rgb="FF24374A"/><name val="Aptos"/></font>'
            '<font><b/><sz val="17"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font>'
            '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font></fonts>'
            '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FF14334A"/><bgColor indexed="64"/></patternFill></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FF087F78"/><bgColor indexed="64"/></patternFill></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFF0F6F8"/><bgColor indexed="64"/></patternFill></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="6">'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1"/>'
            '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFill="1" applyFont="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="164" fontId="0" fillId="4" borderId="0" xfId="0" applyNumberFormat="1"/>'
            '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        for index, sheet in enumerate(sheets, 1):
            archive.writestr(f'xl/worksheets/sheet{index}.xml', worksheet(*sheet))
    return output.getvalue()
