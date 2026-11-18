from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


GRID_BLOCKS = 30
BUILDING_PREFIXES = ('CASA-', 'COM-')
ROAD_PREFIX = 'RUA-'
PLAZA_PREFIX = 'PRACA-'
CODE_RE = re.compile(r'^(RUA|CASA|COM|PRACA)-\d+$')


@dataclass(frozen=True)
class CityLocationMeta:
    code: str
    default_name: str
    kind: str  # 'RUA' | 'CASA' | 'COM' | 'PRACA'
    grid_x: int = 0
    grid_y: int = 0

    @property
    def is_building(self) -> bool:
        return self.kind in ('CASA', 'COM')


def infer_location_kind(code: str) -> str:
    upper = code.strip().upper()
    if upper.startswith(ROAD_PREFIX):
        return 'RUA'
    if upper.startswith('CASA-'):
        return 'CASA'
    if upper.startswith('COM-'):
        return 'COM'
    if upper.startswith(PLAZA_PREFIX):
        return 'PRACA'
    return ''


def is_building_code(code: str) -> bool:
    upper = code.strip().upper()
    return upper.startswith(BUILDING_PREFIXES)


def load_canonical_city_locations(app_root: Path) -> dict[str, CityLocationMeta]:
    """Carrega todos os códigos canônicos da cidade-base a partir do mapa de referência."""
    locations: dict[str, CityLocationMeta] = {}
    ref_map = app_root / 'story' / 'vibe-coding' / 'map' / 'map.md'
    if not ref_map.is_file():
        return locations

    building_idx = 0
    plaza_idx = 0
    road_idx = 0
    for raw_line in ref_map.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or line.startswith('<!--'):
            continue
        if line.startswith('- '):
            line = line[2:].strip()
        if ':' not in line:
            continue
        code_part, rest = line.split(':', 1)
        code = code_part.strip().upper()
        name = rest.split('|', 1)[0].strip()
        if not CODE_RE.match(code) or not name:
            continue
        kind = infer_location_kind(code)
        if kind == 'RUA':
            gx = road_idx % GRID_BLOCKS
            gy = road_idx // GRID_BLOCKS
            road_idx += 1
        elif kind == 'PRACA':
            gx = (plaza_idx % 6) * 5 + 2
            gy = (plaza_idx // 6) * 5 + 2
            plaza_idx += 1
        else:
            bx = building_idx % GRID_BLOCKS
            by = (building_idx // GRID_BLOCKS) % GRID_BLOCKS
            gx, gy = bx, by
            building_idx += 1

        locations[code] = CityLocationMeta(
            code=code,
            default_name=name,
            kind=kind,
            grid_x=gx,
            grid_y=gy,
        )
    return locations
