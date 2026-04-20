#!/usr/bin/env python3
"""Parse the tutorial HTML with html.parser and report unclosed or
mis-nested tags. Exits non-zero on any problem."""

import sys
from html.parser import HTMLParser

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        # <foo/> — self-closing, nothing to do.
        return

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        open_tag, open_line = self.stack[-1]
        if open_tag == tag:
            self.stack.pop()
            return
        # tolerate implicit closes of <p> and <li> which HTML5 allows
        if open_tag in {"p", "li"}:
            self.stack.pop()
            self.handle_endtag(tag)
            return
        self.errors.append(
            f"line {self.getpos()[0]}: </{tag}> closes <{open_tag}> opened on line {open_line}"
        )
        # pop to try to recover
        self.stack.pop()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_html.py <file.html>", file=sys.stderr)
        return 2
    path = argv[1]
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    checker = Checker()
    checker.feed(src)
    checker.close()
    if checker.stack:
        for tag, line in checker.stack:
            checker.errors.append(f"line {line}: <{tag}> was never closed")
    if checker.errors:
        for err in checker.errors:
            print(err)
        return 1
    print(f"{path}: OK ({len(src)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
