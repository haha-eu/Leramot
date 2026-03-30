"""
styles.py — Qt stylesheet strings for Leramot.

Vercel-inspired precision minimalism: dark background, sharp hierarchy,
tight spacing, no fluff.
"""

# ---- Palette ----
BG          = "#0a0a0a"
SURFACE     = "#111111"
SURFACE_UP  = "#1a1a1a"
BORDER      = "#222222"
BORDER_H    = "#333333"
TEXT_PRI    = "#ededed"
TEXT_SEC    = "#888888"
TEXT_MUTED  = "#444444"
ACCENT      = "#ffffff"
ACCENT_DIM  = "rgba(255,255,255,0.08)"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
ERROR       = "#ef4444"


MAIN_STYLE = f"""
/* ---- Root window ---- */
QWidget {{
    background-color: {BG};
    color: {TEXT_PRI};
    font-family: 'DM Sans', 'Inter', sans-serif;
    font-size: 14px;
}}

/* ---- Scroll area ---- */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_H};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ---- Labels ---- */
QLabel {{
    background: transparent;
    color: {TEXT_PRI};
}}
QLabel#sectionLabel {{
    color: #888888; /* contrast-fixed */
    font-size: 11px;
    letter-spacing: 0.08em;
    font-weight: 500;
}}
QLabel#charCount {{
    color: #555555; /* contrast-fixed */
    font-size: 12px;
}}
QLabel#wpmLabel {{
    color: #ededed; /* contrast-fixed */
    font-size: 13px;
}}
QLabel#charProgress {{
    color: #ededed; /* contrast-fixed */
    font-size: 12px;
}}
QLabel#mdIndicator {{
    color: #888888; /* contrast-fixed */
    font-size: 11px;
    letter-spacing: 0.04em;
}}
QLabel#statusLabel {{
    color: #ededed; /* contrast-fixed */
    font-size: 13px;
}}
QLabel#hintLabel {{
    color: #555555; /* contrast-fixed */
    font-size: 11px;
}}
QLabel#titleLabel {{
    color: {TEXT_PRI};
    font-size: 15px;
    font-family: 'Cal Sans', 'DM Sans', 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: 0.02em;
}}
QLabel#windowControls {{
    color: {TEXT_MUTED};
    font-size: 13px;
    letter-spacing: 0.10em;
}}

/* ---- Textarea & Input ---- */
QTextEdit#contentArea, QLineEdit#customInput {{
    background-color: {SURFACE};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 8px 12px;
    font-family: 'DM Mono', 'Consolas', 'DM Sans', monospace;
    font-size: 13px;
    line-height: 1.6;
    selection-background-color: {SURFACE_UP};
}}
QTextEdit#contentArea {{
    padding: 12px;
    border-radius: 0px;
}}
QTextEdit#contentArea:focus, QLineEdit#customInput:focus {{
    border: 1px solid {BORDER_H};
    outline: none;
}}
QLineEdit#customInput[invalid="true"] {{
    border: 1px solid {ERROR};
}}

/* ---- Slider ---- */
QSlider::groove:horizontal {{
    background: {BORDER};
    height: 2px;
    border-radius: 1px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    height: 2px;
    border-radius: 1px;
}}
QSlider::add-page:horizontal {{
    background: {BORDER};
    height: 2px;
    border-radius: 1px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    border: none;
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}

/* ---- Pill buttons (presets/delay) ---- */
QPushButton#pillButton {{
    background-color: transparent;
    color: #ededed; /* contrast-fixed */
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 400;
    min-height: 32px;
    max-height: 32px;
}}
QPushButton#pillButton:hover {{
    background-color: {SURFACE_UP};
    border-color: {BORDER_H};
    color: {TEXT_PRI};
}}
QPushButton#pillButton[selected="true"] {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: #cccccc;
    font-weight: 600;
}}
QPushButton#pillButton:pressed {{
    transform: scale(0.97);
}}

/* ---- Primary button ---- */
QPushButton#primaryButton {{
    background-color: {ACCENT};
    color: #cccccc;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    min-height: 44px;
    max-height: 44px;
    letter-spacing: 0.02em;
}}
QPushButton#primaryButton:hover {{
    background-color: #e5e5e5;
}}
QPushButton#primaryButton:pressed {{
    background-color: #d0d0d0;
}}
QPushButton#primaryButton:disabled {{
    background-color: {SURFACE_UP};
    color: {TEXT_MUTED};
}}

/* ---- Cancel button ---- */
QPushButton#cancelButton {{
    background-color: #1a1a1a; /* contrast-fixed */
    color: #ededed; /* contrast-fixed */
    border: 1px solid #333333; /* contrast-fixed */
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    min-height: 44px;
    max-height: 44px;
    letter-spacing: 0.02em;
}}
QPushButton#cancelButton:hover {{
    background-color: {SURFACE_UP};
    border-color: {BORDER_H};
    color: {TEXT_PRI};
}}
QPushButton#cancelButton:pressed {{
    background-color: {BORDER};
}}

/* ---- Progress bar ---- */
QProgressBar#progressBar {{
    background-color: {SURFACE_UP};
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
    text-align: center;
}}
QProgressBar#progressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: #1a1a1a; /* contrast-fixed */
    color: #ededed; /* contrast-fixed */
    border: 1px solid #333333; /* contrast-fixed */
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}}

/* ---- Title bar ---- */
QWidget#titleBar {{
    background-color: {BG};
    border-bottom: 1px solid {BORDER};
    min-height: 48px;
    max-height: 48px;
}}
"""

# Status dot colours (used programmatically)
DOT_WAITING = "#444444"
DOT_COUNTDOWN = WARNING
DOT_TYPING = SUCCESS
DOT_DONE = ACCENT
DOT_CANCELLED = ERROR
