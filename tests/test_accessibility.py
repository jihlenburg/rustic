"""Run axe-core against the rendered tutorial and fail on new violations.

The baseline allowlist captures violations that exist today; CI fails on
anything new. Tighten the allowlist over time by removing entries once the
underlying issue is fixed.
"""

import pytest

pytest.importorskip("axe_playwright_python")

from axe_playwright_python.sync_playwright import Axe  # noqa: E402


# Rule IDs that are currently accepted (remove as they get fixed).
# Each entry should include a comment with the count as of allowlist time
# and a pointer to the issue/tracking note.
ALLOWLIST: set[str] = set()


def test_no_new_axe_violations(loaded_page):
    axe = Axe()
    # Only audit serious / critical WCAG A/AA rules; leave "best-practice"
    # advice out of the gate until we're ready for that conversation.
    results = axe.run(
        loaded_page,
        options={
            "runOnly": {
                "type": "tag",
                "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
            },
        },
    )
    offending = [
        v for v in results.response["violations"] if v["id"] not in ALLOWLIST
    ]
    if offending:
        lines = [f"axe-core found {len(offending)} unexpected violation(s):"]
        for v in offending[:10]:
            lines.append(
                f"  [{v['impact']}] {v['id']}: {v['help']} ({len(v['nodes'])} node(s))"
            )
            for n in v["nodes"][:2]:
                lines.append(f"      {n['target']}")
        pytest.fail("\n".join(lines))
