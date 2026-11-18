from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil

from .city_catalog import load_canonical_city_locations
from .markdown_codec import (
    parse_character_markdown,
    parse_encounter_markdown,
    parse_item_markdown,
    parse_map_markdown,
    parse_mission_markdown,
    parse_story_markdown,
    serialize_character_markdown,
    serialize_encounter_markdown,
    serialize_item_markdown,
    serialize_map_markdown,
    serialize_mission_markdown,
    serialize_story_markdown,
)
from .models import (
    Character,
    CutsceneBlock,
    CutsceneStep,
    MapLocation,
    Mission,
    StoryCatalogEntry,
    StoryPackage,
)


ALLOWED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
STORY_ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class StoryIOError(OSError):
    """Erro de leitura ou gravação de pacote de história."""


def atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f'.{target.name}.tmp')
    tmp_path.write_text(content, encoding='utf-8')
    os.replace(tmp_path, target)


def safe_rel_path(raw_path: str) -> str:
    value = (raw_path or '').strip()
    if not value:
        return ''
    if value.startswith(('/', '\\')) or '..' in value or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', value):
        raise StoryIOError(f'Caminho inválido "{value}". Use apenas caminhos relativos dentro da história.')
    return value.lstrip('./')


def import_asset_file(story_dir: Path, src_path: Path, target_subdir: str = 'assets', target_name: str = '') -> str:
    if not src_path.is_file():
        raise StoryIOError(f'Arquivo de imagem não encontrado: {src_path}')
    ext = src_path.suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise StoryIOError(f'Formato de imagem não suportado "{ext}". Use PNG, JPG, WEBP ou SVG.')

    clean_subdir = safe_rel_path(target_subdir) or 'assets'
    dest_dir = (story_dir / clean_subdir).resolve()
    story_root = story_dir.resolve()
    if story_root not in dest_dir.parents and dest_dir != story_root:
        raise StoryIOError('Destino de importação fora da pasta da história.')

    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r'[^a-z0-9_-]+', '-', (target_name or src_path.stem).lower()).strip('-') or 'asset'
    dest_file = dest_dir / f'{stem}{ext}'
    if src_path.resolve() != dest_file.resolve():
        shutil.copy2(src_path, dest_file)
    return dest_file.relative_to(story_root).as_posix()


def load_catalog(app_root: Path) -> list[StoryCatalogEntry]:
    catalog_file = app_root / 'story' / 'stories.json'
    if not catalog_file.is_file():
        return []
    data = json.loads(catalog_file.read_text(encoding='utf-8'))
    entries: list[StoryCatalogEntry] = []
    for item in data.get('stories', []):
        story_id = str(item.get('id', '')).strip()
        if not story_id or story_id == '_template':
            continue
        entries.append(StoryCatalogEntry(
            id=story_id,
            title=str(item.get('title', story_id)).strip(),
            description=str(item.get('description', '')).strip(),
            cover=str(item.get('cover', '')).strip(),
            path=str(item.get('path', f'./story/{story_id}')).strip(),
        ))
    return entries


def save_catalog(app_root: Path, entries: list[StoryCatalogEntry]) -> None:
    catalog_file = app_root / 'story' / 'stories.json'
    payload = {
        'stories': [
            {
                'id': entry.id,
                'title': entry.title,
                'description': entry.description,
                'cover': entry.cover or f'./story/{entry.id}/{_default_cover_rel(app_root / "story" / entry.id)}',
                'path': entry.normalized_path(),
            }
            for entry in entries
        ]
    }
    atomic_write_text(catalog_file, json.dumps(payload, indent=2, ensure_ascii=False) + '\n')


def _default_cover_rel(story_dir: Path) -> str:
    if (story_dir / 'splash' / 'splash-start.png').is_file():
        return 'splash/splash-start.png'
    if (story_dir / 'assets' / 'splash.svg').is_file():
        return 'assets/splash.svg'
    return 'splash/splash-start.png'


