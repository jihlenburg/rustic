"""Bilingual parity — for every parent with .lang-en child(ren), the same
parent must have the same number of .lang-tr children.

The sibling-span pattern in the tutorial:

    <p>
      <span class="lang-en">Hello</span>
      <span class="lang-tr">Merhaba</span>
    </p>

and the sibling-block pattern:

    <div>
      <div class="lang-en">…English paragraph…</div>
      <div class="lang-tr">…Turkish paragraph…</div>
    </div>

Both reduce to: at every parent, the count of direct children carrying
.lang-en equals the count of direct children carrying .lang-tr.

This catches the common "forgot the Turkish side" bug class — a change
that ships English-only text — without needing to load a browser.
"""

from html.parser import HTMLParser
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "rust-tutorial.html"

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class ParityChecker(HTMLParser):
    """Tracks per-parent counts of direct .lang-en / .lang-tr children.

    When a parent closes, if its immediate-child en/tr counts differ, the
    parent is recorded as a violation. Subtrees rooted at a .lang-en or
    .lang-tr element are skipped (once you're inside a language-scoped
    block, there's no need for further language markers)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # each frame: {'tag', 'line', 'en', 'tr', 'id', 'lang_scoped'}
        self.stack: list[dict] = []
        self.violations: list[dict] = []

    def _inside_lang_scope(self) -> bool:
        return any(f["lang_scoped"] for f in self.stack)

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        is_en = "lang-en" in classes
        is_tr = "lang-tr" in classes

        if self.stack and not self._inside_lang_scope():
            if is_en:
                self.stack[-1]["en"] += 1
            if is_tr:
                self.stack[-1]["tr"] += 1

        if tag not in VOID:
            self.stack.append({
                "tag": tag,
                "line": self.getpos()[0],
                "en": 0,
                "tr": 0,
                "id": attr_dict.get("id", ""),
                "class": attr_dict.get("class", ""),
                "lang_scoped": is_en or is_tr or self._inside_lang_scope(),
            })

    def handle_startendtag(self, tag: str, attrs) -> None:
        # <foo/> is self-closing — treat as start with no push.
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        if self.stack and not self._inside_lang_scope():
            if "lang-en" in classes:
                self.stack[-1]["en"] += 1
            if "lang-tr" in classes:
                self.stack[-1]["tr"] += 1

    def _close_frame(self) -> None:
        frame = self.stack.pop()
        if frame["en"] != frame["tr"]:
            self.violations.append(frame)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        # Tolerate HTML5 implicit <p>/<li> closes (same as validate_html.py).
        while self.stack and self.stack[-1]["tag"] != tag:
            top = self.stack[-1]["tag"]
            if top in {"p", "li"}:
                self._close_frame()
            else:
                return  # give up — malformed HTML, let validate_html catch it
        if self.stack and self.stack[-1]["tag"] == tag:
            self._close_frame()


def test_bilingual_parity() -> None:
    src = HTML.read_text()
    checker = ParityChecker()
    checker.feed(src)
    checker.close()
    # flush any still-open frames
    while checker.stack:
        checker._close_frame()

    if checker.violations:
        header = f"Bilingual parity violations ({len(checker.violations)}):"
        lines = [header]
        for v in checker.violations[:15]:
            sel = f"<{v['tag']}"
            if v["id"]:
                sel += f" id=\"{v['id']}\""
            if v["class"]:
                sel += f" class=\"{v['class']}\""
            sel += ">"
            lines.append(
                f"  line {v['line']}: {sel} — {v['en']} .lang-en child(ren), {v['tr']} .lang-tr"
            )
        if len(checker.violations) > 15:
            lines.append(f"  … and {len(checker.violations) - 15} more")
        pytest.fail("\n".join(lines))
