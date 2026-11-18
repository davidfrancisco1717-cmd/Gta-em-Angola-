from __future__ import annotations

GAME_PALETTE = {
    'bg_root': '#0e1015',
    'bg_panel': '#141720',
    'bg_elevated': '#1c212e',
    'border': '#2b3245',
    'text': '#f4f5f7',
    'text_muted': '#9ca3af',
    'accent': '#f59e0b',
    'accent_hover': '#fbbf24',
    'accent_text': '#0e1015',
    'danger': '#ef4444',
    'danger_hover': '#dc2626',
    'success': '#22c55e',
}

APP_QSS = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {GAME_PALETTE['bg_root']};
    color: {GAME_PALETTE['text']};
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

QFrame#TopBar, QGroupBox {{
    background-color: {GAME_PALETTE['bg_panel']};
    border: 1px solid {GAME_PALETTE['border']};
    border-radius: 8px;
}}

QGroupBox {{
    margin-top: 10px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {GAME_PALETTE['accent']};
}}

QTabWidget::pane {{
    border: 1px solid {GAME_PALETTE['border']};
    background-color: {GAME_PALETTE['bg_panel']};
    border-radius: 8px;
    padding: 6px;
}}

QTabBar::tab {{
    background-color: {GAME_PALETTE['bg_elevated']};
    color: {GAME_PALETTE['text_muted']};
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {GAME_PALETTE['accent']};
    color: {GAME_PALETTE['accent_text']};
}}

QTabBar::tab:hover:!selected {{
    background-color: #252c3d;
    color: {GAME_PALETTE['text']};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {{
    background-color: {GAME_PALETTE['bg_elevated']};
    color: {GAME_PALETTE['text']};
    border: 1px solid {GAME_PALETTE['border']};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {GAME_PALETTE['accent']};
    selection-color: {GAME_PALETTE['accent_text']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {GAME_PALETTE['accent']};
}}

QListWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {GAME_PALETTE['accent']};
    color: {GAME_PALETTE['accent_text']};
    font-weight: 600;
}}

QPushButton {{
    background-color: {GAME_PALETTE['bg_elevated']};
    color: {GAME_PALETTE['text']};
    border: 1px solid {GAME_PALETTE['border']};
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    border-color: {GAME_PALETTE['accent']};
    background-color: #252c3d;
}}

QPushButton#PrimaryButton {{
    background-color: {GAME_PALETTE['accent']};
    color: {GAME_PALETTE['accent_text']};
    border: none;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {GAME_PALETTE['accent_hover']};
}}

QPushButton#DangerButton {{
    background-color: {GAME_PALETTE['danger']};
    color: #ffffff;
    border: none;
}}

QPushButton#DangerButton:hover {{
    background-color: {GAME_PALETTE['danger_hover']};
}}

QHeaderView::section {{
    background-color: {GAME_PALETTE['bg_panel']};
    color: {GAME_PALETTE['accent']};
    border: 1px solid {GAME_PALETTE['border']};
    padding: 5px;
    font-weight: 600;
}}

QStatusBar {{
    background-color: {GAME_PALETTE['bg_panel']};
    color: {GAME_PALETTE['text_muted']};
    border-top: 1px solid {GAME_PALETTE['border']};
}}
"""
