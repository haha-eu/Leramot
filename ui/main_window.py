"""
main_window.py — PyQt6 MainWindow for Leramot.

Frameless, 580×720, Vercel-dark. Custom title bar, all widgets per spec.
"""

import os
import sys

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSlot, QPoint, QEvent
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QFontDatabase, QFont, QDoubleValidator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QSlider,
    QPushButton, QLabel, QProgressBar, QSizePolicy, QSpacerItem,
    QFrame, QLineEdit,
)

from ui.styles import (
    MAIN_STYLE, BG, SURFACE, BORDER, TEXT_SEC, TEXT_MUTED,
    DOT_WAITING, DOT_COUNTDOWN, DOT_TYPING, DOT_DONE, DOT_CANCELLED,
    SUCCESS, WARNING, ERROR, ACCENT, TEXT_PRI, SURFACE_UP
)
from core.typer import TypingWorkerV3
from core.markdown import convert as md_convert
from core.timing import estimated_wpm


# ---- Duration presets (seconds) ----
DURATION_PRESETS = [
    ("30s",  30),
    ("1m",   60),
    ("5m",   300),
    ("15m",  900),
]

# ---- Delay presets (seconds) ----
DELAY_PRESETS = [
    ("10s",  10),
    ("15s",  15),
    ("30s",  30),
    ("1m",   60),
]

SLIDER_MIN_S = 30
SLIDER_MAX_S = 3600  # 60 minutes


def _resource_path(relative_path: str) -> str:
    """Get absolute path — works both for dev and PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relative_path)


def load_fonts():
    """Load and register bundled fonts."""
    fonts_dir = _resource_path("assets/fonts")
    if not os.path.isdir(fonts_dir):
        return

    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            path = os.path.join(fonts_dir, fname)
            fid = QFontDatabase.addApplicationFont(path)
            if fid < 0:
                print(f"[fonts] Failed to load: {path}")


class StatusDot(QWidget):
    """A 6px coloured circle with optional pulse animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor(DOT_WAITING)
        self._opacity = 1.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = 0.0
        self._pulsing = False

    def set_color(self, hex_color: str, pulse: bool = False):
        self._color = QColor(hex_color)
        self._pulsing = pulse
        if pulse:
            self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0
        self.update()

    def _pulse_tick(self):
        import math
        self._pulse_phase += 0.15
        self._opacity = 0.45 + 0.55 * (math.sin(self._pulse_phase) * 0.5 + 0.5)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 6, 6)


class TitleBar(QWidget):
    """Custom frameless title bar with drag support."""

    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self._win = parent
        self._drag_pos: QPoint | None = None
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 16, 0)
        layout.setSpacing(0)

        # App dot
        dot = StatusDot(self)
        dot.set_color(ACCENT)
        layout.addWidget(dot)
        layout.addSpacing(10)

        # App name
        title = QLabel("Leramot", self)
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        layout.addStretch(1)

        # Window controls
        min_btn = QPushButton("−", self)
        min_btn.setFixedSize(28, 28)
        min_btn.setObjectName("wndBtn")
        min_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; "
            f"font-size: 16px; border-radius: 4px; }}"
            f"QPushButton:hover {{ background: {SURFACE_UP}; color: {TEXT_PRI}; }}"
        )
        min_btn.clicked.connect(parent.showMinimized)

        max_btn = QPushButton("□", self)
        max_btn.setFixedSize(28, 28)
        max_btn.setObjectName("wndBtn")
        max_btn.setStyleSheet(min_btn.styleSheet())
        max_btn.clicked.connect(self._toggle_maximise)

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(28, 28)
        close_btn.setObjectName("wndBtn")
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; "
            f"font-size: 13px; border-radius: 4px; }}"
            f"QPushButton:hover {{ background: #3a1010; color: #ef4444; }}"
        )
        close_btn.clicked.connect(parent.close)

        for btn in (min_btn, max_btn, close_btn):
            layout.addWidget(btn)

    def _toggle_maximise(self):
        if self._win.isMaximized():
            self._win.showNormal()
        else:
            self._win.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._win.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self._win.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self._toggle_maximise()


