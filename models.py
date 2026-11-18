from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StoryCatalogEntry:
    id: str
    title: str
    description: str = ''
    cover: str = ''
    path: str = ''

    def normalized_path(self) -> str:
        return self.path or f'./story/{self.id}'


@dataclass
class Character:
    id: str
    name: str
    profile: str = ''
    traits: str = ''
    sprite_top: str = ''
    sprite_front: str = ''
    sprite_left: str = ''
    sprite_right: str = ''
    sprite_cutscene: str = ''


@dataclass
class Item:
    id: str
    name: str
    description: str = ''
    image: str = ''
    location: str = ''
    category: str = 'missao'
    rarity: str = ''


@dataclass
class CutsceneStep:
    """Representa uma fala, escolha (OPCAO), entrega (ENTREGAR) ou link (- LINK:)."""
    kind: str  # 'line' | 'choice' | 'deliver' | 'link'
    speaker: str = ''
    text: str = ''
    target: str = 'NEXT'  # 'NEXT', 'FAIL', ou label/url
    reason: str = ''


@dataclass
class CutsceneBlock:
    name: str  # 'CUTSCENE_INICIO', 'CUTSCENE_FIM', 'CUTSCENE'
    left: str = ''
    right: str = ''
    bg: str = ''
    steps: list[CutsceneStep] = field(default_factory=list)


@dataclass
class Mission:
    id: str
    title: str
    start: str
    target: str
    objective: str
    pickup: str = ''
    pickup_objective: str = ''
    give_item: str = ''
    require_item: str = ''
    delivery_prompt: str = ''
    wrong_item_message: str = ''
    cutscene_inicio: CutsceneBlock = field(default_factory=lambda: CutsceneBlock(name='CUTSCENE_INICIO'))
    cutscene_fim: CutsceneBlock = field(default_factory=lambda: CutsceneBlock(name='CUTSCENE_FIM'))


@dataclass
class Encounter:
    id: str
    npc: str
    location: str
    prompt: str = ''
    roof_color: str = '#d6282e'
    roof_logo: str = ''
    cutscene: CutsceneBlock = field(default_factory=lambda: CutsceneBlock(name='CUTSCENE'))


@dataclass
class MapLocation:
    code: str
    name: str
    kind: str = ''  # 'RUA' | 'CASA' | 'COM' | 'PRACA'
    roof_color: str = ''
    roof_logo: str = ''


@dataclass
class StoryPackage:
    id: str
    title: str
    page_title: str = ''
    subtitle: str = ''
    body_title: str = ''
    body_description: str = ''
    splash: str = 'splash/splash-start.png'
    splash_end: str = 'splash/splash-end.png'
    characters_order: list[str] = field(default_factory=list)
    items_order: list[str] = field(default_factory=list)
    collectibles_order: list[str] = field(default_factory=list)
    missions_order: list[str] = field(default_factory=list)
    encounters_order: list[str] = field(default_factory=list)
    characters: dict[str, Character] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    missions: dict[str, Mission] = field(default_factory=dict)
    encounters: dict[str, Encounter] = field(default_factory=dict)
    locations: dict[str, MapLocation] = field(default_factory=dict)
