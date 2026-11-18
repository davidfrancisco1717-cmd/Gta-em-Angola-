from __future__ import annotations

from pathlib import Path
import re

from .city_catalog import is_building_code
from .models import CutsceneBlock, StoryPackage


HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')
URL_RE = re.compile(r'^https?://\S+$', re.IGNORECASE)
BRACKET_TOKEN_RE = re.compile(r'\[([^\[\]\n]+)\]')
LOC_CODE_RE = re.compile(r'^(RUA|CASA|COM|PRACA)-\d+$', re.IGNORECASE)


def find_dependents(pkg: StoryPackage, kind: str, target_id: str) -> list[str]:
    """Retorna lista legível de locais onde um personagem, item ou missão está em uso."""
    refs: list[str] = []
    if kind == 'character':
        for mid, mission in pkg.missions.items():
            for block in (mission.cutscene_inicio, mission.cutscene_fim):
                if block.left == target_id or block.right == target_id:
                    refs.append(f'Missão "{mission.title or mid}" ({block.name})')
        for eid, enc in pkg.encounters.items():
            if enc.npc == target_id or enc.cutscene.left == target_id or enc.cutscene.right == target_id:
                refs.append(f'Encontro extra "{eid}"')
    elif kind == 'item':
        for mid, mission in pkg.missions.items():
            if mission.give_item == target_id:
                refs.append(f'Missão "{mission.title or mid}" (give_item)')
            if mission.require_item == target_id:
                refs.append(f'Missão "{mission.title or mid}" (require_item)')
            for block in (mission.cutscene_inicio, mission.cutscene_fim):
                if any(step.kind == 'deliver' and step.text == target_id for step in block.steps):
                    refs.append(f'Missão "{mission.title or mid}" ({block.name}: ENTREGAR)')
    return sorted(set(refs))


def validate_story(pkg: StoryPackage, app_root: Path | None = None) -> list[str]:
    """Valida todas as referências e campos obrigatórios antes de gravar a história."""
    errors: list[str] = []
    story_dir = (app_root / 'story' / pkg.id) if app_root else None

    if not pkg.title.strip():
        errors.append('O título da história (title) é obrigatório.')

    if not pkg.missions:
        errors.append('A história precisa ter ao menos 1 missão principal.')

    known_chars = set(pkg.characters.keys())
    known_items = set(pkg.items.keys())
    known_locations = set(pkg.locations.keys())

    for cid, char in pkg.characters.items():
        if not char.name.strip():
            errors.append(f'Personagem "{cid}" está sem nome.')
        for view_name, rel_path in (
            ('sprite_top', char.sprite_top),
            ('sprite_front', char.sprite_front),
            ('sprite_left', char.sprite_left),
            ('sprite_right', char.sprite_right),
        ):
            if not rel_path:
                errors.append(f'Personagem "{cid}" está sem imagem em {view_name}.')
            elif story_dir and not (story_dir / rel_path).is_file():
                errors.append(f'Personagem "{cid}" ({view_name}): arquivo ausente "{rel_path}".')
        if char.sprite_cutscene and story_dir and not (story_dir / char.sprite_cutscene).is_file():
            errors.append(f'Personagem "{cid}" (sprite_cutscene): arquivo ausente "{char.sprite_cutscene}".')

    for iid, item in pkg.items.items():
        if not item.name.strip():
            errors.append(f'Item "{iid}" está sem nome.')
        if not item.image:
            errors.append(f'Item "{iid}" está sem imagem.')
        elif story_dir and not (story_dir / item.image).is_file():
            errors.append(f'Item "{iid}": imagem ausente "{item.image}".')

    for mid, mission in pkg.missions.items():
        if not mission.title.strip():
            errors.append(f'Missão "{mid}" está sem título.')
        if not mission.objective.strip():
            errors.append(f'Missão "{mid}" está sem objetivo.')
        for field_name, code in (('start', mission.start), ('target', mission.target)):
            if not code:
                errors.append(f'Missão "{mid}" está sem código de local em "{field_name}".')
            elif known_locations and code not in known_locations:
                errors.append(f'Missão "{mid}" ({field_name}): código de local "{code}" inexistente.')
        if mission.pickup and known_locations and mission.pickup not in known_locations:
            errors.append(f'Missão "{mid}" (pickup): código de local "{mission.pickup}" inexistente.')
        if mission.give_item and mission.give_item not in known_items:
            errors.append(f'Missão "{mid}" (give_item): item "{mission.give_item}" não cadastrado.')
        if mission.require_item and mission.require_item not in known_items:
            errors.append(f'Missão "{mid}" (require_item): item "{mission.require_item}" não cadastrado.')

        _validate_bracket_placeholders(mission.objective, f'Missão "{mid}" (objective)', known_locations, known_items, errors)
        _validate_bracket_placeholders(mission.pickup_objective, f'Missão "{mid}" (pickup_objective)', known_locations, known_items, errors)
        _validate_bracket_placeholders(mission.delivery_prompt, f'Missão "{mid}" (delivery_prompt)', known_locations, known_items, errors)
        _validate_bracket_placeholders(mission.wrong_item_message, f'Missão "{mid}" (wrong_item_message)', known_locations, known_items, errors)

        _validate_cutscene_block(mission.cutscene_inicio, f'Missão "{mid}" ({mission.cutscene_inicio.name})', known_chars, known_items, known_locations, errors)
        _validate_cutscene_block(mission.cutscene_fim, f'Missão "{mid}" ({mission.cutscene_fim.name})', known_chars, known_items, known_locations, errors)

    for eid, enc in pkg.encounters.items():
        if enc.npc not in known_chars:
            errors.append(f'Encontro "{eid}": personagem "{enc.npc}" não cadastrado.')
        if not enc.location or (known_locations and enc.location not in known_locations):
            errors.append(f'Encontro "{eid}": local "{enc.location}" inexistente.')
        elif not is_building_code(enc.location):
            errors.append(f'Encontro "{eid}": local "{enc.location}" não é edificável (use CASA-* ou COM-*).')
        if enc.roof_color and not HEX_COLOR_RE.match(enc.roof_color):
            errors.append(f'Encontro "{eid}": cor de telhado inválida "{enc.roof_color}". Use #rrggbb.')
        if enc.roof_logo and story_dir and not (story_dir / enc.roof_logo).is_file():
            errors.append(f'Encontro "{eid}": logo de telhado ausente "{enc.roof_logo}".')
        _validate_bracket_placeholders(enc.prompt, f'Encontro "{eid}" (prompt)', known_locations, known_items, errors)
        _validate_cutscene_block(enc.cutscene, f'Encontro "{eid}"', known_chars, known_items, known_locations, errors)

    for code, loc in pkg.locations.items():
        if loc.roof_color and not is_building_code(code):
            errors.append(f'Local "{code}": apenas edificações (CASA-*, COM-*) aceitam cor de telhado.')
        if loc.roof_color and not HEX_COLOR_RE.match(loc.roof_color):
            errors.append(f'Local "{code}": cor de telhado inválida "{loc.roof_color}". Use #rrggbb.')
        if loc.roof_logo and not is_building_code(code):
            errors.append(f'Local "{code}": apenas edificações (CASA-*, COM-*) aceitam logo de telhado.')
        if loc.roof_logo and story_dir and not (story_dir / loc.roof_logo).is_file():
            errors.append(f'Local "{code}": logo de telhado ausente "{loc.roof_logo}".')

    return errors


