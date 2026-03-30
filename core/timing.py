"""
timing.py — Per-character delay calculation, pause logic, and burst typing detection.

Uses a log-normal distribution for inter-key delays to produce human-like
speed variation. Adjusts base delay per character type, injects punctuation
and paragraph pauses, and detects common digraphs for burst typing.
"""

import math
import random


# Common English digraphs that humans tend to roll over quickly
BURST_DIGRAPHS = frozenset([
    "th", "he", "in", "er", "an", "re", "on", "en", "at", "es",
    "ed", "te", "ti", "or", "hi", "to", "it", "is", "ha", "nd",
    "ou", "ea", "ng", "al", "de", "se", "le", "sa", "si", "ar",
    "ve", "ra", "ld", "ur", "with", "the", "ing",
])

# Characters that are statistically common and typed faster
FAST_CHARS = frozenset("etaoinshrdlu ,")

# Characters that require more cognitive effort
SLOW_CHARS = frozenset("QZXJKVBWPY!@#$%^&*()_+-=[]{}|;:\"<>?/\\~`")

# Adjacent keyboard keys for realistic typo generation (QWERTY layout)
ADJACENT_KEYS: dict[str, str] = {
    'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'ersfxc', 'e': 'wrsdf',
    'f': 'rtdgvc', 'g': 'tyfhbv', 'h': 'yugjbn', 'i': 'uojkl', 'j': 'uihknm',
    'k': 'iojlm,', 'l': 'opk;,.', 'm': 'jkn,', 'n': 'bhjm', 'o': 'iklp',
    'p': 'ol;[', 'q': 'wa', 'r': 'eftd', 's': 'wedxza', 't': 'ryfg',
    'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx',
    '1': '2q', '2': '13qw', '3': '24we', '4': '35er', '5': '46rt',
    '6': '57ty', '7': '68yu', '8': '79io', '9': '80op', '0': '9-p[',
    ',': 'mkl.', '.': 'l,/', ' ': ' ',
}

# Shift-key missed for uppercase (produces lowercase instead)
SHIFT_MISS: dict[str, str] = {
    c.upper(): c for c in 'abcdefghijklmnopqrstuvwxyz'
}
SHIFT_MISS.update({'!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
                   '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'})

# Phonetic substitutions for common typos
PHONETIC_MAP = {
    "their": "thier", "thier": "their",
    "the": "teh", "teh": "the",
    "you": "yuo", "yuo": "you",
    "and": "adn", "adn": "and",
    "ing": "ign", "ign": "ing",
    "ment": "mnet", "mnet": "ment",
}


def _lognormal_delay(mean_ms: float, sigma: float = 0.35) -> float:
    """Return a log-normally distributed delay in seconds."""
    val = random.lognormvariate(math.log(mean_ms), sigma)
    return max(val, 15.0) / 1000.0


class RhythmEngine:
    """Manages typing rhythm variations: fast bursts and slow stretches."""
    def __init__(self):
        self.char_count = 0
        self.burst_target = random.randint(15, 40)
        self.stretch_target = random.randint(60, 120)
        self.mode = "normal"  # normal, burst, stretch
        self.mode_remaining = 0

    def update(self) -> float:
        """Update count and return current delay multiplier."""
        self.char_count += 1
        
        if self.mode == "normal":
            if self.char_count >= self.burst_target:
                self.mode = "burst"
                self.mode_remaining = random.randint(3, 8)
                self.char_count = 0
                self.burst_target = random.randint(15, 40)
            elif self.char_count >= self.stretch_target:
                self.mode = "stretch"
                self.mode_remaining = random.randint(4, 10)
                self.char_count = 0
                self.stretch_target = random.randint(60, 120)
                
        if self.mode == "burst":
            self.mode_remaining -= 1
            if self.mode_remaining <= 0: self.mode = "normal"
            return random.uniform(0.5, 0.7)  # 30-50% shorter
            
        if self.mode == "stretch":
            self.mode_remaining -= 1
            if self.mode_remaining <= 0: self.mode = "normal"
            return random.uniform(1.4, 1.8)  # 40-80% longer
            
        return 1.0


