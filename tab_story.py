from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.models import StoryPackage
from .widgets import AssetPickerRow


class StoryMetadataTab(QWidget):
    """Aba de metadados gerais e imagens de abertura/encerramento da história."""

    def __init__(self, story_dir_provider: Callable[[], Path | None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pkg: StoryPackage | None = None

        root = QVBoxLayout(self)
        root.setSpacing(12)

        info_group = QGroupBox('Identidade da História')
        form = QFormLayout(info_group)
        form.setSpacing(10)

        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.title_edit = QLineEdit()
        self.page_title_edit = QLineEdit()
        self.subtitle_edit = QLineEdit()
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setMaximumHeight(90)

        self.splash_picker = AssetPickerRow(story_dir_provider, subdir='splash')
        self.splash_end_picker = AssetPickerRow(story_dir_provider, subdir='splash', allow_clear=True)

        form.addRow('Identificador:', self.id_edit)
        form.addRow('Título no jogo:', self.title_edit)
        form.addRow('Título da aba:', self.page_title_edit)
        form.addRow('Subtítulo:', self.subtitle_edit)
        form.addRow('Descrição:', self.desc_edit)
        form.addRow('Imagem de abertura:', self.splash_picker)
        form.addRow('Imagem de fim:', self.splash_end_picker)

        root.addWidget(info_group)
        root.addStretch(1)

        self.title_edit.textChanged.connect(self._sync)
        self.page_title_edit.textChanged.connect(self._sync)
        self.subtitle_edit.textChanged.connect(self._sync)
        self.desc_edit.textChanged.connect(self._sync)

    def load_package(self, pkg: StoryPackage | None) -> None:
        self._pkg = None
        if not pkg:
            self.id_edit.clear()
            self.title_edit.clear()
            self.page_title_edit.clear()
            self.subtitle_edit.clear()
            self.desc_edit.clear()
            self.splash_picker.set_value('')
            self.splash_end_picker.set_value('')
            return

        self.id_edit.setText(pkg.id)
        self.title_edit.setText(pkg.title)
        self.page_title_edit.setText(pkg.page_title)
        self.subtitle_edit.setText(pkg.subtitle)
        self.desc_edit.setPlainText(pkg.body_description)
        self.splash_picker.set_value(pkg.splash)
        self.splash_end_picker.set_value(pkg.splash_end)
        self._pkg = pkg

    def flush(self) -> None:
        self._sync()

    def _sync(self) -> None:
        if not self._pkg:
            return
        self._pkg.title = self.title_edit.text().strip()
        self._pkg.page_title = self.page_title_edit.text().strip()
        self._pkg.subtitle = self.subtitle_edit.text().strip()
        self._pkg.body_description = self.desc_edit.toPlainText().strip()
        self._pkg.splash = self.splash_picker.value() or 'splash/splash-start.png'
        self._pkg.splash_end = self.splash_end_picker.value() or 'splash/splash-end.png'
