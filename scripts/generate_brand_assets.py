"""Extrai as variações oficiais do arquivo vetorial fornecido para o Comercializa.

Uso (na raiz do repositório): python scripts/generate_brand_assets.py
Não requer pacotes externos. O SVG original contém várias artes fora do viewBox
principal; cada variante é formada por grupos vetoriais do próprio arquivo.
"""
from __future__ import annotations

import copy
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets' / 'brand' / 'LOGO COMERCIALIZA.svg'
OUTPUT = ROOT / 'frontend' / 'public'

# Índices de elementos, ignorando os comentários XML, conforme a arte-mestre.
# ViewBoxes ajustados ao desenho de cada variante e com respiro na borda.
VARIANTS = {
    'logo-comercializa-vertical.svg': ([1, 2, 3], (290, 182, 420, 636)),
    'logo-comercializa-horizontal-light.svg': ([10], (-2041, -731, 851, 156)),
    'logo-comercializa-horizontal-dark.svg': ([5, 6, 7], (-2041, 422, 851, 156)),
    'favicon-comercializa.svg': ([9], (-876, -915, 597, 525)),
    'favicon-comercializa-dark.svg': ([4], (-876, 237, 597, 525)),
}


def main() -> None:
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    source = ET.parse(SOURCE).getroot()
    assert source[0].tag.endswith('defs'), 'A arte-mestre mudou de estrutura.'
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for filename, (indices, viewbox) in VARIANTS.items():
        svg = ET.Element(source.tag, {'viewBox': ' '.join(str(v) for v in viewbox)})
        svg.append(copy.deepcopy(source[0]))  # Gradientes e estilos da marca.
        for index in indices:
            svg.append(copy.deepcopy(source[index]))
        ET.ElementTree(svg).write(OUTPUT / filename, encoding='utf-8', xml_declaration=True)
        print(f'Gerado: {OUTPUT / filename}')


if __name__ == '__main__':
    main()
