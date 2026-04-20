# AGENTS.md

Operational guidance for AI coding agents working on this repository. Humans: see `README.md`.

This repo contains an interactive Rust + Tauri 2.0 tutorial (`rust-tutorial.html`) and the companion editor project it teaches (`fedit/`). The tutorial and the project are **tightly coupled** — changes to one usually require changes to the other.

---

## Authoritative spec

`rust-tutorial-architecture.md` at the repo root is the source of truth for structure, pedagogy, design, and acceptance criteria. **If anything in this file conflicts with the architecture document, the architecture document wins.** Read it before planning any non-trivial change.

## Commands

```bash
# Run the editor in dev mode (hot reload)
cd fedit && npm run tauri dev

# Build a debug binary
cd fedit && npm run tauri build --debug

# Release binary (slow)
cd fedit && npm run tauri build

# Rust-only check (fast; works without webview deps installed)
cd fedit && cargo check --manifest-path src-tauri/Cargo.toml

# Rust format + clippy
cd fedit/src-tauri && cargo fmt && cargo clippy -- -D warnings

# Extract and compile-check Rust samples from the tutorial sidebars
python3 scripts/extract_samples.py rust-tutorial.html /tmp/samples
for f in /tmp/samples/*.rs; do rustc --edition 2024 --emit=metadata "$f" -o /dev/null; done

# Validate the tutorial HTML
python3 scripts/validate_html.py rust-tutorial.html

# View the tutorial locally (any static server works)
python3 -m http.server 8000
```

## Repo layout

```
.
├── AGENTS.md                        # this file
├── README.md                        # human-facing
├── rust-tutorial-architecture.md    # authoritative spec
├── rust-tutorial.html               # the tutorial (single self-contained file)
├── scripts/                         # validation helpers
└── fedit/                           # the Tauri 2.0 editor project
    ├── src/                         # frontend (vanilla HTML/CSS/JS, 3 files)
    ├── src-tauri/                   # Rust backend
    │   ├── src/lib.rs
    │   ├── src/main.rs
    │   ├── Cargo.toml
    │   ├── tauri.conf.json
    │   └── capabilities/default.json
    └── package.json
```

## Non-negotiable invariants

These are invariants because the tutorial breaks if they drift. Do not "improve" any of them without updating the architecture doc first.

1. **Twin-track structure.** Main-track chapters are short, build `fedit` forward, and end with a visibly different app. Rust-the-language content lives in **collapsible sidebars** attached to the main track, not in inline body text. A reader who skips every sidebar must still reach the end with a working editor.
2. **Sidebars default collapsed.** On first page load, every `<details>` concept sidebar is closed. Do not auto-expand them.
3. **Main track has no Playground buttons.** That code belongs in `fedit/`. Playground buttons appear only inside sidebars.
4. **`fedit/` tags mirror the tutorial.** Every main-track chapter that changes code has a matching git tag (`ch01`, `ch03`, `ch04`, `ch05`, `ch07`, `ch08`, `ch09`, `ch11`, `ch12`, `ch13`, `ch15`, `ch16`, `ch17`). Chapters 2, 6, 10, 14, 18, 19, 20 do not tag (frontend tweaks, checkpoints, or outros). `main` equals `ch17`. If you add or renumber a chapter, update tags accordingly and audit every link in the tutorial.
5. **Every Part-2 code block corresponds to a real line range in `fedit/`** at its chapter's tag. No fabricated snippets. If the tutorial shows it, you can `git checkout ch09` and find it.
6. **Checkpoints at ch. 6, 10, 14, 18.** Quizzes live there, not in every chapter. Do not sprinkle quizzes throughout.
7. **Vanilla JS frontend.** Do not introduce React, Svelte, Vue, or any build-tool plumbing beyond what `create-tauri-app --template vanilla` produces. The tutorial's focus is Rust.
8. **Every teaching chapter has a "try breaking it" compiler-error exercise.** This is content, not filler.

## Version constraints

Hard requirements. If a user reports a version mismatch, update `rust-tutorial-architecture.md` Section 3 first, then propagate.

- Tauri: `2.x` (stable since Oct 2, 2024). Do not suggest v1 anywhere.
- Rust edition: `2024` (stable since Rust 1.85, Feb 2025). Every `Cargo.toml` has `edition = "2024"`.
- `rand` (if touched): 0.9 API — `rand::rng()` and `rng.random_range(…)`. Not `thread_rng()` / `gen_range`. `gen` is a reserved keyword in edition 2024.
- `@tauri-apps/cli`: v2.
- Node: 18+.
- `tauri-plugin-fs`, `tauri-plugin-dialog`, `tauri-plugin-store`: all v2.

