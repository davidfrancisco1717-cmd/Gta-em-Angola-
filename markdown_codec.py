from __future__ import annotations

import re

from .city_catalog import infer_location_kind
from .models import (
    Character,
    CutsceneBlock,
    CutsceneStep,
    Encounter,
    Item,
    MapLocation,
    Mission,
    StoryPackage,
)


HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class CodecError(ValueError):
    """Erro de leitura ou serialização de arquivo de história."""


def parse_frontmatter(raw_text: str, file_name: str = 'arquivo.md') -> tuple[dict[str, str], str]:
    normalized = (raw_text or '').replace('\r\n', '\n')
    lines = normalized.split('\n')
    if not lines or lines[0].strip() != '---':
        raise CodecError(f'[{file_name}] Frontmatter ausente (esperado "---" na primeira linha).')

    end_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == '---':
            end_idx = idx
            break
    if end_idx == -1:
        raise CodecError(f'[{file_name}] Frontmatter sem fechamento "---".')

    meta: dict[str, str] = {}
    for line in lines[1:end_idx]:
        trimmed = line.strip()
        if not trimmed or trimmed.startswith('#'):
            continue
        if ':' not in trimmed:
            raise CodecError(f'[{file_name}] Linha inválida no frontmatter: "{trimmed}".')
        key, value = trimmed.split(':', 1)
        meta[key.strip()] = value.strip()

    body = '\n'.join(lines[end_idx + 1:]).strip()
    return meta, body


def serialize_frontmatter(meta: list[tuple[str, str]], body: str = '') -> str:
    lines = ['---']
    for key, value in meta:
        clean_val = str(value or '').replace('\r', ' ').replace('\n', ' ').strip()
        if clean_val != '':
            lines.append(f'{key}: {clean_val}')
    lines.append('---')
    if body.strip():
        lines.append('')
        lines.append(body.strip())
    return '\n'.join(lines) + '\n'


def split_csv_list(raw: str) -> list[str]:
    return [part.strip() for part in (raw or '').split(',') if part.strip()]


def parse_story_markdown(raw_text: str, story_id: str) -> StoryPackage:
    meta, body = parse_frontmatter(raw_text, 'story.md')
    body_title = ''
    body_desc_lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not body_title and stripped.startswith('# '):
            body_title = stripped[2:].strip()
        elif stripped:
            body_desc_lines.append(stripped)

    return StoryPackage(
        id=story_id,
        title=meta.get('title', story_id),
        page_title=meta.get('page_title', ''),
        subtitle=meta.get('subtitle', ''),
        body_title=body_title,
        body_description='\n'.join(body_desc_lines),
        splash=meta.get('splash', 'splash/splash-start.png'),
        splash_end=meta.get('splash_end', 'splash/splash-end.png'),
        characters_order=split_csv_list(meta.get('characters', '')),
        items_order=split_csv_list(meta.get('items', '')),
        collectibles_order=split_csv_list(meta.get('collectibles', '')),
        missions_order=split_csv_list(meta.get('missions', '')),
        encounters_order=split_csv_list(meta.get('encounters', '')),
    )


def serialize_story_markdown(pkg: StoryPackage) -> str:
    meta: list[tuple[str, str]] = [
        ('title', pkg.title),
        ('page_title', pkg.page_title),
        ('subtitle', pkg.subtitle),
        ('splash', pkg.splash or 'splash/splash-start.png'),
    ]
    if pkg.splash_end and pkg.splash_end != 'splash/splash-end.png':
        meta.append(('splash_end', pkg.splash_end))
    meta.append(('characters', ', '.join(pkg.characters_order)))
    meta.append(('items', ', '.join(pkg.items_order)))
    if pkg.collectibles_order:
        meta.append(('collectibles', ', '.join(pkg.collectibles_order)))
    meta.append(('missions', ', '.join(pkg.missions_order)))
    if pkg.encounters_order:
        meta.append(('encounters', ', '.join(pkg.encounters_order)))

    body_parts: list[str] = []
    heading = pkg.body_title or pkg.title
    if heading:
        body_parts.append(f'# {heading}')
    if pkg.body_description.strip():
        body_parts.append('')
        body_parts.append(pkg.body_description.strip())
    return serialize_frontmatter(meta, '\n'.join(body_parts))


def parse_character_markdown(raw_text: str, file_name: str) -> Character:
    meta, _ = parse_frontmatter(raw_text, file_name)
    return Character(
        id=meta.get('id', '').strip(),
        name=meta.get('name', '').strip(),
        profile=meta.get('profile', '').strip(),
        traits=meta.get('traits', '').strip(),
        sprite_top=meta.get('sprite_top', '').strip(),
        sprite_front=meta.get('sprite_front', '').strip(),
        sprite_left=meta.get('sprite_left', '').strip(),
        sprite_right=meta.get('sprite_right', '').strip(),
        sprite_cutscene=meta.get('sprite_cutscene', meta.get('cutscene_image', '')).strip(),
    )


