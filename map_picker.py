from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.city_catalog import GRID_BLOCKS, is_building_code, load_canonical_city_locations
from ..core.models import StoryPackage


class _SelectableMapRect(QGraphicsRectItem):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        code: str,
        selectable: bool,
        on_click: Callable[[str], None],
    ) -> None:
        super().__init__(x, y, w, h)
        self.code = code
        self._selectable = selectable
        self._on_click = on_click
        if selectable:
            self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event: object) -> None:
        if self._selectable:
            self._on_click(self.code)


class LocationPickerDialog(QDialog):
    """Diálogo visual para escolher um local clicando nos quadrados do mapa."""

    def __init__(
        self,
        app_root: Path,
        pkg: StoryPackage | None,
        current_code: str = '',
        buildings_only: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_root = app_root
        self._pkg = pkg
        self._buildings_only = buildings_only
        self._canonical = load_canonical_city_locations(app_root)
        self.selected_code = (current_code or '').strip().upper()

        self.setWindowTitle('Escolher Local no Mapa')
        self.resize(620, 600)

        layout = QVBoxLayout(self)
        hint = QLabel(
            'Clique em um quadrado do mapa para selecionar uma edificação (CASA/COM):'
            if buildings_only
            else 'Clique em um quadrado do mapa para selecionar uma edificação ou praça:'
        )
        layout.addWidget(hint)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view, 1)

        self.selection_label = QLabel()
        self.selection_label.setStyleSheet(
            'padding: 8px 10px; background: #141720; border: 1px solid #2b3245; '
            'border-radius: 6px; font-weight: 700; color: #f59e0b;'
        )
        layout.addWidget(self.selection_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Confirmar')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        layout.addWidget(buttons)

        self._render_map()
        self._update_selection_label()

    def _location_name(self, code: str) -> str:
        if self._pkg and code in self._pkg.locations:
            return self._pkg.locations[code].name
        if code in self._canonical:
            return self._canonical[code].default_name
        return ''

    def _on_rect_clicked(self, code: str) -> None:
        self.selected_code = code
        self._render_map()
        self._update_selection_label()

    def _update_selection_label(self) -> None:
        if not self.selected_code:
            self.selection_label.setText('Nenhum local selecionado.')
            self._ok_btn.setEnabled(False)
            return
        name = self._location_name(self.selected_code)
        full = f'{self.selected_code} — {name}' if name else self.selected_code
        self.selection_label.setText(f'Selecionado: {full}')
        valid = is_building_code(self.selected_code) if self._buildings_only else True
        self._ok_btn.setEnabled(valid)

    def _render_map(self) -> None:
        self.scene.clear()
        cell = 15
        for code, meta in self._canonical.items():
            if meta.kind == 'RUA':
                continue
            selectable = is_building_code(code) if self._buildings_only else True
            x = (meta.grid_x % GRID_BLOCKS) * (cell + 2)
            y = (meta.grid_y % GRID_BLOCKS) * (cell + 2)
            rect = _SelectableMapRect(x, y, cell, cell, code, selectable, self._on_rect_clicked)

            loc = self._pkg.locations.get(code) if self._pkg else None
            if not selectable:
                fill = QColor('#222733')
            elif loc and loc.roof_color:
                fill = QColor(loc.roof_color)
            elif meta.kind == 'PRACA':
                fill = QColor('#2d6a4f')
            elif meta.kind == 'COM':
                fill = QColor('#3d5a80')
            else:
                fill = QColor('#8d5b4c')

            is_sel = code == self.selected_code
            rect.setBrush(QBrush(fill))
            rect.setPen(QPen(QColor('#f59e0b' if is_sel else '#0e1015'), 2.2 if is_sel else 0.7))
            name = loc.name if loc else meta.default_name
            rect.setToolTip(f'{code} — {name}')
            self.scene.addItem(rect)


class LocationPickerField(QWidget):
    """Campo somente leitura com botão para escolher o local clicando no mapa."""

    def __init__(
        self,
        app_root: Path,
        pkg_provider: Callable[[], StoryPackage | None],
        buildings_only: bool = False,
        allow_clear: bool = False,
        on_changed: Callable[[str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_root = app_root
        self._pkg_provider = pkg_provider
        self._buildings_only = buildings_only
        self._on_changed = on_changed
        self._code = ''

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.display_edit = QLineEdit()
        self.display_edit.setReadOnly(True)
        self.display_edit.setPlaceholderText('Nenhum local selecionado')

        self.pick_btn = QPushButton('Escolher no Mapa...')
        self.pick_btn.clicked.connect(self._open_picker)

        layout.addWidget(self.display_edit, 1)
        layout.addWidget(self.pick_btn)

        if allow_clear:
            self.clear_btn = QPushButton('Limpar')
            self.clear_btn.clicked.connect(self._clear)
            layout.addWidget(self.clear_btn)

    def set_code(self, code: str) -> None:
        self._code = (code or '').strip().upper()
        if not self._code:
            self.display_edit.clear()
            return
        pkg = self._pkg_provider()
        loc = pkg.locations.get(self._code) if pkg else None
        self.display_edit.setText(f'{self._code} — {loc.name}' if loc else self._code)

    def code(self) -> str:
        return self._code

    def _open_picker(self) -> None:
        pkg = self._pkg_provider()
        dlg = LocationPickerDialog(
            self._app_root,
            pkg,
            current_code=self._code,
            buildings_only=self._buildings_only,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_code:
            self.set_code(dlg.selected_code)
            if self._on_changed:
                self._on_changed(self._code)

    def _clear(self) -> None:
        self.set_code('')
        if self._on_changed:
            self._on_changed('')