def load_story_package(app_root: Path, story_id: str) -> StoryPackage:
    story_dir = app_root / 'story' / story_id
    manifest_path = story_dir / 'story.md'
    if not manifest_path.is_file():
        raise StoryIOError(f'História "{story_id}" não encontrada em {story_dir}.')

    pkg = parse_story_markdown(manifest_path.read_text(encoding='utf-8'), story_id)

    for char_id in pkg.characters_order:
        char_file = story_dir / 'characters' / f'{char_id}.md'
        if char_file.is_file():
            pkg.characters[char_id] = parse_character_markdown(char_file.read_text(encoding='utf-8'), char_file.name)

    for item_id in list(pkg.items_order) + list(pkg.collectibles_order):
        item_file = story_dir / 'items' / f'{item_id}.md'
        if item_file.is_file():
            pkg.items[item_id] = parse_item_markdown(item_file.read_text(encoding='utf-8'), item_file.name)

    for mission_id in pkg.missions_order:
        mission_file = story_dir / 'missions' / f'{mission_id}.md'
        if mission_file.is_file():
            pkg.missions[mission_id] = parse_mission_markdown(mission_file.read_text(encoding='utf-8'), mission_file.name)

    for enc_id in pkg.encounters_order:
        enc_file = story_dir / 'missions' / f'{enc_id}.md'
        if enc_file.is_file():
            pkg.encounters[enc_id] = parse_encounter_markdown(enc_file.read_text(encoding='utf-8'), enc_file.name)

    canonical = load_canonical_city_locations(app_root)
    for code, meta in canonical.items():
        pkg.locations[code] = MapLocation(code=code, name=meta.default_name, kind=meta.kind)

    map_file = story_dir / 'map' / 'map.md'
    if map_file.is_file():
        parsed_locs = parse_map_markdown(map_file.read_text(encoding='utf-8'), 'map/map.md')
        for code, loc in parsed_locs.items():
            pkg.locations[code] = loc

    return pkg


def save_story_package(app_root: Path, pkg: StoryPackage) -> None:
    story_dir = app_root / 'story' / pkg.id
    story_dir.mkdir(parents=True, exist_ok=True)

    # Sincroniza ordem com dicionários atuais
    pkg.characters_order = [cid for cid in pkg.characters_order if cid in pkg.characters] + [
        cid for cid in pkg.characters if cid not in pkg.characters_order
    ]
    pkg.items_order = [iid for iid in pkg.items_order if iid in pkg.items and pkg.items[iid].category != 'extra'] + [
        iid for iid, it in pkg.items.items() if it.category != 'extra' and iid not in pkg.items_order
    ]
    pkg.collectibles_order = [iid for iid in pkg.collectibles_order if iid in pkg.items and pkg.items[iid].category == 'extra'] + [
        iid for iid, it in pkg.items.items() if it.category == 'extra' and iid not in pkg.collectibles_order
    ]
    pkg.missions_order = [mid for mid in pkg.missions_order if mid in pkg.missions] + [
        mid for mid in pkg.missions if mid not in pkg.missions_order
    ]
    pkg.encounters_order = [eid for eid in pkg.encounters_order if eid in pkg.encounters] + [
        eid for eid in pkg.encounters if eid not in pkg.encounters_order
    ]

    atomic_write_text(story_dir / 'story.md', serialize_story_markdown(pkg))

    chars_dir = story_dir / 'characters'
    chars_dir.mkdir(parents=True, exist_ok=True)
    for existing in chars_dir.glob('*.md'):
        if existing.stem not in pkg.characters:
            existing.unlink()
    for char_id, char in pkg.characters.items():
        atomic_write_text(chars_dir / f'{char_id}.md', serialize_character_markdown(char))

    items_dir = story_dir / 'items'
    items_dir.mkdir(parents=True, exist_ok=True)
    for existing in items_dir.glob('*.md'):
        if existing.stem not in pkg.items:
            existing.unlink()
    for item_id, item in pkg.items.items():
        atomic_write_text(items_dir / f'{item_id}.md', serialize_item_markdown(item))

    missions_dir = story_dir / 'missions'
    missions_dir.mkdir(parents=True, exist_ok=True)
    valid_mission_stems = set(pkg.missions.keys()) | set(pkg.encounters.keys())
    for existing in missions_dir.glob('*.md'):
        if existing.stem not in valid_mission_stems:
            existing.unlink()
    for mission_id, mission in pkg.missions.items():
        atomic_write_text(missions_dir / f'{mission_id}.md', serialize_mission_markdown(mission))
    for enc_id, encounter in pkg.encounters.items():
        atomic_write_text(missions_dir / f'{enc_id}.md', serialize_encounter_markdown(encounter))

    if pkg.locations:
        atomic_write_text(story_dir / 'map' / 'map.md', serialize_map_markdown(pkg.locations))

    # Atualiza catálogo stories.json
    entries = load_catalog(app_root)
    cover_rel = pkg.splash or _default_cover_rel(story_dir)
    if not (story_dir / cover_rel).is_file():
        cover_rel = _default_cover_rel(story_dir)
    cover_url = f'./story/{pkg.id}/{cover_rel}' if (story_dir / cover_rel).is_file() else ''
    updated = False
    for entry in entries:
        if entry.id == pkg.id:
            entry.title = pkg.title
            entry.description = pkg.subtitle or pkg.body_description
            entry.cover = cover_url
            entry.path = f'./story/{pkg.id}'
            updated = True
            break
    if not updated:
        entries.append(StoryCatalogEntry(
            id=pkg.id,
            title=pkg.title,
            description=pkg.subtitle or pkg.body_description,
            cover=cover_url,
            path=f'./story/{pkg.id}',
        ))
    save_catalog(app_root, entries)


