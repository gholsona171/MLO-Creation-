"""Archetype bounds for the gates: Rockstar's (survey/arch_ytyp.json, find_arch_ytyp.ps1) plus our own custom archetypes', from the
build's layout (custom_props: seals, flags, statue, ballot booth, chandelier, mirror). load() -> {name (lower): {'bbMin', 'bbMax'}}."""
import json
from pathlib import Path
P3 = Path(__file__).resolve().parent
def load():
    A = json.load(open(P3 / 'survey/arch_ytyp.json', encoding='utf-8-sig'))
    for k, b in json.load(open(P3 / 'out/jc3_layout.json')).get('custom_props', {}).items():
        A[k] = {'bbMin': ' '.join(f'{c}:{x}' for c, x in zip('xyz', b['bb_lo'])), 'bbMax': ' '.join(f'{c}:{x}' for c, x in zip('xyz', b['bb_hi']))}
    return {k.lower(): v for k, v in A.items()}