def char_delay(
    char: str,
    total_chars: int,
    total_duration_s: float,
    prev_char: str = "",
    next_char: str = "",
    rhythm_mult: float = 1.0
) -> float:
    """Compute a realistic inter-key delay for a given character."""
    if total_chars <= 0: return 0.05
    base_ms = (total_duration_s * 1000.0) / total_chars

    multiplier = rhythm_mult
    if char in FAST_CHARS: multiplier *= 0.82
    elif char in SLOW_CHARS: multiplier *= 1.35
    elif char.isupper(): multiplier *= 1.20
    elif char in '.,;:!?': multiplier *= 1.25

    if (prev_char + char).lower() in BURST_DIGRAPHS:
        multiplier *= 0.58

    mean_ms = max(20.0, min(base_ms * multiplier, 900.0))
    return _lognormal_delay(mean_ms)


def backspace_delay(is_burst: bool = False) -> float:
    """Realistic cadence between backspace presses."""
    if is_burst:
        return random.uniform(0.01, 0.05)  # 10-50ms for burst deletions
    return _lognormal_delay(75, sigma=0.25)


def pause_after_char(char: str) -> float:
    if char in ',;': return random.uniform(0.12, 0.35)
    if char in '.!?': return random.uniform(0.30, 0.75)
    return 0.0


def paragraph_pause() -> float:
    return random.uniform(0.50, 1.40)


def thinking_pause() -> float:
    return random.uniform(0.60, 2.20)


class FatigueEngine:
    """Manages mistake trigger via fatigue accumulation."""
    def __init__(self):
        self.accumulator = 0.0
        self.threshold = random.uniform(0.08, 0.20)

    def update(self) -> bool:
        """Returns True if a mistake should trigger."""
        self.accumulator += random.uniform(0.0005, 0.003)
        if self.accumulator >= self.threshold:
            # Trigger mistake, reset with carry over (0-30%)
            self.accumulator *= random.uniform(0.0, 0.3)
            self.threshold = random.uniform(0.08, 0.20)
            return True
        return False


def get_mistake_type() -> str:
    """Choose mistake type based on spec weights."""
    return random.choices(
        ['adjacent', 'transposition', 'double_tap', 'missed_shift', 'phonetic', 'omission'],
        weights=[40, 20, 15, 10, 10, 5]
    )[0]


def generate_typo(intended: str, m_type: str = 'adjacent') -> str:
    """Generate typo based on specific type."""
    lower = intended.lower()
    
    if m_type == 'adjacent':
        pool = ADJACENT_KEYS.get(lower, 'qwsz')
        return random.choice(pool)
        
    if m_type == 'double_tap':
        return intended
        
    if m_type == 'missed_shift':
        if intended.isupper(): return intended.lower()
        if intended in "!@#$%^&*()_+": return SHIFT_MISS.get(intended, intended)
        return intended.upper()
        
    return intended


def notice_delay() -> int:
    """How many extra chars before noticing mistake (geometric distribution)."""
    # Using random.choices for a simple discrete distribution approximating geometric
    return random.choices([0, 1, 2, 3, 4], weights=[40, 30, 15, 10, 5])[0]


def wpm_from_duration(text: str, duration_s: float) -> float:
    if duration_s <= 0: return 0.0
    word_count = len(text.split()) if text.strip() else len(text) / 5.0
    return round(word_count / (duration_s / 60.0), 1) if duration_s > 0 else 0.0


def estimated_wpm(char_count: int, duration_s: float) -> int:
    if duration_s <= 0 or char_count <= 0: return 0
    return max(1, round((char_count / 5.0) / (duration_s / 60.0)))