def serialize_character_markdown(char: Character) -> str:
    return serialize_frontmatter([
        ('id', char.id),
        ('name', char.name),
        ('profile', char.profile),
        ('traits', char.traits),
        ('sprite_top', char.sprite_top),
        ('sprite_front', char.sprite_front),
        ('sprite_left', char.sprite_left),
        ('sprite_right', char.sprite_right),
        ('sprite_cutscene', char.sprite_cutscene),
    ])


def parse_item_markdown(raw_text: str, file_name: str) -> Item:
    meta, _ = parse_frontmatter(raw_text, file_name)
    return Item(
        id=meta.get('id', '').strip(),
        name=meta.get('name', '').strip(),
        description=meta.get('description', '').strip(),
        image=meta.get('image', '').strip(),
        location=meta.get('location', '').strip(),
        category=(meta.get('category', 'missao') or 'missao').strip().lower(),
        rarity=meta.get('rarity', '').strip(),
    )


def serialize_item_markdown(item: Item) -> str:
    fields: list[tuple[str, str]] = [
        ('id', item.id),
        ('name', item.name),
        ('description', item.description),
        ('image', item.image),
        ('location', item.location),
        ('category', item.category or 'missao'),
    ]
    if item.rarity:
        fields.append(('rarity', item.rarity))
    return serialize_frontmatter(fields)


def _parse_cutscene_block(name: str, lines: list[str]) -> CutsceneBlock:
    block = CutsceneBlock(name=name)
    for raw_line in lines:
        trimmed = raw_line.strip()
        if not trimmed:
            continue
        if not trimmed.startswith('- ') and ':' in trimmed:
            key, val = trimmed.split(':', 1)
            k = key.strip().lower()
            v = val.strip()
            if k == 'left':
                block.left = v
                continue
            if k == 'right':
                block.right = v
                continue
            if k == 'bg':
                block.bg = v
                continue
        if trimmed.startswith('- '):
            content = trimmed[2:].strip()
            if content.upper().startswith('OPCAO:'):
                payload = content[6:].strip()
                if '->' in payload:
                    label, target = payload.split('->', 1)
                    target = target.strip()
                    reason = ''
                    if ':' in target and target.upper().startswith('FAIL:'):
                        _, reason = target.split(':', 1)
                        target = 'FAIL'
                    block.steps.append(CutsceneStep(
                        kind='choice',
                        text=label.strip(),
                        target=target,
                        reason=reason.strip(),
                    ))
                else:
                    block.steps.append(CutsceneStep(kind='choice', text=payload, target='NEXT'))
            elif content.upper().startswith('ENTREGAR:'):
                item_id = content[9:].strip()
                block.steps.append(CutsceneStep(kind='deliver', text=item_id))
            elif content.upper().startswith('LINK:'):
                payload = content[5:].strip()
                if '->' in payload:
                    label, url = payload.split('->', 1)
                    block.steps.append(CutsceneStep(kind='link', text=label.strip(), target=url.strip()))
                else:
                    block.steps.append(CutsceneStep(kind='link', text='Visualizar o link', target=payload))
            elif ':' in content:
                speaker, speech = content.split(':', 1)
                block.steps.append(CutsceneStep(kind='line', speaker=speaker.strip(), text=speech.strip()))
    return block


def _serialize_cutscene_block(block: CutsceneBlock) -> str:
    lines = [
        f'## {block.name}',
        f'left: {block.left}',
        f'right: {block.right}',
        f'bg: {block.bg}',
        '',
    ]
    for step in block.steps:
        if step.kind == 'line':
            lines.append(f'- {step.speaker}: {step.text}')
        elif step.kind == 'choice':
            if step.target.upper() == 'FAIL' and step.reason:
                lines.append(f'- OPCAO: {step.text} -> FAIL: {step.reason}')
            else:
                lines.append(f'- OPCAO: {step.text} -> {step.target or "NEXT"}')
        elif step.kind == 'deliver':
            lines.append(f'- ENTREGAR: {step.text}')
        elif step.kind == 'link':
            if step.text and step.text != 'Visualizar o link':
                lines.append(f'- LINK: {step.text} -> {step.target}')
            else:
                lines.append(f'- LINK: {step.target}')
    return '\n'.join(lines)