class MainWindow(QWidget):
    """
    Main application window — 580×720, frameless.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(580, 720)
        self.setWindowTitle("Leramot")
        self.setStyleSheet(MAIN_STYLE)

        # State
        self._worker: TypingWorkerV3 | None = None
        self._current_delay_s: int = 10 
        self._current_duration_s: int = 120 
        self._is_running = False
        self._plain_text = ""
        self._is_paused = False

        self._md_hide_timer = QTimer(self)
        self._md_hide_timer.setSingleShot(True)
        self._md_hide_timer.timeout.connect(self._hide_md_indicator)

        self._build_ui()
        self._connect_signals()
        self._update_start_button_state()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = TitleBar(self)
        root.addWidget(self._title_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; margin: 0;")
        root.addWidget(sep)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet(f"background: {BG};")
        content_layout = QVBoxLayout(scroll_widget)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(0)

        # Content section
        content_layout.addWidget(self._section_label("CONTENT"))
        content_layout.addSpacing(8)

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("contentArea")
        self._text_edit.setFixedHeight(220)
        self._text_edit.setPlaceholderText("Paste your text here…")
        self._text_edit.setAcceptRichText(False)
        content_layout.addWidget(self._text_edit)

        content_layout.addSpacing(6)

        row = QHBoxLayout()
        self._char_count_label = QLabel("0 characters")
        self._char_count_label.setObjectName("charCount")
        row.addWidget(self._char_count_label)
        row.addStretch(1)
        self._md_indicator = QLabel("Markdown detected · converted")
        self._md_indicator.setObjectName("mdIndicator")
        self._md_indicator.setVisible(False)
        row.addWidget(self._md_indicator)
        content_layout.addLayout(row)
        content_layout.addSpacing(24)

        # Duration section
        content_layout.addWidget(self._section_label("DURATION"))
        content_layout.addSpacing(8)

        dur_row = QHBoxLayout()
        self._duration_slider = QSlider(Qt.Orientation.Horizontal)
        self._duration_slider.setMinimum(SLIDER_MIN_S)
        self._duration_slider.setMaximum(SLIDER_MAX_S)
        self._duration_slider.setValue(self._current_duration_s)
        self._duration_slider.setSingleStep(10)
        self._duration_slider.setPageStep(60)
        dur_row.addWidget(self._duration_slider, 1)

        dur_row.addSpacing(12)

        self._duration_input = QLineEdit()
        self._duration_input.setObjectName("customInput")
        self._duration_input.setFixedWidth(60)
        self._duration_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._duration_input.setText("2.0")
        self._duration_input.setToolTip("Type duration in minutes (0.5 - 60)")
        dv = QDoubleValidator(0.5, 60.0, 1)
        dv.setNotation(QDoubleValidator.Notation.StandardNotation)
        self._duration_input.setValidator(dv)
        dur_row.addWidget(self._duration_input)

        self._wpm_label = QLabel("~42 WPM")
        self._wpm_label.setObjectName("wpmLabel")
        self._wpm_label.setFixedWidth(70)
        self._wpm_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        dur_row.addWidget(self._wpm_label)

        content_layout.addLayout(dur_row)
        content_layout.addSpacing(10)

        dur_pills_row = QHBoxLayout()
        dur_pills_row.setSpacing(8)
        self._dur_pills: list[QPushButton] = []
        for label, seconds in DURATION_PRESETS:
            btn = self._pill_button(label)
            btn.setProperty("preset_s", seconds)
            btn.clicked.connect(self._on_dur_pill_clicked)
            dur_pills_row.addWidget(btn)
            self._dur_pills.append(btn)
        dur_pills_row.addStretch(1)
        content_layout.addLayout(dur_pills_row)
        content_layout.addSpacing(24)

        # Start delay section
        content_layout.addWidget(self._section_label("START DELAY"))
        content_layout.addSpacing(8)

        delay_pills_row = QHBoxLayout()
        delay_pills_row.setSpacing(8)
        self._delay_pills: list[QPushButton] = []
        for label, seconds in DELAY_PRESETS:
            btn = self._pill_button(label)
            btn.setProperty("preset_s", seconds)
            btn.clicked.connect(self._on_delay_pill_clicked)
            delay_pills_row.addWidget(btn)
            self._delay_pills.append(btn)
        delay_pills_row.addStretch(1)
        content_layout.addLayout(delay_pills_row)
        content_layout.addSpacing(28)

        self._select_delay_pill(self._delay_pills[0])

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progressBar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        content_layout.addWidget(self._progress_bar)

        content_layout.addSpacing(8)
        self._char_progress_label = QLabel("0 / 0 characters")
        self._char_progress_label.setObjectName("charProgress")
        content_layout.addWidget(self._char_progress_label)
        content_layout.addSpacing(24)

        # Buttons
        self._start_btn = QPushButton("▶  Start Typing")
        self._start_btn.setObjectName("primaryButton")
        content_layout.addWidget(self._start_btn)
        content_layout.addSpacing(8)

        self._cancel_btn = QPushButton("■  Cancel")
        self._cancel_btn.setObjectName("cancelButton")
        self._cancel_btn.setVisible(False)
        content_layout.addWidget(self._cancel_btn)

        content_layout.addSpacing(20)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self._status_dot = StatusDot()
        status_row.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        self._status_label = QLabel("Waiting for input")
        self._status_label.setObjectName("statusLabel")
        status_row.addWidget(self._status_label, 1)
        content_layout.addLayout(status_row)

        content_layout.addSpacing(4)
        self._hint_label = QLabel("End (double tap) — emergency stop")
        self._hint_label.setObjectName("hintLabel")
        content_layout.addWidget(self._hint_label)

        content_layout.addStretch(1)
        root.addWidget(scroll_widget)
        self._update_wpm_label()

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        return lbl

    def _pill_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("pillButton")
        btn.setProperty("selected", "false")
        return btn

    def _connect_signals(self):
        self._text_edit.textChanged.connect(self._on_text_changed)
        self._duration_slider.valueChanged.connect(self._on_duration_changed)
        self._duration_input.textEdited.connect(self._on_duration_input_edited)
        self._start_btn.clicked.connect(self._on_start)
        self._cancel_btn.clicked.connect(self._on_cancel)

    @pyqtSlot()
    def _on_text_changed(self):
        raw = self._text_edit.toPlainText()
        if not raw:
            self._plain_text = ""
            self._char_count_label.setText("0 characters")
            self._md_indicator.setVisible(False)
            self._update_start_button_state()
            self._update_wpm_label()
            self._update_char_progress(0, 0)
            return

        plain, was_md = md_convert(raw)
        self._plain_text = plain
        count = len(plain)
        self._char_count_label.setText(f"{count:,} characters")
        if was_md:
            self._md_indicator.setVisible(True)
            self._md_hide_timer.start(2500)
        else:
            self._md_indicator.setVisible(False)

        self._update_start_button_state()
        self._update_wpm_label()
        self._update_char_progress(0, count)

    @pyqtSlot()
    def _hide_md_indicator(self):
        self._md_indicator.setVisible(False)

    @pyqtSlot(int)
    def _on_duration_changed(self, value: int):
        if not self._duration_input.hasFocus():
            self._duration_input.setText(f"{value / 60.0:.1f}")
        self._current_duration_s = value
        self._update_wpm_label()
        for btn in self._dur_pills:
            ps = btn.property("preset_s")
            btn.setProperty("selected", str(ps == value).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    @pyqtSlot(str)
    def _on_duration_input_edited(self, text: str):
        try:
            val = float(text)
            if 0.5 <= val <= 60.0:
                s = int(val * 60)
                self._duration_slider.setValue(s)
                self._duration_input.setProperty("invalid", "false")
            else:
                self._duration_input.setProperty("invalid", "true")
        except ValueError:
            self._duration_input.setProperty("invalid", "true")
        self._duration_input.style().unpolish(self._duration_input)
        self._duration_input.style().polish(self._duration_input)

    def _update_wpm_label(self):
        char_count = len(self._plain_text) if self._plain_text else 500
        wpm = estimated_wpm(char_count, self._current_duration_s)
        self._wpm_label.setText(f"~{wpm} WPM")

    def _on_dur_pill_clicked(self):
        btn = self.sender()
        seconds = btn.property("preset_s")
        self._duration_slider.setValue(seconds)

    def _on_delay_pill_clicked(self):
        self._select_delay_pill(self.sender())

    def _select_delay_pill(self, selected_btn: QPushButton):
        for btn in self._delay_pills:
            is_sel = btn is selected_btn
            btn.setProperty("selected", str(is_sel).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._current_delay_s = selected_btn.property("preset_s")

    @pyqtSlot()
    def _on_start(self):
        if not self._plain_text.strip(): return
        self._is_running = True
        self._start_btn.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._text_edit.setReadOnly(True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()

        self._worker = TypingWorkerV3(
            text=self._plain_text,
            duration_s=float(self._current_duration_s),
            delay_s=float(self._current_delay_s),
            parent=self,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.status_update.connect(self._on_status_update)
        self._worker.countdown_tick.connect(self._on_countdown_tick)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.paused_status.connect(self._on_paused_status)
        self._worker.start()

    @pyqtSlot()
    def _on_cancel(self):
        if self._worker: self._worker.stop()

    @pyqtSlot(int, int)
    def _on_progress(self, typed: int, total: int):
        if total > 0: self._progress_bar.setValue(int(typed * 100 / total))
        self._update_char_progress(typed, total)

    @pyqtSlot(str)
    def _on_status_update(self, status: str):
        if status == "countdown":
            self._status_dot.set_color(DOT_COUNTDOWN)
        elif status == "release_focus":
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
            self.lower()
        elif status == "typing":
            self._status_dot.set_color(DOT_TYPING, pulse=True)
            self._status_label.setText("Typing…")

    @pyqtSlot(int)
    def _on_countdown_tick(self, remaining: int):
        if not self._is_paused:
            self._status_label.setText(f"Starting in {remaining}s…")

    @pyqtSlot(bool)
    def _on_paused_status(self, paused: bool):
        self._is_paused = paused
        if paused:
            self._status_dot.set_color(WARNING, pulse=True)
            self._status_label.setText("Focus detected. Resuming in 1.5s...")
        else:
            self._status_dot.set_color(DOT_TYPING, pulse=True)
            self._status_label.setText("Typing…")

    @pyqtSlot()
    def _on_finished(self): self._finish_session(done=True)

    @pyqtSlot()
    def _on_cancelled(self): self._finish_session(done=False)

    def _finish_session(self, done: bool):
        self._is_running = False
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()
        self._start_btn.setVisible(True)
        self._cancel_btn.setVisible(False)
        self._text_edit.setReadOnly(False)
        if done:
            self._status_dot.set_color(DOT_DONE)
            self._status_label.setText("Done ✓")
            self._progress_bar.setValue(100)
        else:
            self._status_dot.set_color(ERROR)
            self._status_label.setText("Stopped.")
        self._worker = None

    def _update_start_button_state(self):
        has_text = bool(self._plain_text.strip())
        self._start_btn.setEnabled(has_text)
        if not has_text:
            self._status_dot.set_color(DOT_WAITING)
            self._status_label.setText("Waiting for input")

    def _update_char_progress(self, typed: int, total: int):
        self._char_progress_label.setText(f"{typed:,} / {total:,} characters")

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow() and self._is_running and self._worker:
                if self._worker.status_update: # only if typing started
                    self._worker.set_paused(True)
                    QTimer.singleShot(1500, lambda: self._worker.set_paused(False) if self._worker else None)
        super().changeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self._is_running:
            self._on_cancel()
        else:
            super().keyPressEvent(event)
