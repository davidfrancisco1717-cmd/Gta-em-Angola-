from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
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

from ..core.models import Item, StoryPackage
from ..core.validator import find_dependents
from .map_picker import LocationPickerField
from .widgets import AssetPickerRow


SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class ItemsTab(QWidget):
    """Aba de gerenciamento de itens de missão e itens extras de inventário."""

    def __init__(
        self,
        app_root: Path,
        story_dir_provider: Callable[[], Path | None],
        on_data_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_root = app_root
        self._pkg: StoryPackage | None = None
        self._current_id: str | None = None
        self._on_data_changed = on_data_changed

        layout = QVBoxLayout(self)
        splitter = QSplitter()
        layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.item_list = QListWidget()
        self.item_list.currentItemChanged.connect(self._on_selected)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton('+ Novo Item')
        self.add_btn.setObjectName('PrimaryButton')
        self.del_btn = QPushButton('Excluir')
        self.del_btn.setObjectName('DangerButton')
        self.add_btn.clicked.connect(self._on_add)
        self.del_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)

        left_layout.addWidget(self.item_list, 1)
        left_layout.addLayout(btn_row)

        right_group = QGroupBox('Detalhes do Item')
        form = QFormLayout(right_group)
        form.setSpacing(8)

        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.name_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(['missao', 'extra'])
        self.rarity_edit = QLineEdit()
        self.rarity_edit.setPlaceholderText('Opcional (ex.: comum, raro, épico)')
        self.location_picker = LocationPickerField(
            self._app_root,
            lambda: self._pkg,
            allow_clear=True,
            on_changed=lambda _: self._sync(),
        )
        self.image_picker = AssetPickerRow(story_dir_provider, subdir='assets', on_changed=lambda _: self._sync())

        form.addRow('ID:', self.id_edit)
        form.addRow('Nome:', self.name_edit)
        form.addRow('Descrição:', self.desc_edit)
        form.addRow('Categoria:', self.category_combo)
        form.addRow('Raridade:', self.rarity_edit)
        form.addRow('Local no mapa (extra):', self.location_picker)
        form.addRow('Imagem:', self.image_picker)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_group)
        splitter.setSizes([250, 620])

        self.name_edit.textChanged.connect(self._sync)
        self.desc_edit.textChanged.connect(self._sync)
        self.category_combo.currentTextChanged.connect(self._sync)
        self.rarity_edit.textChanged.connect(self._sync)

    def load_package(self, pkg: StoryPackage | None) -> None:
        self._pkg = pkg
        self._current_id = None
        self.item_list.clear()
        if not pkg:
            self._clear_form()
            return
        ordered = list(pkg.items_order) + [iid for iid in pkg.collectibles_order if iid not in pkg.items_order]
        for iid in pkg.items:
            if iid not in ordered:
                ordered.append(iid)
        for iid in ordered:
            item = pkg.items.get(iid)
            if not item:
                continue
            list_item = QListWidgetItem(f'[{item.category}] {item.name} ({item.id})')
            list_item.setData(256, iid)
            self.item_list.addItem(list_item)
        if self.item_list.count() > 0:
            self.item_list.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self) -> None:
        self._current_id = None
        self.id_edit.clear()
        self.name_edit.clear()
        self.desc_edit.clear()
        self.rarity_edit.clear()
        self.location_picker.set_code('')
        self.image_picker.set_value('')

    def _on_selected(self, current: QListWidgetItem | None) -> None:
        if not current or not self._pkg:
            return
        iid = current.data(256)
        item = self._pkg.items.get(iid)
        if not item:
            return
        self._current_id = None
        self.id_edit.setText(item.id)
        self.name_edit.setText(item.name)
        self.desc_edit.setText(item.description)
        self.category_combo.setCurrentText(item.category if item.category in ('missao', 'extra') else 'missao')
        self.rarity_edit.setText(item.rarity)
        self.location_picker.set_code(item.location)
        self.image_picker.set_value(item.image)
        self._current_id = iid

    def _sync(self) -> None:
        if not self._pkg or not self._current_id:
            return
        item = self._pkg.items.get(self._current_id)
        if not item:
            return
        item.name = self.name_edit.text().strip()
        item.description = self.desc_edit.text().strip()
        item.category = self.category_combo.currentText()
        item.rarity = self.rarity_edit.text().strip()
        item.location = self.location_picker.code()
        item.image = self.image_picker.value()
        list_item = self.item_list.currentItem()
        if list_item:
            list_item.setText(f'[{item.category}] {item.name or item.id} ({item.id})')
        if self._on_data_changed:
            self._on_data_changed()

    def _on_add(self) -> None:
        if not self._pkg:
            return
        raw_id, ok = QInputDialog.getText(self, 'Novo Item', 'Identificador (ex.: chave-dourada):')
        if not ok:
            return
        iid = raw_id.strip().lower()
        if not SLUG_RE.match(iid):
            QMessageBox.warning(self, 'ID inválido', 'Use apenas letras minúsculas, números e hífen.')
            return
        if iid in self._pkg.items:
            QMessageBox.warning(self, 'Duplicado', f'Já existe um item com ID "{iid}".')
            return
        item = Item(id=iid, name=iid.replace('-', ' ').title(), category='missao')
        self._pkg.items[iid] = item
        self._pkg.items_order.append(iid)
        self.load_package(self._pkg)
        self.item_list.setCurrentRow(self.item_list.count() - 1)
        if self._on_data_changed:
            self._on_data_changed()

    def _on_delete(self) -> None:
        if not self._pkg or not self._current_id:
            return
        refs = find_dependents(self._pkg, 'item', self._current_id)
        if refs:
            QMessageBox.warning(
                self,
                'Exclusão bloqueada',
                f'O item "{self._current_id}" está em uso e não pode ser excluído:\n\n• ' + '\n• '.join(refs),
            )
            return
        iid = self._current_id
        self._pkg.items.pop(iid, None)
        self._pkg.items_order = [i for i in self._pkg.items_order if i != iid]
        self._pkg.collectibles_order = [i for i in self._pkg.collectibles_order if i != iid]
        self.load_package(self._pkg)
        if self._on_data_changed:
            self._on_data_changed()
