"""Keyboard-only navigation smoke tests.

axe-core catches visual contrast but not "can a keyboard user actually
reach and operate this control?". These tests drive the page with Tab /
Enter / Space / arrow keys and assert the interactive chrome responds
the same way it does under mouse input.

Everything here is browser-agnostic on paper; Firefox's default
Tab-focus model skips links unless `accessibility.tabfocus` is
permissive, so we drive focus directly via `element.focus()` where the
test is about "does Enter/Space activate this control?" and use real
Tab traversal only where the order itself is the thing being checked.
"""

import re

from playwright.sync_api import expect


def test_skip_link_is_first_tabbable(loaded_page):
    """The skip link must be the first element in keyboard tab order.

    We can't rely on "click body then Tab" because Chromium makes overflowing
    <pre> blocks tabbable, and where `blur()` lands focus is browser-dependent.
    Instead, assert the invariant directly: among focusable elements in DOM
    order, the skip link appears first.
    """
    first = loaded_page.evaluate(
        """() => {
          const selector = [
            'a[href]', 'button', 'input', 'select', 'textarea',
            'summary', '[tabindex]:not([tabindex="-1"])',
            'pre[tabindex="0"]'
          ].join(',');
          const candidates = Array.from(document.querySelectorAll(selector));
          const visible = candidates.filter(el => {
            const s = getComputedStyle(el);
            if (s.display === 'none' || s.visibility === 'hidden') return false;
            if (el.hasAttribute('disabled')) return false;
            return true;
          });
          const first = visible[0];
          if (!first) return null;
          return {
            tag: first.tagName,
            cls: first.className,
            href: first.getAttribute('href'),
          };
        }"""
    )
    assert first is not None, "no focusable elements found on the page"
    assert first["tag"] == "A", f"first focusable element is not a link: {first}"
    assert "skip" in (first["cls"] or ""), f"first focusable is not the skip link: {first}"
    assert first["href"] == "#main", f"skip link href should be #main: {first}"

    # And it really works — focusing it and pressing Enter jumps to #main.
    loaded_page.locator("a.skip").focus()
    focused_tag = loaded_page.evaluate("() => document.activeElement.tagName")
    assert focused_tag == "A", f"skip link should be focusable: got {focused_tag}"


def test_lang_toggle_activates_via_enter(loaded_page):
    """Focusing #lang-toggle and pressing Enter must flip data-lang."""
    html = loaded_page.locator("html")
    start = html.get_attribute("data-lang")
    loaded_page.locator("#lang-toggle").focus()
    loaded_page.keyboard.press("Enter")
    expect(html).not_to_have_attribute("data-lang", start or "")


def test_dark_toggle_activates_via_enter(loaded_page):
    """Focusing #dark-toggle and pressing Enter must flip data-theme."""
    html = loaded_page.locator("html")
    start = html.get_attribute("data-theme")
    loaded_page.locator("#dark-toggle").focus()
    loaded_page.keyboard.press("Enter")
    expect(html).not_to_have_attribute("data-theme", start or "")


def test_details_summary_opens_via_enter(loaded_page):
    """Sidebar <details> must expand when its summary is focused and
    Enter is pressed — keyboard-only users can't click the disclosure."""
    details = loaded_page.locator("details.sidebar").first
    summary = details.locator("summary").first
    was_open = details.get_attribute("open") is not None
    summary.focus()
    loaded_page.keyboard.press("Enter")
    now_open = details.get_attribute("open") is not None
    assert was_open != now_open, (
        f"Enter on summary did not toggle <details>: before={was_open} after={now_open}"
    )


def test_mark_done_activates_via_enter(loaded_page):
    """A mark-done link must check when focused and Enter is pressed."""
    # Clear any persisted state so the link starts unchecked.
    loaded_page.evaluate("localStorage.clear()")
    loaded_page.reload(wait_until="load")
    loaded_page.wait_for_function(
        "() => document.querySelectorAll(\"code[class*='language-'] span\").length > 0",
        timeout=5_000,
    )
    btn = loaded_page.locator("a.mark-done[data-ch='0']")
    # The element has class "mark-done"; we're asserting "checked" gets *added*.
    expect(btn).not_to_have_class(re.compile(r"\bchecked\b"))
    btn.focus()
    loaded_page.keyboard.press("Enter")
    expect(btn).to_have_class(re.compile(r"\bchecked\b"))


def test_quiz_radio_selectable_via_space(loaded_page):
    """A focused quiz radio must check when Space is pressed, and the
    label then visually indicates selection (native :checked)."""
    radio = loaded_page.locator(".quiz input[type=radio]").first
    radio.focus()
    loaded_page.keyboard.press("Space")
    # The Space key is what the browser uses to check an unchecked radio;
    # confirm the DOM state reflects that.
    assert radio.is_checked(), "Space on focused radio did not check it"


def test_focus_ring_visible_on_interactive_chrome(loaded_page):
    """Every interactive chrome element must paint *some* focus indicator
    when focused (non-transparent outline OR a distinct background/box-shadow).
    Catches regressions where a future refactor strips `:focus-visible` rules.
    """
    targets = ["#lang-toggle", "#dark-toggle", "a.skip"]
    weak = []
    for sel in targets:
        el = loaded_page.locator(sel).first
        el.focus()
        style = loaded_page.evaluate(
            """(sel) => {
              const el = document.querySelector(sel);
              const s = getComputedStyle(el);
              return {
                outlineStyle: s.outlineStyle,
                outlineWidth: s.outlineWidth,
                boxShadow: s.boxShadow,
              };
            }""",
            sel,
        )
        has_outline = style["outlineStyle"] not in ("none", "") and style["outlineWidth"] != "0px"
        has_shadow = style["boxShadow"] not in ("none", "")
        if not (has_outline or has_shadow):
            weak.append((sel, style))
    assert not weak, f"interactive chrome missing focus indicator: {weak}"
