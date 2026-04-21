"""Browser-based correctness checks.

Each test navigates the tutorial in a fresh Playwright page (via the
pytest-playwright `page` fixture) and asserts one invariant. Failures are
reported per-test, not as a single aggregate — so CI surfaces them
individually and `pytest -k` lets you run one at a time.
"""

import re

from playwright.sync_api import expect


# ---------- 1. console errors on load ----------

def test_no_console_errors(page, base_url):
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on(
        "console",
        lambda m: m.type == "error" and errors.append(f"console: {m.text}"),
    )
    page.goto(base_url, wait_until="load")
    page.wait_for_load_state("networkidle")
    assert not errors, f"console errors on load: {errors}"


# ---------- 2. every href="#foo" resolves ----------

def test_anchors_resolve(anchors_and_ids):
    anchors, ids = anchors_and_ids
    missing = sorted(
        {h for h in anchors if h != "#" and h[1:] and h[1:] not in ids}
    )
    assert not missing, f"{len(missing)} broken anchor(s); first 10: {missing[:10]}"


# ---------- 3. every chapter section has a mark-done ----------

def test_every_chapter_has_mark_done(loaded_page):
    chapters = loaded_page.query_selector_all("section.chapter")
    missing = [
        c.get_attribute("data-chapter")
        for c in chapters
        if not c.query_selector("a.mark-done")
    ]
    assert not missing, f"chapters missing mark-done: {missing}"
    assert len(chapters) >= 20, f"suspiciously few chapters: {len(chapters)}"


# ---------- 4. language toggle flips data-lang ----------

def test_language_toggle(loaded_page):
    html = loaded_page.locator("html")
    start = html.get_attribute("data-lang")
    loaded_page.click("#lang-toggle")
    expect(html).not_to_have_attribute("data-lang", start or "")


# ---------- 5. dark-mode toggle flips data-theme and repaints ----------

def test_dark_mode_toggle(loaded_page):
    html = loaded_page.locator("html")
    start_theme = html.get_attribute("data-theme")
    start_bg = loaded_page.eval_on_selector(
        "body", "el => getComputedStyle(el).backgroundColor"
    )
    loaded_page.click("#dark-toggle")
    expect(html).not_to_have_attribute("data-theme", start_theme or "")
    end_bg = loaded_page.eval_on_selector(
        "body", "el => getComputedStyle(el).backgroundColor"
    )
    assert start_bg != end_bg, "body bg did not repaint after theme flip"


# ---------- 6. clicking a sub-TOC link opens the target <details> ----------

def test_subtoc_opens_sidebar(loaded_page):
    link = loaded_page.locator("ul.toc-sub a[href^='#sidebar-']").first
    target_id = link.get_attribute("href")[1:]
    link.click()
    expect(loaded_page.locator(f"#{target_id}")).to_have_attribute("open", "")


# ---------- 7. mark-done on ch4 lights the ownership badge ----------

def test_ownership_badge_lights(page, base_url):
    page.goto(base_url, wait_until="load")
    # deterministic: clear any progress from previous runs
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="load")
    page.click("a.mark-done[data-ch='4']")
    expect(page.locator(".badge[data-badge='ownership']")).to_have_class(
        re.compile(r"\bearned\b")
    )


# ---------- 8. EN and TR quiz radios never share a name ----------

def test_quiz_radio_names_dont_collide(loaded_page):
    en = set(
        loaded_page.eval_on_selector_all(
            ".quiz.lang-en input[type=radio]", "els => els.map(i => i.name)"
        )
    )
    tr = set(
        loaded_page.eval_on_selector_all(
            ".quiz.lang-tr input[type=radio]", "els => els.map(i => i.name)"
        )
    )
    overlap = sorted(en & tr)
    assert not overlap, f"EN/TR quiz radios collide on {len(overlap)} name(s): {overlap[:5]}"
    assert en and tr, f"expected quizzes in both locales (en={len(en)} tr={len(tr)})"


# ---------- 9. Prism actually highlighted code ----------

