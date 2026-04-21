"""Shared fixtures for the rust-tutorial test suite."""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "rust-tutorial.html"


@pytest.fixture(scope="session")
def html_file() -> Path:
    assert HTML.exists(), f"missing tutorial HTML at {HTML}"
    return HTML


@pytest.fixture(scope="session")
def base_url(html_file: Path) -> str:
    return f"file://{html_file}"


@pytest.fixture
def loaded_page(page, base_url):
    """A page that has navigated to the tutorial and fired `load`."""
    page.goto(base_url, wait_until="load")
    # Give Prism + the inline tokenizer a tick to finish without using a
    # bare sleep — wait until at least one code block has been tokenised.
    page.wait_for_function(
        "() => document.querySelectorAll(\"code[class*='language-'] span\").length > 0",
        timeout=5_000,
    )
    return page


@pytest.fixture
def anchors_and_ids(loaded_page):
    """(list of href="#foo" values, set of [id] values on the page)."""
    anchors = loaded_page.eval_on_selector_all(
        "a[href^='#']", "els => els.map(a => a.getAttribute('href'))"
    )
    ids = set(
        loaded_page.eval_on_selector_all("[id]", "els => els.map(e => e.id)")
    )
    return anchors, ids
