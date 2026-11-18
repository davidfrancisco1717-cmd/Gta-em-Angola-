from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
import re

from ..core.models import Character, StoryPackage
from ..core.validator import find_dependents
from .widgets import AssetPickerRow


SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class CharactersTab(QWidget):
    """Aba de cadastro, edição e remoção segura de personagens."""

    def __init__(
        self,
        story_dir_provider: Callable[[], Path | None],
        on_data_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pkg: StoryPackage | None = None
        self._current_id: str | None = None
        self._on_data_changed = on_data_changed

        layout = QVBoxLayout(self)
        splitter = QSplitter()
        layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.char_list = QListWidget()
        self.char_list.currentItemChanged.connect(self._on_selected)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton('+ Novo Personagem')
        self.add_btn.setObjectName('PrimaryButton')
        self.del_btn = QPushButton('Excluir')
        self.del_btn.setObjectName('DangerButton')
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)

        left_layout.addWidget(self.char_list, 1)
        left_layout.addLayout(btn_row)

        right_group = QGroupBox('Dados e Sprites do Personagem')
        form = QFormLayout(right_group)
        form.setSpacing(8)

        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.name_edit = QLineEdit()
        self.profile_edit = QLineEdit()
        self.traits_edit = QLineEdit()

        self.top_picker = AssetPickerRow(story_dir_provider, subdir='assets', on_changed=lambda _: self._sync())
        self.front_picker = AssetPickerRow(story_dir_provider, subdir='assets', on_changed=lambda _: self._sync())
        self.left_picker = AssetPickerRow(story_dir_provider, subdir='assets', on_changed=lambda _: self._sync())
        self.right_picker = AssetPickerRow(story_dir_provider, subdir='assets', on_changed=lambda _: self._sync())
        self.cutscene_picker = AssetPickerRow(
            story_dir_provider,
            subdir='assets',
            allow_clear=True,
            on_changed=lambda _: self._sync(),
        )

        form.addRow('ID:', self.id_edit)
        form.addRow('Nome:', self.name_edit)
        form.addRow('Perfil:', self.profile_edit)
        form.addRow('Características:', self.traits_edit)
        form.addRow('Visão superior (top):', self.top_picker)
        form.addRow('Visão frontal (front):', self.front_picker)
        form.addRow('Visão esquerda (left):', self.left_picker)
        form.addRow('Visão direita (right):', self.right_picker)
        form.addRow('Retrato Cutscene (PNG):', self.cutscene_picker)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_group)
        splitter.setSizes([250, 620])

        self.name_edit.textChanged.connect(self._sync)
        self.profile_edit.textChanged.connect(self._sync)
        self.traits_edit.textChanged.connect(self._sync)

    def load_package(self, pkg: StoryPackage | None) -> None:
        self._pkg = pkg
        self._current_id = None
        self.char_list.clear()
        if not pkg:
            self._clear_form()
            return
        for cid in pkg.characters_order:
            char = pkg.characters.get(cid)
            if not char:
                continue
            item = QListWidgetItem(f'{char.name} ({char.id})')
            item.setData(256, cid)
            self.char_list.addItem(item)
        if self.char_list.count() > 0:
            self.char_list.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self) -> None:
        self._current_id = None
        self.id_edit.clear()
        self.name_edit.clear()
        self.profile_edit.clear()
        self.traits_edit.clear()
        self.top_picker.set_value('')
        self.front_picker.set_value('')
        self.left_picker.set_value('')
        self.right_picker.set_value('')
        self.cutscene_picker.set_value('')

    def _on_selected(self, current: QListWidgetItem | None) -> None:
        if not current or not self._pkg:
            return
        cid = current.data(256)
        char = self._pkg.characters.get(cid)
        if not char:
            return
        self._current_id = None
        self.id_edit.setText(char.id)
        self.name_edit.setText(char.name)
        self.profile_edit.setText(char.profile)
        self.traits_edit.setText(char.traits)
        self.top_picker.set_value(char.sprite_top)
        self.front_picker.set_value(char.sprite_front)
        self.left_picker.set_value(char.sprite_left)
        self.right_picker.set_value(char.sprite_right)
        self.cutscene_picker.set_value(char.sprite_cutscene)
        self._current_id = cid

    def _sync(self) -> None:
        if not self._pkg or not self._current_id:
            return
        char = self._pkg.characters.get(self._current_id)
        if not char:
            return
        char.name = self.name_edit.text().strip()
        char.profile = self.profile_edit.text().strip()
        char.traits = self.traits_edit.text().strip()
        char.sprite_top = self.top_picker.value()
        char.sprite_front = self.front_picker.value()
        char.sprite_left = self.left_picker.value()
        char.sprite_right = self.right_picker.value()
        char.sprite_cutscene = self.cutscene_picker.value()
        item = self.char_list.currentItem()
        if item:
            item.setText(f'{char.name or char.id} ({char.id})')
        if self._on_data_changed:
            self._on_data_changed()

    def _on_add(self) -> None:
        if not self._pkg:
            return
        raw_id, ok = QInputDialog.getText(self, 'Novo Personagem', 'Identificador (ex.: ana, chefe-01):')
        if not ok:
            return
        cid = raw_id.strip().lower()
        if not SLUG_RE.match(cid):
            QMessageBox.warning(self, 'ID inválido', 'Use apenas letras minúsculas, números e hífen.')
            return
        if cid in self._pkg.characters:
            QMessageBox.warning(self, 'Duplicado', f'Já existe um personagem com ID "{cid}".')
            return
        char = Character(id=cid, name=cid.capitalize())
        self._pkg.characters[cid] = char
        self._pkg.characters_order.append(cid)
        self.load_package(self._pkg)
        self.char_list.setCurrentRow(self.char_list.count() - 1)
        if self._on_data_changed:
            self._on_data_changed()

    def _on_delete(self) -> None:
        if not self._pkg or not self._current_id:
            return
        refs = find_dependents(self._pkg, 'character', self._current_id)
        if refs:
            QMessageBox.warning(
                self,
                'Exclusão bloqueada',
                f'O personagem "{self._current_id}" está em uso e não pode ser excluído:\n\n• ' + '\n• '.join(refs),
            )
            return
        cid = self._current_id
        self._pkg.characters.pop(cid, None)
        self._pkg.characters_order = [c for c in self._pkg.characters_order if c != cid]
        self.load_package(self._pkg)
        if self._on_data_changed:
            self._on_data_changed()