def _split_cutscene_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('## '):
            current = trimmed[3:].strip().upper()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def parse_mission_markdown(raw_text: str, file_name: str) -> Mission:
    meta, body = parse_frontmatter(raw_text, file_name)
    sections = _split_cutscene_sections(body)
    return Mission(
        id=meta.get('id', '').strip(),
        title=meta.get('title', '').strip(),
        start=meta.get('start', '').strip().upper(),
        pickup=meta.get('pickup', '').strip().upper(),
        pickup_objective=meta.get('pickup_objective', '').strip(),
        target=meta.get('target', '').strip().upper(),
        objective=meta.get('objective', '').strip(),
        give_item=meta.get('give_item', '').strip(),
        require_item=meta.get('require_item', '').strip(),
        delivery_prompt=meta.get('delivery_prompt', '').strip(),
        wrong_item_message=meta.get('wrong_item_message', '').strip(),
        cutscene_inicio=_parse_cutscene_block('CUTSCENE_INICIO', sections.get('CUTSCENE_INICIO', [])),
        cutscene_fim=_parse_cutscene_block('CUTSCENE_FIM', sections.get('CUTSCENE_FIM', [])),
    )


def serialize_mission_markdown(mission: Mission) -> str:
    fields: list[tuple[str, str]] = [
        ('id', mission.id),
        ('title', mission.title),
        ('start', mission.start),
        ('pickup', mission.pickup),
        ('pickup_objective', mission.pickup_objective),
        ('target', mission.target),
        ('objective', mission.objective),
        ('give_item', mission.give_item),
        ('require_item', mission.require_item),
        ('delivery_prompt', mission.delivery_prompt),
        ('wrong_item_message', mission.wrong_item_message),
    ]
    body = '\n\n'.join([
        _serialize_cutscene_block(mission.cutscene_inicio),
        _serialize_cutscene_block(mission.cutscene_fim),
    ])
    return serialize_frontmatter(fields, body)


def parse_encounter_markdown(raw_text: str, file_name: str) -> Encounter:
    meta, body = parse_frontmatter(raw_text, file_name)
    sections = _split_cutscene_sections(body)
    return Encounter(
        id=meta.get('id', '').strip(),
        npc=meta.get('npc', '').strip(),
        location=meta.get('location', '').strip().upper(),
        prompt=meta.get('prompt', '').strip(),
        roof_color=meta.get('roof_color', '#d6282e').strip() or '#d6282e',
        roof_logo=meta.get('roof_logo', '').strip(),
        cutscene=_parse_cutscene_block('CUTSCENE', sections.get('CUTSCENE', [])),
    )


def serialize_encounter_markdown(encounter: Encounter) -> str:
    fields: list[tuple[str, str]] = [
        ('id', encounter.id),
        ('npc', encounter.npc),
        ('location', encounter.location),
        ('prompt', encounter.prompt),
        ('roof_color', encounter.roof_color or '#d6282e'),
        ('roof_logo', encounter.roof_logo),
    ]
    return serialize_frontmatter(fields, _serialize_cutscene_block(encounter.cutscene))


def parse_map_markdown(raw_text: str, file_name: str = 'map/map.md') -> dict[str, MapLocation]:
    locations: dict[str, MapLocation] = {}
    for line in (raw_text or '').replace('\r\n', '\n').splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith('#') or trimmed.startswith('<!--'):
            continue
        if trimmed.startswith('- '):
            trimmed = trimmed[2:].strip()
        if ':' not in trimmed:
            continue
        code_part, rest = trimmed.split(':', 1)
        code = code_part.strip().upper()
        parts = [p.strip() for p in rest.split('|')]
        name = parts[0]
        roof_color = ''
        roof_logo = ''
        for seg in parts[1:]:
            if '=' not in seg:
                continue
            k, v = seg.split('=', 1)
            key = k.strip().lower()
            val = v.strip()
            if key == 'roof_color':
                roof_color = val.lower()
            elif key == 'roof_logo':
                roof_logo = val
        if code and name:
            locations[code] = MapLocation(
                code=code,
                name=name,
                kind=infer_location_kind(code),
                roof_color=roof_color,
                roof_logo=roof_logo,
            )
    return locations


def serialize_map_markdown(locations: dict[str, MapLocation]) -> str:
    groups = {
        'RUA': ('## Ruas', []),
        'PRACA': ('## Praças', []),
        'COM': ('## Comércios', []),
        'CASA': ('## Casas', []),
    }
    for code in sorted(locations.keys()):
        loc = locations[code]
        kind = loc.kind or infer_location_kind(code)
        line = f'{loc.code}: {loc.name}'
        if loc.roof_color and HEX_COLOR_RE.match(loc.roof_color):
            line += f' | roof_color={loc.roof_color.lower()}'
        if loc.roof_logo:
            line += f' | roof_logo={loc.roof_logo}'
        if kind in groups:
            groups[kind][1].append(line)
        else:
            groups['CASA'][1].append(line)

    out = ['<!-- Mapa de nomes dos locais da cidade -->', '# Mapa da Cidade', '']
    for key in ('RUA', 'PRACA', 'COM', 'CASA'):
        heading, items = groups[key]
        if items:
            out.append(heading)
            out.extend(items)
            out.append('')
    return '\n'.join(out).rstrip() + '\n'
