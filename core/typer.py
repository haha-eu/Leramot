"""
typer.py — QThread-based human typing engine.

Handles:
  - Countdown with always-on-top window behaviour
  - Per-character delay with log-normal distribution
  - Typo injection, continuation, backspace correction, re-correction
  - Punctuation & paragraph pauses
  - Burst digraph typing
  - Random mid-sentence thinking pauses
  - Unicode via pynput keyboard controller
  - Esc global hotkey to cancel
  - Thread-safe signals to update UI
"""

import threading
import time
import random

from PyQt6.QtCore import QThread, pyqtSignal

from core import timing

try:
    from pynput.keyboard import Controller as KeyboardController, Key, Listener as KeyListener, GlobalHotKeys
    _PYNPUT = True
except ImportError:
    _PYNPUT = False

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False


class TypingWorkerV3(QThread):
    """
    Overhauled worker with:
      - Global emergency stop (Ctrl+Shift+F4)
      - Focus-based pause/resume
      - Fatigue-based mistake trigger
      - Multi-layered mistake types
      - Rhythm variations (bursts/stretches)
    """

    progress = pyqtSignal(int, int)
    status_update = pyqtSignal(str)
    countdown_tick = pyqtSignal(int)
    finished_ok = pyqtSignal()
    cancelled = pyqtSignal()
    paused_status = pyqtSignal(bool)

    def __init__(self, text: str, duration_s: float, delay_s: float, parent=None):
        super().__init__(parent)
        self._text = text
        self._duration_s = duration_s
        self._delay_s = delay_s
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # If set, typing pauses
        self._keyboard: KeyboardController | None = None
        self._hotkeys = None
        
        # Engines
        self._rhythm = timing.RhythmEngine()
        self._fatigue = timing.FatigueEngine()

    def stop(self):
        self._stop_event.set()
        self._pause_event.clear()

    def set_paused(self, paused: bool):
        if paused:
            self._pause_event.set()
        else:
            self._pause_event.clear()

    def run(self):
        self._setup_keyboard()
        self._setup_global_hotkeys()

        try:
            # --- Countdown phase ---
            self.status_update.emit("countdown")
            total_delay = int(self._delay_s)
            for remaining in range(total_delay, 0, -1):
                if self._stop_event.is_set():
                    self.cancelled.emit()
                    return
                self.countdown_tick.emit(remaining)
                time.sleep(1.0)

            if self._stop_event.is_set():
                self.cancelled.emit()
                return

            self.status_update.emit("release_focus")
            time.sleep(0.15)

            # --- Typing phase ---
            self.status_update.emit("typing")
            self._run_typing()

        finally:
            self._teardown_global_hotkeys()

    def _setup_keyboard(self):
        if _PYNPUT:
            self._keyboard = KeyboardController()

    def _setup_global_hotkeys(self):
        if not _PYNPUT: return
        self._last_end_tap = 0.0

        def on_press(key):
            try:
                if key == Key.end:
                    now = time.time()
                    if now - self._last_end_tap < 0.4:
                        self.stop()
                    self._last_end_tap = now
            except:
                pass

        try:
            self._hotkeys = KeyListener(on_press=on_press)
            self._hotkeys.start()
        except Exception:
            self._hotkeys = None

    def _teardown_global_hotkeys(self):
        if self._hotkeys:
            self._hotkeys.stop()

    def _type_char(self, char: str):
        if self._keyboard:
            try: self._keyboard.type(char); return
            except: pass
        if _PYAUTOGUI:
            try: pyautogui.typewrite(char, interval=0); return
            except: pass

    def _press_backspace(self):
        if self._keyboard:
            try:
                self._keyboard.press(Key.backspace)
                self._keyboard.release(Key.backspace)
                return
            except: pass
        if _PYAUTOGUI: pyautogui.press('backspace')

    def _sleep_interruptible(self, seconds: float):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._stop_event.is_set(): return
            
            # Check pause
            if self._pause_event.is_set():
                self.paused_status.emit(True)
                while self._pause_event.is_set():
                    if self._stop_event.is_set(): return
                    time.sleep(0.05)
                self.paused_status.emit(False)
                
            remaining = end - time.monotonic()
            time.sleep(min(0.02, remaining))

    def _run_typing(self):
        text = self._text
        total = len(text)
        typed_count = 0
        i = 0

        while i < len(text):
            if self._stop_event.is_set():
                self.cancelled.emit()
                return

            char = text[i]
            prev_char = text[i - 1] if i > 0 else ""
            next_char = text[i + 1] if i + 1 < len(text) else ""

            # Update rhythm and fatigue
            r_mult = self._rhythm.update()
            
            # Paragraphs
            if char == '\n':
                delay = timing.char_delay(char, total, self._duration_s, prev_char, next_char, r_mult)
                self._sleep_interruptible(delay)
                self._type_char('\n')
                typed_count += 1
                self.progress.emit(typed_count, total)
                i += 1
                if i < len(text) and text[i] == '\n':
                    self._sleep_interruptible(timing.paragraph_pause())
                continue

            # Mistake trigger
            if self._fatigue.update() and char.isprintable():
                typed_count, extra_advance = self._do_typo_v3(
                    text, i, typed_count, total, prev_char, r_mult
                )
                i += 1 + extra_advance
                continue

            # Normal char
            delay = timing.char_delay(char, total, self._duration_s, prev_char, next_char, r_mult)
            self._sleep_interruptible(delay)
            if self._stop_event.is_set():
                self.cancelled.emit()
                return

            self._type_char(char)
            typed_count += 1
            self.progress.emit(typed_count, total)
            i += 1

            # Pauses
            self._sleep_interruptible(timing.pause_after_char(char))
            if random.random() < 0.005:  # rare thinking pause
                self._sleep_interruptible(timing.thinking_pause())

        self.finished_ok.emit()

    def _do_typo_v3(
        self, text: str, index: int, typed_count: int, total: int, prev_char: str, r_mult: float
    ) -> tuple[int, int]:
        m_type = timing.get_mistake_type()
        char = text[index]
        
        # 1. Type the typo
        typo_char = timing.generate_typo(char, m_type)
        delay = timing.char_delay(char, total, self._duration_s, prev_char, rhythm_mult=r_mult)
        self._sleep_interruptible(delay)
        if self._stop_event.is_set(): return typed_count, 0

        # Handle transposition/double_tap etc specially? No, timing.generate_typo handles.
        if m_type == 'transposition' and index + 1 < len(text):
            self._type_char(text[index+1])
            self._sleep_interruptible(0.04)
            self._type_char(char)
            typed_count += 2
        elif m_type == 'omission':
            # Skip and noticing comes later
            typed_count += 0 
        else:
            self._type_char(typo_char)
            typed_count += 1
            if m_type == 'double_tap':
                self._sleep_interruptible(0.03)
                self._type_char(char)
                typed_count += 1

        self.progress.emit(typed_count, total)

        # 2. Continue typing (notice delay)
        n_delay = timing.notice_delay()
        cont_indices = []
        for j in range(n_delay):
            ni = index + 1 + j
            if ni >= len(text) or text[ni] == '\n': break
            c_char = text[ni]
            c_p = text[ni-1] if ni > 0 else ""
            c_delay = timing.char_delay(c_char, total, self._duration_s, c_p, rhythm_mult=r_mult)
            self._sleep_interruptible(c_delay)
            if self._stop_event.is_set(): return typed_count, 0
            self._type_char(c_char)
            typed_count += 1
            self.progress.emit(typed_count, total)
            cont_indices.append(ni)

        # 3. Notice and Backspace
        self._sleep_interruptible(random.uniform(0.1, 0.4))
        
        bs_needed = 0
        if m_type == 'transposition': bs_needed = 2 + len(cont_indices)
        elif m_type == 'double_tap': bs_needed = 2 + len(cont_indices)
        elif m_type == 'omission': bs_needed = len(cont_indices)
        else: bs_needed = 1 + len(cont_indices)

        for _ in range(bs_needed):
            # 5% chance of burst backspace
            is_bs_burst = random.random() < 0.05
            self._sleep_interruptible(timing.backspace_delay(is_bs_burst))
            if self._stop_event.is_set(): return typed_count, 0
            self._press_backspace()

        # 4. Correct re-attempt (12% error)
        if random.random() < 0.12:
            second_typo = timing.generate_typo(char, 'adjacent')
            self._sleep_interruptible(timing.char_delay(char, total, self._duration_s, rhythm_mult=r_mult))
            self._type_char(second_typo)
            self._sleep_interruptible(0.4)
            self._press_backspace()

        # 5. Final correct type
        self._sleep_interruptible(timing.char_delay(char, total, self._duration_s, rhythm_mult=r_mult))
        if self._stop_event.is_set(): return typed_count, 0
        self._type_char(char)
        typed_count += 1
        self.progress.emit(typed_count, total)

        # Micro-pause after correction
        self._sleep_interruptible(random.uniform(0.05, 0.18))

        # Re-type continuation
        for ni in cont_indices:
            c_char = text[ni]
            c_p = text[ni-1] if ni > 0 else ""
            self._sleep_interruptible(timing.char_delay(c_char, total, self._duration_s, c_p, rhythm_mult=r_mult))
            if self._stop_event.is_set(): return typed_count, len(cont_indices)
            self._type_char(c_char)
            typed_count += 1
            self.progress.emit(typed_count, total)

        return typed_count, len(cont_indices)