def test_prism_highlighted_code(loaded_page):
    total = loaded_page.eval_on_selector_all(
        "code[class*='language-']", "els => els.length"
    )
    tokenized = loaded_page.eval_on_selector_all(
        "code[class*='language-']",
        "els => els.filter(e => e.querySelector('span')).length",
    )
    assert tokenized > 0, f"no code block tokenised (of {total} language-* blocks)"


# ---------- 10. every sidebar is reachable from the body/TOC ----------

def test_no_orphan_sidebars(loaded_page, anchors_and_ids):
    anchors, _ = anchors_and_ids
    referenced = {h[1:] for h in anchors if h.startswith("#sidebar-")}
    sidebar_ids = loaded_page.eval_on_selector_all(
        "details.sidebar", "els => els.map(e => e.id)"
    )
    orphans = [sid for sid in sidebar_ids if sid not in referenced]
    assert not orphans, f"sidebars not linked from TOC/body: {orphans}"


# ---------- 11. sidebar 'see also' cross-links resolve to existing sidebars ----------

def test_see_also_links_resolve(loaded_page, anchors_and_ids):
    _, ids = anchors_and_ids
    see_also_targets = loaded_page.eval_on_selector_all(
        ".see-also a[href^='#'], .sidebar-footer a[href^='#']",
        "els => els.map(a => a.getAttribute('href'))",
    )
    missing = sorted({h[1:] for h in see_also_targets if h[1:] not in ids})
    assert not missing, f"cross-links to non-existent sidebars: {missing}"


# ---------- 12. Turkish İ uppercase regression ----------

def test_no_text_transform_uppercase_with_lowercase_i(loaded_page):
    """Regression test for the bug where CSS `text-transform: uppercase`
    under `<html lang="tr">` rendered English labels' lowercase `i` as `İ`
    (dotted capital).

    The fix was to pre-uppercase the content strings in ::before/::after
    and drop `text-transform: uppercase` from the affected rules. If
    anyone re-adds that property on an element containing lowercase `i`
    (and the element isn't explicitly scoped to `lang="en"`), this test
    fails in Turkish locale.
    """
    # Flip to Turkish so Turkish locale rules apply.
    loaded_page.click("#lang-toggle")
    expect(loaded_page.locator("html")).to_have_attribute("data-lang", "tr")

    suspicious = loaded_page.evaluate("""
        () => {
            const bad = [];
            for (const el of document.querySelectorAll('body *')) {
                // Skip invisible elements — hidden .lang-en wrappers under
                // Turkish locale can't exhibit the bug.
                const rect = el.getBoundingClientRect();
                if (rect.width * rect.height === 0) continue;
                const style = getComputedStyle(el);
                if (style.textTransform !== 'uppercase') continue;
                // Explicit lang="en" anywhere up the tree opts out of
                // Turkish locale uppercasing — that's the fix we want.
                if (el.closest('[lang="en"]')) continue;
                // Content inside .lang-tr wrappers is genuinely Turkish;
                // i → İ is correct capitalization there.
                if (el.closest('.lang-tr')) continue;
                const before = getComputedStyle(el, '::before').content || '';
                const after  = getComputedStyle(el, '::after').content  || '';
                const direct = [...el.childNodes]
                    .filter(n => n.nodeType === 3)
                    .map(n => n.textContent).join('');
                // Strip CSS `none` sentinel that non-existent pseudos yield.
                const pseudoText = (before === 'none' ? '' : before) +
                                   (after  === 'none' ? '' : after);
                const all = direct + pseudoText;
                if (/i/.test(all)) {
                    bad.push({
                        tag: el.tagName.toLowerCase(),
                        cls: el.className || '',
                        text: all.trim().slice(0, 60),
                    });
                    if (bad.length >= 10) break;
                }
            }
            return bad;
        }
    """)

    assert not suspicious, (
        "Turkish İ regression risk: "
        f"{len(suspicious)} element(s) have text-transform:uppercase and "
        "contain lowercase 'i' without an lang='en' opt-out. "
        "Either pre-uppercase the content (so the CSS transform is a no-op) "
        f"or add lang='en' to the element. First offenders: {suspicious}"
    )
