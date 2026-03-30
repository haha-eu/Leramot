"""
markdown.py — Markdown → plain text conversion.

Uses mistune to parse Markdown into an AST, then renders clean plain text:
  - Headers → plain text (no # symbols)
  - Bold / italic → plain text (no markers)
  - Links → link text only
  - Images → alt text only
  - Bullet lists → "- " prefixed lines
  - Numbered lists → "1. " / "2. " prefixed lines
  - Code spans → plain text
  - Fenced code blocks → indented or plain
  - Blockquotes → plain text
  - Paragraphs separated by double newlines
  - Hard line breaks preserved
"""

import re
import mistune


class PlainTextRenderer(mistune.BaseRenderer):
    """Renders Markdown AST tokens into clean plain text."""

    NAME = "plain"

    def __init__(self):
        super().__init__()
        self._list_type_stack: list[str] = []   # 'bullet' | 'ordered'
        self._list_index_stack: list[int] = []

    # ---- Inline elements ----

    def text(self, token, state):
        return token["raw"]

    def emphasis(self, token, state):
        return self.render_children(token, state)

    def strong(self, token, state):
        return self.render_children(token, state)

    def codespan(self, token, state):
        return token["raw"]

    def linebreak(self, token, state):
        return "\n"

    def softline(self, token, state):
        return " "

    def link(self, token, state):
        return self.render_children(token, state)

    def image(self, token, state):
        return token.get("attrs", {}).get("alt", "")

    def inline_html(self, token, state):
        return ""

    def raw_text(self, token, state):
        return token["raw"]

    # ---- Block elements ----

    def paragraph(self, token, state):
        children = self.render_children(token, state)
        return children.strip() + "\n\n"

    def heading(self, token, state):
        children = self.render_children(token, state)
        return children.strip() + "\n\n"

    def blank_line(self, token, state):
        return ""

    def thematic_break(self, token, state):
        return "\n"

    def block_code(self, token, state):
        code = token["raw"]
        lines = code.split("\n")
        indented = "\n".join("    " + l for l in lines)
        return indented + "\n\n"

    def block_quote(self, token, state):
        children = self.render_children(token, state)
        return children.strip() + "\n\n"

    def block_html(self, token, state):
        # Strip HTML tags
        return re.sub(r"<[^>]+>", "", token["raw"]).strip() + "\n"

    def block_error(self, token, state):
        return ""

    def list(self, token, state):
        list_type = token["attrs"].get("ordered", False)
        list_type_str = "ordered" if list_type else "bullet"
        self._list_type_stack.append(list_type_str)
        self._list_index_stack.append(token["attrs"].get("start", 1))

        result = self.render_children(token, state)

        self._list_type_stack.pop()
        self._list_index_stack.pop()

        return result + "\n"

    def list_item(self, token, state):
        if self._list_type_stack and self._list_type_stack[-1] == "ordered":
            idx = self._list_index_stack[-1]
            prefix = f"{idx}. "
            self._list_index_stack[-1] = idx + 1
        else:
            prefix = "- "

        children = self.render_children(token, state)
        # Strip leading/trailing whitespace from children, re-add newline
        body = children.strip()
        return prefix + body + "\n"

    def render_children(self, token, state):
        children = token.get("children", [])
        out = ""
        for child in children:
            out += self.render_token(child, state)
        return out

    def render_token(self, token, state):
        func = self._get_method(token["type"])
        attrs = token.get("attrs", {})
        if callable(func):
            return func(token, state)
        return ""

    def _get_method(self, name):
        return getattr(self, name, None)

    def finalize(self, data, state):
        return data


def _create_parser():
    renderer = PlainTextRenderer()
    md = mistune.create_markdown(renderer=renderer)
    return md


_parser = _create_parser()


def _looks_like_markdown(text: str) -> bool:
    """Heuristic: detect common Markdown patterns."""
    patterns = [
        r"^\s{0,3}#{1,6}\s",           # headings
        r"\*\*[^*]+\*\*",              # bold
        r"\*[^*]+\*",                  # italic
        r"^[-*+]\s",                   # bullet list
        r"^\d+\.\s",                   # numbered list
        r"`[^`]+`",                    # inline code
        r"\[.+?\]\(.+?\)",             # link
        r"^>\s",                       # blockquote
        r"```",                        # fenced code
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def _cleanup(text: str) -> str:
    """Post-process the rendered plain text."""
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def convert(text: str) -> tuple[str, bool]:
    """
    Convert Markdown to clean plain text.

    Returns:
        (plain_text, was_markdown) — was_markdown is True if MD was detected.
    """
    if not text.strip():
        return text, False

    was_markdown = _looks_like_markdown(text)

    if not was_markdown:
        return text, False

    try:
        rendered = _parser(text)
        # rendered is the accumulated string from paragraph() etc.
        plain = _cleanup(rendered)
        return plain, True
    except Exception:
        # If mistune fails for any reason, return original text
        return text, False