def _validate_bracket_placeholders(
    text: str,
    ctx: str,
    known_locations: set[str],
    known_items: set[str],
    errors: list[str],
) -> None:
    if not text:
        return
    lower_items = {iid.lower() for iid in known_items}
    for match in BRACKET_TOKEN_RE.finditer(text):
        token = match.group(1).strip()
        if LOC_CODE_RE.match(token) and known_locations and token.upper() not in known_locations:
            errors.append(f'{ctx}: marcador "[{token}]" referencia local inexistente.')
        elif token.lower().startswith('item-'):
            item_id = token[5:].strip().lower()
            if item_id not in lower_items:
                errors.append(f'{ctx}: marcador "[{token}]" referencia item não cadastrado.')


def _validate_cutscene_block(
    block: CutsceneBlock,
    ctx: str,
    known_chars: set[str],
    known_items: set[str],
    known_locations: set[str],
    errors: list[str],
) -> None:
    if block.left and block.left.lower() != 'none' and block.left not in known_chars:
        errors.append(f'{ctx}: personagem esquerdo "{block.left}" não cadastrado.')
    if block.right and block.right.lower() != 'none' and block.right not in known_chars:
        errors.append(f'{ctx}: personagem direito "{block.right}" não cadastrado.')
    for idx, step in enumerate(block.steps, start=1):
        if step.kind == 'deliver' and step.text not in known_items:
            errors.append(f'{ctx} (passo {idx}): ENTREGAR referencia item inexistente "{step.text}".')
        elif step.kind == 'link' and not URL_RE.match(step.target or ''):
            errors.append(f'{ctx} (passo {idx}): LINK com URL inválida "{step.target}". Use http:// ou https://.')
        elif step.kind in ('line', 'choice'):
            _validate_bracket_placeholders(step.text, f'{ctx} (passo {idx})', known_locations, known_items, errors)