def create_story(app_root: Path, story_id: str, title: str, description: str = '') -> StoryPackage:
    clean_id = (story_id or '').strip().lower()
    if clean_id == '_template' or not STORY_ID_RE.match(clean_id):
        raise StoryIOError('Identificador inválido. Use apenas letras minúsculas, números e hífen.')
    story_dir = app_root / 'story' / clean_id
    if story_dir.exists():
        raise StoryIOError(f'Já existe uma história com o identificador "{clean_id}".')

    template_dir = app_root / 'story' / '_template'
    if template_dir.is_dir():
        shutil.copytree(template_dir, story_dir)
        pkg = load_story_package(app_root, clean_id)
        clean_title = title.strip() or clean_id
        clean_desc = description.strip() or pkg.body_description
        pkg.title = clean_title
        pkg.page_title = clean_title
        pkg.subtitle = description.strip() or pkg.subtitle
        pkg.body_title = clean_title
        pkg.body_description = clean_desc
        save_story_package(app_root, pkg)
        return pkg

    for sub in ('assets', 'characters', 'items', 'map', 'missions', 'splash'):
        (story_dir / sub).mkdir(parents=True, exist_ok=True)

    # Copia recursos mínimos da campanha base quando disponíveis para garantir jogo funcional imediato
    ref_dir = app_root / 'story' / 'vibe-coding'
    for rel in (
        'assets/splash.svg',
        'assets/alex-top.svg',
        'assets/alex-front.svg',
        'assets/alex-left.svg',
        'assets/alex-right.svg',
        'assets/clara-top.svg',
        'assets/clara-front.svg',
        'assets/clara-left.svg',
        'assets/clara-right.svg',
        'favicon.svg',
    ):
        src = ref_dir / rel
        if src.is_file():
            dst = story_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    canonical = load_canonical_city_locations(app_root)
    locations = {
        code: MapLocation(code=code, name=meta.default_name, kind=meta.kind)
        for code, meta in canonical.items()
    }

    pkg = StoryPackage(
        id=clean_id,
        title=title.strip() or clean_id,
        page_title=title.strip() or clean_id,
        subtitle=description.strip(),
        body_title=title.strip() or clean_id,
        body_description=description.strip() or 'Nova história criada no setup.',
        splash='assets/splash.svg',
        characters_order=['protagonista', 'contato'],
        missions_order=['01-inicio'],
        characters={
            'protagonista': Character(
                id='protagonista',
                name='Protagonista',
                profile='Personagem principal da história.',
                traits='Ágil, curioso',
                sprite_top='assets/alex-top.svg',
                sprite_front='assets/alex-front.svg',
                sprite_left='assets/alex-left.svg',
                sprite_right='assets/alex-right.svg',
            ),
            'contato': Character(
                id='contato',
                name='Contato',
                profile='Aliado na cidade.',
                traits='Comunicativo',
                sprite_top='assets/clara-top.svg',
                sprite_front='assets/clara-front.svg',
                sprite_left='assets/clara-left.svg',
                sprite_right='assets/clara-right.svg',
            ),
        },
        missions={
            '01-inicio': Mission(
                id='01-inicio',
                title='Missão 1 — Primeiro Contato',
                start='CASA-001',
                target='PRACA-001',
                objective='Vá até PRACA-001 para encontrar o Contato.',
                cutscene_inicio=CutsceneBlock(
                    name='CUTSCENE_INICIO',
                    left='protagonista',
                    right='contato',
                    bg='Frente da CASA-001',
                    steps=[CutsceneStep(kind='line', speaker='Contato', text='Te espero na PRACA-001!')],
                ),
                cutscene_fim=CutsceneBlock(
                    name='CUTSCENE_FIM',
                    left='protagonista',
                    right='contato',
                    bg='PRACA-001',
                    steps=[CutsceneStep(kind='line', speaker='Contato', text='Missão cumprida!')],
                ),
            ),
        },
        locations=locations,
    )
    save_story_package(app_root, pkg)
    return pkg


def delete_story(app_root: Path, story_id: str) -> None:
    entries = load_catalog(app_root)
    remaining = [e for e in entries if e.id != story_id]
    story_dir = (app_root / 'story' / story_id).resolve()
    story_root = (app_root / 'story').resolve()
    if story_dir.exists() and story_root in story_dir.parents:
        shutil.rmtree(story_dir)
    save_catalog(app_root, remaining)
