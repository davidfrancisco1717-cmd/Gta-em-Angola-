from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.models import CutsceneBlock, CutsceneStep, Encounter, Mission, StoryPackage
from .map_picker import LocationPickerField
from .rich_text_field import RichTextLineWidget


SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def _set_combo_by_data(combo: QComboBox, value: str) -> None:
    idx = combo.findData(value)
    if idx >= 0:
        combo.setCurrentIndex(idx)
    elif combo.count() > 0:
        combo.setCurrentIndex(0)


class CutsceneStepDialog(QDialog):
    """Diálogo guiado para adicionar ou editar um passo de cutscene sem digitação livre de IDs."""

    def __init__(
        self,
        app_root: Path,
        pkg_provider: Callable[[], StoryPackage | None],
        characters: list[tuple[str, str]],
        items: list[tuple[str, str]],
        step: CutsceneStep | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle('Passo da Cutscene')
        self.resize(560, 320)

        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        self.kind_combo = QComboBox()
        self.kind_combo.addItem('Fala de personagem (line)', 'line')
        self.kind_combo.addItem('Opção de escolha (choice)', 'choice')
        self.kind_combo.addItem('Entregar item (deliver)', 'deliver')
        self.kind_combo.addItem('Botão de link externo (link)', 'link')

        self.speaker_combo = QComboBox()
        for cid, cname in characters:
            self.speaker_combo.addItem(f'{cname} ({cid})', cname)

        self.deliver_combo = QComboBox()
        for iid, iname in items:
            self.deliver_combo.addItem(f'{iname} ({iid})', iid)

        self.text_edit = RichTextLineWidget(app_root, pkg_provider, placeholder='Use B/I/U ou + Local / + Item / + Personagem')
        self.choice_target_combo = QComboBox()
        self.choice_target_combo.addItems(['NEXT', 'FAIL'])
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText('https://...')
        self.reason_edit = QLineEdit()

        self.form.addRow('Tipo:', self.kind_combo)
        self.form.addRow('Falante:', self.speaker_combo)
        self.form.addRow('Item a entregar:', self.deliver_combo)
        self.form.addRow('Texto / Rótulo:', self.text_edit)
        self.form.addRow('Destino (escolha):', self.choice_target_combo)
        self.form.addRow('URL (link):', self.url_edit)
        self.form.addRow('Motivo falha (FAIL):', self.reason_edit)

        layout.addLayout(self.form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if step:
            _set_combo_by_data(self.kind_combo, step.kind)
            if step.kind == 'line':
                idx = self.speaker_combo.findData(step.speaker)
                if idx < 0:
                    for i in range(self.speaker_combo.count()):
                        if self.speaker_combo.itemData(i).lower() == step.speaker.lower():
                            idx = i
                            break
                if idx >= 0:
                    self.speaker_combo.setCurrentIndex(idx)
                self.text_edit.setText(step.text)
            elif step.kind == 'deliver':
                _set_combo_by_data(self.deliver_combo, step.text)
            elif step.kind == 'choice':
                self.text_edit.setText(step.text)
                self.choice_target_combo.setCurrentText(step.target or 'NEXT')
                self.reason_edit.setText(step.reason)
            elif step.kind == 'link':
                self.text_edit.setText(step.text)
                self.url_edit.setText(step.target)

        self.kind_combo.currentIndexChanged.connect(self._update_visibility)
        self.choice_target_combo.currentTextChanged.connect(self._update_visibility)
        self._update_visibility()

    def _set_row_visible(self, field: QWidget, visible: bool) -> None:
        label = self.form.labelForField(field)
        field.setVisible(visible)
        if label:
            label.setVisible(visible)

    def _update_visibility(self) -> None:
        kind = self.kind_combo.currentData()
        self._set_row_visible(self.speaker_combo, kind == 'line')
        self._set_row_visible(self.deliver_combo, kind == 'deliver')
        self._set_row_visible(self.text_edit, kind in ('line', 'choice', 'link'))
        self._set_row_visible(self.choice_target_combo, kind == 'choice')
        self._set_row_visible(self.url_edit, kind == 'link')
        is_fail = kind == 'choice' and self.choice_target_combo.currentText() == 'FAIL'
        self._set_row_visible(self.reason_edit, is_fail)

    def to_step(self) -> CutsceneStep:
        kind = str(self.kind_combo.currentData())
        if kind == 'line':
            return CutsceneStep(
                kind='line',
                speaker=str(self.speaker_combo.currentData() or ''),
                text=self.text_edit.text().strip(),
            )
        if kind == 'deliver':
            return CutsceneStep(
                kind='deliver',
                text=str(self.deliver_combo.currentData() or ''),
            )
        if kind == 'link':
            return CutsceneStep(
                kind='link',
                text=self.text_edit.text().strip() or 'Visualizar o link',
                target=self.url_edit.text().strip(),
            )
        target = self.choice_target_combo.currentText()
        return CutsceneStep(
            kind='choice',
            text=self.text_edit.text().strip(),
            target=target,
            reason=self.reason_edit.text().strip() if target == 'FAIL' else '',
        )


class CutsceneEditorWidget(QGroupBox):
    """Editor visual para um bloco de cutscene (left, right, bg e passos)."""

    def __init__(
        self,
        title: str,
        app_root: Path,
        pkg_provider: Callable[[], StoryPackage | None],
        on_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, parent)
        self._app_root = app_root
        self._pkg_provider = pkg_provider
        self._block: CutsceneBlock | None = None
        self._on_changed = on_changed
        self._suppress = False
        self._characters: list[tuple[str, str]] = []
        self._items: list[tuple[str, str]] = []

        layout = QVBoxLayout(self)
        top_form = QFormLayout()
        self.left_combo = QComboBox()
        self.right_combo = QComboBox()
        self.bg_edit = QLineEdit()
        top_form.addRow('Personagem esq.:', self.left_combo)
        top_form.addRow('Personagem dir.:', self.right_combo)
        top_form.addRow('Cenário (bg):', self.bg_edit)
        layout.addLayout(top_form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Tipo', 'Falante', 'Texto / Item', 'Destino / URL'])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(140)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        for label, cb in (
            ('+ Passo', self._on_add_step),
            ('Editar', self._on_edit_step),
            ('Subir', lambda: self._move_step(-1)),
            ('Descer', lambda: self._move_step(1)),
            ('Remover', self._on_remove_step),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(cb)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        self.left_combo.currentIndexChanged.connect(self._sync_meta)
        self.right_combo.currentIndexChanged.connect(self._sync_meta)
        self.bg_edit.textChanged.connect(self._sync_meta)

    def set_choices(self, characters: list[tuple[str, str]], items: list[tuple[str, str]]) -> None:
        self._suppress = True
        self._characters = characters
        self._items = items
        cur_left = str(self.left_combo.currentData() or '')
        cur_right = str(self.right_combo.currentData() or '')

        for combo, cur_val in ((self.left_combo, cur_left), (self.right_combo, cur_right)):
            combo.clear()
            combo.addItem('(nenhum)', 'none')
            for cid, cname in characters:
                combo.addItem(f'{cname} ({cid})', cid)
            _set_combo_by_data(combo, cur_val or 'none')
        self._suppress = False

    def load_block(self, block: CutsceneBlock | None) -> None:
        self._suppress = True
        self._block = block
        if not block:
            _set_combo_by_data(self.left_combo, 'none')
            _set_combo_by_data(self.right_combo, 'none')
            self.bg_edit.clear()
            self.table.setRowCount(0)
            self._suppress = False
            return
        _set_combo_by_data(self.left_combo, block.left or 'none')
        _set_combo_by_data(self.right_combo, block.right or 'none')
        self.bg_edit.setText(block.bg)
        self._refresh_table()
        self._suppress = False

    def _refresh_table(self) -> None:
        if not self._block:
            self.table.setRowCount(0)
            return
        self.table.setRowCount(len(self._block.steps))
        for row, step in enumerate(self._block.steps):
            self.table.setItem(row, 0, QTableWidgetItem(step.kind))
            self.table.setItem(row, 1, QTableWidgetItem(step.speaker))
            self.table.setItem(row, 2, QTableWidgetItem(step.text))
            dest = f'FAIL: {step.reason}' if step.target == 'FAIL' and step.reason else step.target
            self.table.setItem(row, 3, QTableWidgetItem(dest if step.kind in ('choice', 'link') else ''))

    def _sync_meta(self) -> None:
        if self._suppress or not self._block:
            return
        self._block.left = str(self.left_combo.currentData() or 'none')
        self._block.right = str(self.right_combo.currentData() or 'none')
        self._block.bg = self.bg_edit.text().strip()
        if self._on_changed:
            self._on_changed()

    def _on_add_step(self) -> None:
        if not self._block:
            return
        dlg = CutsceneStepDialog(self._app_root, self._pkg_provider, self._characters, self._items, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._block.steps.append(dlg.to_step())
            self._refresh_table()
            if self._on_changed:
                self._on_changed()

    def _on_edit_step(self) -> None:
        row = self.table.currentRow()
        if not self._block or row < 0 or row >= len(self._block.steps):
            return
        dlg = CutsceneStepDialog(
            self._app_root,
            self._pkg_provider,
            self._characters,
            self._items,
            self._block.steps[row],
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._block.steps[row] = dlg.to_step()
            self._refresh_table()
            if self._on_changed:
                self._on_changed()

    def _move_step(self, delta: int) -> None:
        row = self.table.currentRow()
        if not self._block or row < 0:
            return
        new_row = row + delta
        if new_row < 0 or new_row >= len(self._block.steps):
            return
        self._block.steps[row], self._block.steps[new_row] = self._block.steps[new_row], self._block.steps[row]
        self._refresh_table()
        self.table.selectRow(new_row)
        if self._on_changed:
            self._on_changed()

    def _on_remove_step(self) -> None:
        row = self.table.currentRow()
        if not self._block or row < 0 or row >= len(self._block.steps):
            return
        self._block.steps.pop(row)
        self._refresh_table()
        if self._on_changed:
            self._on_changed()


class MissionsAndEncountersTab(QWidget):
    """Aba unificada de Missões Principais (com reordenação) e Encontros Extras."""

    def __init__(
        self,
        app_root: Path,
        on_data_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_root = app_root
        self._pkg: StoryPackage | None = None
        self._current_mission_id: str | None = None
        self._current_enc_id: str | None = None
        self._on_data_changed = on_data_changed

        layout = QVBoxLayout(self)
        self.subtabs = QTabWidget()
        layout.addWidget(self.subtabs)

        self.subtabs.addTab(self._build_missions_tab(), 'Missões Principais')
        self.subtabs.addTab(self._build_encounters_tab(), 'Encontros Extras')

    def _pkg_provider(self) -> StoryPackage | None:
        return self._pkg

    def _build_missions_tab(self) -> QWidget:
        splitter = QSplitter()

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.mission_list = QListWidget()
        self.mission_list.currentItemChanged.connect(self._on_mission_selected)

        row1 = QHBoxLayout()
        add_btn = QPushButton('+ Nova Missão')
        add_btn.setObjectName('PrimaryButton')
        del_btn = QPushButton('Excluir')
        del_btn.setObjectName('DangerButton')
        add_btn.clicked.connect(self._on_add_mission)
        del_btn.clicked.connect(self._on_del_mission)
        row1.addWidget(add_btn)
        row1.addWidget(del_btn)

        row2 = QHBoxLayout()
        up_btn = QPushButton('Subir')
        down_btn = QPushButton('Descer')
        up_btn.clicked.connect(lambda: self._move_mission(-1))
        down_btn.clicked.connect(lambda: self._move_mission(1))
        row2.addWidget(up_btn)
        row2.addWidget(down_btn)

        left_layout.addWidget(self.mission_list, 1)
        left_layout.addLayout(row1)
        left_layout.addLayout(row2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        form_group = QGroupBox('Configuração da Missão')
        form = QFormLayout(form_group)
        self.m_id = QLineEdit()
        self.m_id.setReadOnly(True)
        self.m_title = QLineEdit()
        self.m_start = LocationPickerField(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())
        self.m_pickup = LocationPickerField(
            self._app_root,
            self._pkg_provider,
            allow_clear=True,
            on_changed=lambda _: self._sync_mission(),
        )
        self.m_pickup_obj = RichTextLineWidget(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())
        self.m_target = LocationPickerField(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())
        self.m_objective = RichTextLineWidget(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())
        self.m_give_item = QComboBox()
        self.m_require_item = QComboBox()
        self.m_delivery_prompt = RichTextLineWidget(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())
        self.m_wrong_msg = RichTextLineWidget(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_mission())

        form.addRow('ID:', self.m_id)
        form.addRow('Título:', self.m_title)
        form.addRow('Início (start):', self.m_start)
        form.addRow('Coleta opcional (pickup):', self.m_pickup)
        form.addRow('Objetivo coleta:', self.m_pickup_obj)
        form.addRow('Destino (target):', self.m_target)
        form.addRow('Objetivo principal:', self.m_objective)
        form.addRow('Concede item (give_item):', self.m_give_item)
        form.addRow('Exige item (require_item):', self.m_require_item)
        form.addRow('Prompt entrega:', self.m_delivery_prompt)
        form.addRow('Msg item errado:', self.m_wrong_msg)

        self.cs_inicio = CutsceneEditorWidget('Cutscene Inicial', self._app_root, self._pkg_provider, on_changed=self._on_data_changed)
        self.cs_fim = CutsceneEditorWidget('Cutscene Final', self._app_root, self._pkg_provider, on_changed=self._on_data_changed)

        right_layout.addWidget(form_group)
        right_layout.addWidget(self.cs_inicio)
        right_layout.addWidget(self.cs_fim)
        scroll.setWidget(right_container)

        splitter.addWidget(left_panel)
        splitter.addWidget(scroll)
        splitter.setSizes([260, 640])

        self.m_title.textChanged.connect(self._sync_mission)
        self.m_give_item.currentIndexChanged.connect(self._sync_mission)
        self.m_require_item.currentIndexChanged.connect(self._sync_mission)

        return splitter

    def _build_encounters_tab(self) -> QWidget:
        splitter = QSplitter()

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.enc_list = QListWidget()
        self.enc_list.currentItemChanged.connect(self._on_enc_selected)

        row = QHBoxLayout()
        add_btn = QPushButton('+ Novo Encontro')
        add_btn.setObjectName('PrimaryButton')
        del_btn = QPushButton('Excluir')
        del_btn.setObjectName('DangerButton')
        add_btn.clicked.connect(self._on_add_enc)
        del_btn.clicked.connect(self._on_del_enc)
        row.addWidget(add_btn)
        row.addWidget(del_btn)
        left_layout.addWidget(self.enc_list, 1)
        left_layout.addLayout(row)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        form_group = QGroupBox('Encontro Extra em Construção')
        form = QFormLayout(form_group)
        self.e_id = QLineEdit()
        self.e_id.setReadOnly(True)
        self.e_npc = QComboBox()
        self.e_loc = LocationPickerField(
            self._app_root,
            self._pkg_provider,
            buildings_only=True,
            on_changed=lambda _: self._sync_enc(),
        )
        self.e_prompt = RichTextLineWidget(self._app_root, self._pkg_provider, on_changed=lambda _: self._sync_enc())
        form.addRow('ID:', self.e_id)
        form.addRow('Personagem NPC:', self.e_npc)
        form.addRow('Edificação (CASA/COM):', self.e_loc)
        form.addRow('Texto da ação:', self.e_prompt)

        self.e_cutscene = CutsceneEditorWidget('Cutscene do Encontro', self._app_root, self._pkg_provider, on_changed=self._on_data_changed)
        right_layout.addWidget(form_group)
        right_layout.addWidget(self.e_cutscene, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_container)
        splitter.setSizes([260, 640])

        self.e_npc.currentIndexChanged.connect(self._sync_enc)
        return splitter

    def load_package(self, pkg: StoryPackage | None) -> None:
        self._pkg = pkg
        self._current_mission_id = None
        self._current_enc_id = None
        self.mission_list.clear()
        self.enc_list.clear()
        if not pkg:
            return

        self.refresh_reference_choices()

        for mid in pkg.missions_order:
            m = pkg.missions.get(mid)
            if not m:
                continue
            item = QListWidgetItem(f'{m.title} ({m.id})')
            item.setData(256, mid)
            self.mission_list.addItem(item)
        if self.mission_list.count() > 0:
            self.mission_list.setCurrentRow(0)

        for eid in pkg.encounters_order:
            enc = pkg.encounters.get(eid)
            if not enc:
                continue
            item = QListWidgetItem(f'{enc.id} ({enc.location})')
            item.setData(256, eid)
            self.enc_list.addItem(item)
        if self.enc_list.count() > 0:
            self.enc_list.setCurrentRow(0)

    def refresh_reference_choices(self) -> None:
        if not self._pkg:
            return
        characters = [(cid, c.name or cid) for cid, c in self._pkg.characters.items()]
        items = [(iid, it.name or iid) for iid, it in self._pkg.items.items()]

        self.cs_inicio.set_choices(characters, items)
        self.cs_fim.set_choices(characters, items)
        self.e_cutscene.set_choices(characters, items)

        cur_npc = str(self.e_npc.currentData() or '')
        self.e_npc.blockSignals(True)
        self.e_npc.clear()
        for cid, cname in characters:
            self.e_npc.addItem(f'{cname} ({cid})', cid)
        _set_combo_by_data(self.e_npc, cur_npc)
        self.e_npc.blockSignals(False)

        for combo in (self.m_give_item, self.m_require_item):
            cur_val = str(combo.currentData() or '')
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('(nenhum)', '')
            for iid, iname in items:
                combo.addItem(f'{iname} ({iid})', iid)
            _set_combo_by_data(combo, cur_val)
            combo.blockSignals(False)

    def _on_mission_selected(self, current: QListWidgetItem | None) -> None:
        if not current or not self._pkg:
            return
        mid = current.data(256)
        m = self._pkg.missions.get(mid)
        if not m:
            return
        self._current_mission_id = None
        self.m_id.setText(m.id)
        self.m_title.setText(m.title)
        self.m_start.set_code(m.start)
        self.m_pickup.set_code(m.pickup)
        self.m_pickup_obj.setText(m.pickup_objective)
        self.m_target.set_code(m.target)
        self.m_objective.setText(m.objective)
        _set_combo_by_data(self.m_give_item, m.give_item)
        _set_combo_by_data(self.m_require_item, m.require_item)
        self.m_delivery_prompt.setText(m.delivery_prompt)
        self.m_wrong_msg.setText(m.wrong_item_message)
        self.cs_inicio.load_block(m.cutscene_inicio)
        self.cs_fim.load_block(m.cutscene_fim)
        self._current_mission_id = mid

    def _sync_mission(self) -> None:
        if not self._pkg or not self._current_mission_id:
            return
        m = self._pkg.missions.get(self._current_mission_id)
        if not m:
            return
        m.title = self.m_title.text().strip()
        m.start = self.m_start.code()
        m.pickup = self.m_pickup.code()
        m.pickup_objective = self.m_pickup_obj.text().strip()
        m.target = self.m_target.code()
        m.objective = self.m_objective.text().strip()
        m.give_item = str(self.m_give_item.currentData() or '')
        m.require_item = str(self.m_require_item.currentData() or '')
        m.delivery_prompt = self.m_delivery_prompt.text().strip()
        m.wrong_item_message = self.m_wrong_msg.text().strip()
        item = self.mission_list.currentItem()
        if item:
            item.setText(f'{m.title or m.id} ({m.id})')
        if self._on_data_changed:
            self._on_data_changed()

    def _on_add_mission(self) -> None:
        if not self._pkg:
            return
        raw_id, ok = QInputDialog.getText(self, 'Nova Missão', 'Identificador (ex.: 06-entrega-final):')
        if not ok:
            return
        mid = raw_id.strip().lower()
        if not SLUG_RE.match(mid):
            QMessageBox.warning(self, 'ID inválido', 'Use apenas letras minúsculas, números e hífen.')
            return
        if mid in self._pkg.missions:
            QMessageBox.warning(self, 'Duplicado', f'Já existe uma missão "{mid}".')
            return
        chars = list(self._pkg.characters.keys())
        c1 = chars[0] if chars else 'none'
        c2 = chars[1] if len(chars) > 1 else c1
        m = Mission(
            id=mid,
            title='Nova Missão',
            start='CASA-001',
            target='PRACA-001',
            objective='Vá até PRACA-001.',
            cutscene_inicio=CutsceneBlock(name='CUTSCENE_INICIO', left=c1, right=c2, bg='Frente da CASA-001'),
            cutscene_fim=CutsceneBlock(name='CUTSCENE_FIM', left=c1, right=c2, bg='PRACA-001'),
        )
        self._pkg.missions[mid] = m
        self._pkg.missions_order.append(mid)
        self.load_package(self._pkg)
        self.mission_list.setCurrentRow(self.mission_list.count() - 1)
        if self._on_data_changed:
            self._on_data_changed()

    def _on_del_mission(self) -> None:
        if not self._pkg or not self._current_mission_id:
            return
        if len(self._pkg.missions) <= 1:
            QMessageBox.warning(self, 'Bloqueado', 'A história precisa manter ao menos 1 missão principal.')
            return
        mid = self._current_mission_id
        self._pkg.missions.pop(mid, None)
        self._pkg.missions_order = [m for m in self._pkg.missions_order if m != mid]
        self.load_package(self._pkg)
        if self._on_data_changed:
            self._on_data_changed()

    def _move_mission(self, delta: int) -> None:
        if not self._pkg:
            return
        row = self.mission_list.currentRow()
        new_row = row + delta
        if row < 0 or new_row < 0 or new_row >= len(self._pkg.missions_order):
            return
        order = self._pkg.missions_order
        order[row], order[new_row] = order[new_row], order[row]
        self.load_package(self._pkg)
        self.mission_list.setCurrentRow(new_row)
        if self._on_data_changed:
            self._on_data_changed()

    def _on_enc_selected(self, current: QListWidgetItem | None) -> None:
        if not current or not self._pkg:
            return
        eid = current.data(256)
        enc = self._pkg.encounters.get(eid)
        if not enc:
            return
        self._current_enc_id = None
        self.e_id.setText(enc.id)
        _set_combo_by_data(self.e_npc, enc.npc)
        self.e_loc.set_code(enc.location)
        self.e_prompt.setText(enc.prompt)
        self.e_cutscene.load_block(enc.cutscene)
        self._current_enc_id = eid

    def _sync_enc(self) -> None:
        if not self._pkg or not self._current_enc_id:
            return
        enc = self._pkg.encounters.get(self._current_enc_id)
        if not enc:
            return
        enc.npc = str(self.e_npc.currentData() or '')
        enc.location = self.e_loc.code()
        enc.prompt = self.e_prompt.text().strip()
        item = self.enc_list.currentItem()
        if item:
            item.setText(f'{enc.id} ({enc.location})')
        if self._on_data_changed:
            self._on_data_changed()

    def _on_add_enc(self) -> None:
        if not self._pkg:
            return
        raw_id, ok = QInputDialog.getText(self, 'Novo Encontro Extra', 'Identificador (ex.: extra-oficina):')
        if not ok:
            return
        eid = raw_id.strip().lower()
        if not SLUG_RE.match(eid):
            QMessageBox.warning(self, 'ID inválido', 'Use apenas letras minúsculas, números e hífen.')
            return
        if eid in self._pkg.encounters or eid in self._pkg.missions:
            QMessageBox.warning(self, 'Duplicado', f'Identificador "{eid}" já existe.')
            return
        chars = list(self._pkg.characters.keys())
        npc = chars[0] if chars else ''
        enc = Encounter(
            id=eid,
            npc=npc,
            location='CASA-001',
            prompt='Conversar na CASA-001',
            cutscene=CutsceneBlock(name='CUTSCENE', left=npc or 'none', right=npc or 'none', bg='Interior da CASA-001'),
        )
        self._pkg.encounters[eid] = enc
        self._pkg.encounters_order.append(eid)
        self.load_package(self._pkg)
        self.enc_list.setCurrentRow(self.enc_list.count() - 1)
        if self._on_data_changed:
            self._on_data_changed()

    def _on_del_enc(self) -> None:
        if not self._pkg or not self._current_enc_id:
            return
        eid = self._current_enc_id
        self._pkg.encounters.pop(eid, None)
        self._pkg.encounters_order = [e for e in self._pkg.encounters_order if e != eid]
        self.load_package(self._pkg)
        if self._on_data_changed:
            self._on_data_changed()