## Tauri v2 permissions trap

This is the single biggest source of silent failures. Every plugin API the frontend calls must be allow-listed in `fedit/src-tauri/capabilities/default.json`. When adding or modifying a Tauri command or plugin call, audit this file in the same commit.

Currently expected permissions (as of `ch17` / `main`):

- `core:default`
- `dialog:allow-open`, `dialog:allow-save`
- `fs:allow-read-text-file`, `fs:allow-write-text-file` (scoped — not global)
- `store:default`

No more, no less. Over-granted permissions are a bug.

## Adding or editing a chapter

1. Edit `rust-tutorial-architecture.md` first if the change is structural (new chapter, renumbering, new sidebar). The architecture doc is the plan; everything else follows from it.
2. Make the code changes in `fedit/` on a feature branch. Commit, then `git tag chNN` if it's a tagged chapter.
3. Update `rust-tutorial.html`:
   - The chapter prose and diff blocks.
   - The "full file at tag" link.
   - The TOC.
   - The sidebar links if the chapter introduces a new concept.
4. Run the full verification pass (see below).
5. If a sidebar's Playground example changed, re-run `scripts/extract_samples.py` and recompile.

## Verification before opening a PR

Run all of these. None are optional.

```bash
# HTML validity
python3 scripts/validate_html.py rust-tutorial.html

# Sidebar samples compile
python3 scripts/extract_samples.py rust-tutorial.html /tmp/samples
for f in /tmp/samples/*.rs; do rustc --edition 2024 --emit=metadata "$f" -o /dev/null || echo "FAIL: $f"; done

# fedit still builds
cd fedit && cargo check --manifest-path src-tauri/Cargo.toml
cd fedit && npm run tauri build --debug  # if webview deps are installed

# Permissions didn't drift
diff <(jq -S . fedit/src-tauri/capabilities/default.json) <(jq -S . fedit/src-tauri/capabilities/default.json.expected) || true

# Every tagged chapter still checks out cleanly
for tag in ch01 ch03 ch04 ch05 ch07 ch08 ch09 ch11 ch12 ch13 ch15 ch16 ch17; do
  git -C fedit checkout "$tag" && cargo check --manifest-path fedit/src-tauri/Cargo.toml || echo "FAIL: $tag"
done
git -C fedit checkout main
```

See also the full acceptance checklist in **Section 13 of `rust-tutorial-architecture.md`**.

## Common pitfalls (ranked by how often they happen)

1. **Forgetting to allow-list a new plugin permission.** App compiles, UI loads, button does nothing, no obvious error. Always edit `capabilities/default.json` in the same commit as a new API call.
2. **Letting a chapter end without a visible change.** Re-read the chapter. If nothing looks different on screen, the chapter is not done — either add UI wiring or merge with the next chapter.
3. **Inlining a concept sidebar into main-track prose.** If a main-track paragraph starts explaining *why* Rust has ownership, stop and move it to the sidebar.
4. **Fabricating code examples.** Every Part-2 code block must be copy-pasteable from `fedit/` at the matching tag. If you can't find it in the repo, it doesn't belong in the tutorial.
5. **Using v1 Tauri APIs from memory.** The v1 → v2 migration is large. If uncertain, check `v2.tauri.app` rather than recalling from training data.
6. **`rand` 0.8 API creeping in.** `gen_range` is invalid in edition 2024. Use `random_range`.
7. **Auto-expanding sidebars.** Sidebars are opt-in by design. Do not open them on page load regardless of the user's browser state.
8. **Sneaking a framework into the frontend.** Vanilla JS is deliberate. If you want React, the user will tell you.

## What not to do

- Do not add new sidebars beyond the 14 listed in architecture doc Section 6 without updating that document first.
- Do not add per-chapter quizzes. Quizzes live at checkpoints (ch. 6, 10, 14, 18) only.
- Do not use `localStorage` or `sessionStorage` anywhere without `try/catch` — incognito throws.
- Do not introduce bundlers, TypeScript, or any build tooling into the frontend.
- Do not silently drop a tutorial section's Playground examples when refactoring. Playground examples are the *point* of the sidebar system.
- Do not claim a task is done before running the verification commands. Report the actual outputs.

## When in doubt

Ask the user. The architecture doc is thorough but not exhaustive, and the pedagogy (ADHD-aware, momentum-first) has judgment calls the spec can't fully capture. Surfacing a question is cheaper than a PR that misses the tone.
