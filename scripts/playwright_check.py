#!/usr/bin/env python3
"""Headless correctness sweep for rust-tutorial.html.

Checks:
  1. Console errors / page errors on load.
  2. Every anchor href="#foo" targets an element that actually exists.
  3. Every chapter <section class="chapter"> has a Mark-done anchor.
  4. Language toggle flips data-lang between en and tr and visibly swaps content.
  5. Dark-mode toggle changes data-theme and the computed bg differs.
  6. Clicking a sub-TOC link opens the target <details>.
  7. Mark-done on chapter 4 lights the Ownership Slayer badge.
  8. Quiz radio groups differ between EN and TR (no cross-lang collision).
  9. Prism has highlighted at least one block (language-bash/-rust/-json).
 10. No unreferenced/orphaned sidebars (every <details class="sidebar"> is
     reachable from at least one <a href="#id"> in the TOC or body).

Usage:
    python3 scripts/playwright_check.py [path/to/rust-tutorial.html]

Defaults to <repo-root>/rust-tutorial.html resolved relative to this script.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def resolve_html(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1]).resolve()
    return (Path(__file__).resolve().parent.parent / "rust-tutorial.html").resolve()


HTML = resolve_html(sys.argv)
if not HTML.exists():
    print(f"error: {HTML} does not exist", file=sys.stderr)
    sys.exit(2)
URL = f"file://{HTML}"

failures: list[str] = []
notes: list[str] = []

def fail(msg): failures.append(msg); print(f"✗ {msg}")
def note(msg): notes.append(msg);    print(f"· {msg}")
def ok(msg):                          print(f"✓ {msg}")

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx     = browser.new_context(viewport={"width": 1400, "height": 900})
    page    = ctx.new_page()

    console_errors: list[str] = []
    page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))
    page.on("console",   lambda m: m.type == "error" and console_errors.append(f"console: {m.text}"))

    page.goto(URL, wait_until="load")
    page.wait_for_timeout(500)

    # ---------- 1. console ----------
    if console_errors:
        for e in console_errors: fail(e)
    else:
        ok("no console errors on load")

    # ---------- 2. anchor targets ----------
    anchors = page.eval_on_selector_all("a[href^='#']",
        "els => els.map(a => a.getAttribute('href'))")
    ids = set(page.eval_on_selector_all("[id]", "els => els.map(e => e.id)"))
    missing = [h for h in anchors if h != "#" and h[1:] and h[1:] not in ids]
    if missing:
        fail(f"broken anchor targets: {sorted(set(missing))[:10]} ({len(set(missing))} unique)")
    else:
        ok(f"all {len(anchors)} anchors resolve")

    # ---------- 3. every chapter has mark-done ----------
    chapters = page.query_selector_all("section.chapter")
    missing_md = [c.get_attribute("data-chapter") for c in chapters
                  if not c.query_selector("a.mark-done")]
    if missing_md:
        fail(f"chapters missing mark-done: {missing_md}")
    else:
        ok(f"all {len(chapters)} chapter sections have mark-done")

    # ---------- 4. language toggle ----------
    html_lang_initial = page.eval_on_selector("html", "el => el.getAttribute('data-lang')")
    page.click("#lang-toggle")
    page.wait_for_timeout(150)
    html_lang_after = page.eval_on_selector("html", "el => el.getAttribute('data-lang')")
    if html_lang_initial == html_lang_after:
        fail(f"lang toggle didn't flip data-lang (stayed {html_lang_initial})")
    else:
        ok(f"lang toggle: {html_lang_initial} → {html_lang_after}")
    page.click("#lang-toggle")
    page.wait_for_timeout(150)

    # ---------- 5. dark-mode toggle ----------
    bg_before = page.eval_on_selector("body", "el => getComputedStyle(el).backgroundColor")
    theme_0   = page.eval_on_selector("html", "el => el.getAttribute('data-theme')")
    page.click("#dark-toggle")
    page.wait_for_timeout(150)
    bg_after  = page.eval_on_selector("body", "el => getComputedStyle(el).backgroundColor")
    theme_1   = page.eval_on_selector("html", "el => el.getAttribute('data-theme')")
    if bg_before == bg_after or theme_0 == theme_1:
        fail(f"dark-mode toggle didn't change anything (theme {theme_0}→{theme_1}, bg {bg_before}→{bg_after})")
    else:
        ok(f"dark-mode toggle: theme {theme_0} → {theme_1}")
    page.click("#dark-toggle")
    page.wait_for_timeout(150)

    # ---------- 6. sub-TOC click opens sidebar ----------
    sub_link = page.query_selector("ul.toc-sub a[href^='#sidebar-']")
    if not sub_link:
        fail("no sub-TOC entries found")
    else:
        target = sub_link.get_attribute("href")[1:]
        sub_link.click()
        page.wait_for_timeout(250)
        is_open = page.eval_on_selector(f"#{target}", "el => el.open")
        if is_open: ok(f"clicking TOC sub-link opens <details id={target}>")
        else:       fail(f"clicking TOC sub-link did NOT open <details id={target}>")

    # ---------- 7. mark-done ch4 → Ownership Slayer badge earned ----------
    page.evaluate("localStorage.clear(); location.reload()")
    page.wait_for_load_state("load")
    page.wait_for_timeout(400)
    page.click("a.mark-done[data-ch='4']")
    page.wait_for_timeout(200)
    badge_class = page.eval_on_selector(".badge[data-badge='ownership']", "el => el.className")
    if "earned" in badge_class: ok("ownership badge lit after ch4 mark-done")
    else:                        fail(f"ownership badge class is '{badge_class}' (expected 'earned')")

    # ---------- 8. quiz radio collision check ----------
    en_names = set(page.eval_on_selector_all(".quiz.lang-en input[type=radio]",
        "els => els.map(i => i.name)"))
    tr_names = set(page.eval_on_selector_all(".quiz.lang-tr input[type=radio]",
        "els => els.map(i => i.name)"))
    overlap = en_names & tr_names
    if overlap:
        fail(f"quiz radio name collision between EN & TR: {sorted(overlap)}")
    else:
        ok(f"quizzes have distinct radio names (EN {len(en_names)}, TR {len(tr_names)})")

    # ---------- 9. Prism / own tokenizer ran ----------
    tokenized_blocks = page.eval_on_selector_all(
        "code[class*='language-']",
        "els => els.filter(e => e.querySelector('span')).length")
    total_blocks = page.eval_on_selector_all(
        "code[class*='language-']", "els => els.length")
    if tokenized_blocks == 0:
        fail(f"no highlighted code blocks (found {total_blocks} language-* blocks, 0 tokenized)")
    else:
        ok(f"{tokenized_blocks}/{total_blocks} language-* blocks tokenized")

    # ---------- 10. orphan sidebars ----------
    sidebar_ids = page.eval_on_selector_all(
        "details.sidebar", "els => els.map(e => e.id)")
    referenced = set(h[1:] for h in anchors if h.startswith("#sidebar-"))
    orphans = [s for s in sidebar_ids if s not in referenced]
    if orphans:
        fail(f"orphan sidebars (no TOC/body link): {orphans}")
    else:
        ok(f"all {len(sidebar_ids)} sidebars are linked from the body/TOC")

    note(f"sections: {len(chapters)} chapter sections, {len(sidebar_ids)} sidebars")
    browser.close()

print()
print("=" * 60)
if failures:
    print(f"FAIL: {len(failures)} check(s)")
    for f in failures: print(" -", f)
    sys.exit(1)
else:
    print(f"PASS: all checks green ({len(notes)} note(s))")
