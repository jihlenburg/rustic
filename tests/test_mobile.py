"""Mobile-viewport smoke tests.

Loads the tutorial in an iPhone 13 Mini emulation context (375×812, dpr 3)
and asserts the fundamentals: no horizontal overflow, the language and
theme toggles are reachable, chapters render within the viewport.

Firefox is skipped: Playwright's Firefox backend doesn't support the
`isMobile` flag that device descriptors set, and device emulation is
explicitly a Chromium/WebKit feature. Mobile parity on Firefox is better
covered by real-device testing, not emulation.
"""

import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def _skip_on_firefox(browser_name):
    if browser_name == "firefox":
        pytest.skip("Firefox does not support Playwright device emulation (isMobile)")


def test_no_horizontal_overflow(mobile_page):
    """The body must not be wider than the viewport on mobile."""
    result = mobile_page.evaluate(
        """() => {
          const vp = window.innerWidth;
          const scroll = document.documentElement.scrollWidth;
          if (scroll <= vp + 1) return {scroll, client: vp, offenders: []};
          // Find the outermost elements whose right edge exceeds the viewport.
          const offenders = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.right > vp + 1 && r.width > 0) {
              // Keep only if no ancestor already clips (overflow-x hidden/auto/scroll).
              let clipped = false;
              for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
                const ox = getComputedStyle(p).overflowX;
                if (ox === 'hidden' || ox === 'auto' || ox === 'scroll') { clipped = true; break; }
              }
              if (clipped) continue;
              const seg = el.tagName.toLowerCase() +
                          (el.id ? '#'+el.id : '') +
                          (el.className && typeof el.className === 'string'
                            ? '.'+el.className.trim().split(/\\s+/).join('.') : '');
              offenders.push({seg, right: r.right, width: r.width, text: (el.textContent||'').trim().slice(0, 80)});
              if (offenders.length >= 5) break;
            }
          }
          return {scroll, client: vp, offenders};
        }"""
    )
    assert result["scroll"] <= result["client"] + 1, (
        f"horizontal overflow on mobile: scrollWidth={result['scroll']} vs innerWidth={result['client']}\n"
        f"  offenders: {result['offenders']}"
    )


def test_header_toggles_reachable(mobile_page):
    """The language and dark-mode toggles must be visible and clickable."""
    lang = mobile_page.locator("#lang-toggle")
    dark = mobile_page.locator("#dark-toggle")
    expect(lang).to_be_visible()
    expect(dark).to_be_visible()
    lang.click()
    expect(mobile_page.locator("html")).to_have_attribute("data-lang", "tr")


def test_first_chapter_fits_viewport(mobile_page):
    """No element in ch0 may visually extend past the viewport right edge.

    We check `getBoundingClientRect().right` against the viewport (the user-
    visible overflow) and ignore elements clipped by an ancestor with
    `overflow-x: hidden|auto|scroll` — scrollable code blocks legitimately
    have wider intrinsic content.
    """
    viewport_w = mobile_page.evaluate("() => window.innerWidth")
    offenders = mobile_page.evaluate(
        """(vp) => {
          const ch = document.querySelector('#ch0');
          if (!ch) return [];
          const out = [];
          for (const el of ch.querySelectorAll('*')) {
            const r = el.getBoundingClientRect();
            if (r.right <= vp + 4 || r.width === 0) continue;
            let clipped = false;
            for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
              const ox = getComputedStyle(p).overflowX;
              if (ox === 'hidden' || ox === 'auto' || ox === 'scroll') { clipped = true; break; }
            }
            if (clipped) continue;
            out.push({
              tag: el.tagName.toLowerCase(),
              classes: (typeof el.className === 'string') ? el.className : '',
              right: r.right,
              width: r.width,
              text: (el.textContent || '').trim().slice(0, 80),
            });
            if (out.length >= 5) break;
          }
          return out;
        }""",
        viewport_w,
    )
    assert not offenders, (
        f"element(s) extending past viewport ({viewport_w}px) on mobile:\n  "
        + "\n  ".join(repr(o) for o in offenders)
    )
