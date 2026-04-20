#!/usr/bin/env python3
"""Extract Rust samples from tutorial sidebars to standalone .rs files,
one per <pre class="sample"> ... </pre> block. Usage:

    python3 scripts/extract_samples.py rust-tutorial.html /tmp/samples
"""

import html
import os
import re
import sys


SAMPLE_RE = re.compile(
    r'<pre[^>]*class="[^"]*\bsample\b[^"]*"[^>]*>'
    r'(?:\s*<code[^>]*>)?'
    r'(?P<body>.*?)'
    r'(?:</code>)?\s*</pre>',
    re.DOTALL,
)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: extract_samples.py <input.html> <out-dir>", file=sys.stderr)
        return 2
    in_path, out_dir = argv[1], argv[2]
    os.makedirs(out_dir, exist_ok=True)
    with open(in_path, encoding="utf-8") as fh:
        src = fh.read()
    count = 0
    for match in SAMPLE_RE.finditer(src):
        body = html.unescape(match.group("body"))
        body = body.strip() + "\n"
        out_path = os.path.join(out_dir, f"sample_{count:03d}.rs")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(body)
        count += 1
    print(f"wrote {count} samples to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
