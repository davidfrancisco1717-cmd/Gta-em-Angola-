from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.models import StoryPackage
from .map_picker import LocationPickerDialog


class RichTextLineWidget(QWidget):
    """Campo de texto com atalhos para negrito/itálico/sublinhado e inserção de [Local], [ITEM-id] e [Personagem]."""

    def __init__(
        self,
        app_root: Path,
        pkg_provider: Callable[[], StoryPackage | None],
        placeholder: str = '',
        on_changed: Callable[[str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._app_root = app_root
        self._pkg_provider = pkg_provider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.edit = QLineEdit()
        if placeholder:
            self.edit.setPlaceholderText(placeholder)
        if on_changed:
            self.edit.textChanged.connect(on_changed)

        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(4)

        for label, prefix, suffix, tip in (
            ('B', '**', '**', 'Negrito (**texto**)'),
            ('I', '*', '*', 'Itálico (*texto*)'),
            ('U', '__', '__', 'Sublinhado (__texto__)'),
        ):
            btn = QPushButton(label)
            btn.setFixedWidth(28)
            btn.setToolTip(tip)
            btn.setStyleSheet('padding: 3px 6px; font-size: 11px;')
            btn.clicked.connect(lambda _=False, p=prefix, s=suffix: self._wrap_selection(p, s))
            bar.addWidget(btn)

        for label, cb, tip in (
            ('+ Local', self._insert_location, 'Escolher local no mapa e inserir [CODIGO]'),
            ('+ Item', self._insert_item, 'Inserir [ITEM-id]'),
            ('+ Personagem', self._insert_character, 'Inserir [Nome]'),
        ):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.setStyleSheet('padding: 3px 8px; font-size: 11px;')
            btn.clicked.connect(cb)
            bar.addWidget(btn)

        bar.addStretch(1)
        layout.addWidget(self.edit)
        layout.addLayout(bar)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, value: str) -> None:  # noqa: N802
        self.edit.setText(value or '')

    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        cur = self.edit.text()
        sel = self.edit.selectedText()
        if sel:
            start = self.edit.selectionStart()
            end = start + len(sel)
            self.edit.setText(cur[:start] + prefix + sel + suffix + cur[end:])
            self.edit.setCursorPosition(end + len(prefix) + len(suffix))
        else:
            pos = self.edit.cursorPosition()
            self.edit.setText(cur[:pos] + prefix + suffix + cur[pos:])
            self.edit.setCursorPosition(pos + len(prefix))
        self.edit.setFocus()

    def _insert_token(self, token: str) -> None:
        cur = self.edit.text()
        pos = self.edit.cursorPosition()
        self.edit.setText(cur[:pos] + token + cur[pos:])
        self.edit.setCursorPosition(pos + len(token))
        self.edit.setFocus()

    def _insert_location(self) -> None:
        pkg = self._pkg_provider()
        dlg = LocationPickerDialog(self._app_root, pkg, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_code:
            self._insert_token(f'[{dlg.selected_code}]')

    def _insert_item(self) -> None:
        pkg = self._pkg_provider()
        if not pkg or not pkg.items:
            return
        choices = [f'{it.name} ({iid})' for iid, it in pkg.items.items()]
        ids = list(pkg.items.keys())
        chosen, ok = QInputDialog.getItem(self, 'Inserir Item', 'Selecione o item:', choices, 0, False)
        if ok and chosen in choices:
            iid = ids[choices.index(chosen)]
            self._insert_token(f'[ITEM-{iid}]')

    def _insert_character(self) -> None:
        pkg = self._pkg_provider()
        if not pkg or not pkg.characters:
            return
        choices = [f'{c.name} ({cid})' for cid, c in pkg.characters.items()]
        names = [c.name or cid for cid, c in pkg.characters.items()]
        chosen, ok = QInputDialog.getItem(self, 'Inserir Personagem', 'Selecione o personagem:', choices, 0, False)
        if ok and chosen in choices:
            cname = names[choices.index(chosen)]
            self._insert_token(f'[{cname}]')
