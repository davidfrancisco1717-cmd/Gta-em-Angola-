from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from ..core.story_io import StoryIOError, import_asset_file


class AssetPreviewWidget(QStackedWidget):
    """Exibe preview de imagem PNG/JPG/WEBP ou SVG em tamanho fixo."""

    def __init__(self, size: int = 56, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

        self._raster = QLabel('—')
        self._raster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._raster.setStyleSheet('border: 1px solid #2b3245; border-radius: 6px; background: #0e1015;')

        self._svg = QSvgWidget()
        self._svg.setFixedSize(size, size)

        self.addWidget(self._raster)
        self.addWidget(self._svg)

    def load_file(self, file_path: Path | None) -> None:
        if not file_path or not file_path.is_file():
            self._raster.setPixmap(QPixmap())
            self._raster.setText('—')
            self.setCurrentWidget(self._raster)
            return
        if file_path.suffix.lower() == '.svg':
            self._svg.load(str(file_path))
            self.setCurrentWidget(self._svg)
            return
        pix = QPixmap(str(file_path))
        if pix.isNull():
            self._raster.setPixmap(QPixmap())
            self._raster.setText('!')
            self.setCurrentWidget(self._raster)
            return
        scaled = pix.scaled(
            self._size - 4,
            self._size - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._raster.setText('')
        self._raster.setPixmap(scaled)
        self.setCurrentWidget(self._raster)


class AssetPickerRow(QWidget):
    """Campo de caminho relativo + preview + botões Importar/Limpar."""

    def __init__(
        self,
        story_dir_provider: Callable[[], Path | None],
        subdir: str = 'assets',
        allow_clear: bool = False,
        on_changed: Callable[[str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._story_dir_provider = story_dir_provider
        self._subdir = subdir
        self._on_changed = on_changed

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.preview = AssetPreviewWidget(48)
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText('Nenhuma imagem selecionada')

        self.import_btn = QPushButton('Importar...')
        self.import_btn.clicked.connect(self._on_import)

        layout.addWidget(self.preview)
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(self.import_btn)

        if allow_clear:
            self.clear_btn = QPushButton('Limpar')
            self.clear_btn.clicked.connect(self._on_clear)
            layout.addWidget(self.clear_btn)

    def set_value(self, rel_path: str) -> None:
        self.path_edit.setText(rel_path or '')
        story_dir = self._story_dir_provider()
        full = (story_dir / rel_path) if (story_dir and rel_path) else None
        self.preview.load_file(full)

    def value(self) -> str:
        return self.path_edit.text().strip()

    def _on_import(self) -> None:
        story_dir = self._story_dir_provider()
        if not story_dir:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Selecionar imagem',
            str(story_dir),
            'Imagens (*.png *.jpg *.jpeg *.webp *.svg)',
        )
        if not file_path:
            return
        try:
            rel = import_asset_file(story_dir, Path(file_path), target_subdir=self._subdir)
        except StoryIOError as err:
            QMessageBox.warning(self, 'Imagem inválida', str(err))
            return
        self.set_value(rel)
        if self._on_changed:
            self._on_changed(rel)

    def _on_clear(self) -> None:
        self.set_value('')
        if self._on_changed:
            self._on_changed('')


class QuietHttpHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class LocalPreviewServer:
    """Servidor HTTP local sob demanda para testar a história no navegador."""

    def __init__(self, app_root: Path) -> None:
        self.app_root = app_root
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def ensure_running(self) -> int:
        if self._server is not None:
            return int(self._server.server_port)
        handler = partial(QuietHttpHandler, directory=str(self.app_root))
        self._server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return int(self._server.server_port)

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._thread = None
