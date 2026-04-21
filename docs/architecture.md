# Rust + Tauri 2.0 tutorial — architectural document

This document is the authoritative specification. `AGENTS.md` and `README.md` both point here. If anything elsewhere in the repo conflicts with this file, **this file wins**.

Last verified against the repo: 2026-04-21.

---

## 1. Overview

**Goal.** Teach a beginner enough Rust to ship a small, real, native desktop app: a minimal **text-file editor built on Tauri 2.0** (code-named `fedit`). The tutorial is designed for an audience with short attention spans and a preference for learning by doing — **DAVE-aware pedagogy is a first-class constraint**, not a nice-to-have. (*DAVE* — Dopamine Attention Variability Executive Dysfunction — is how we refer throughout this document to the cluster of attention, motivation, and executive-function patterns the tutorial accommodates.) Readers start building on chapter 1 and have a running window within 10 minutes.

**Audience.** Someone who has written a little JavaScript or Python. No C/C++, no prior Rust. Comfortable on the command line. Likely to bail the moment something feels like homework.

**Non-goals.** Not a reference. No deep async beyond a single orientation sidebar, no exhaustive lifetimes treatment, no macro authoring (only a brief `macro_rules!` primer), no mobile.

**Bilingual delivery.** Every main-track paragraph, every sidebar, every checkpoint quiz ships in **English and Turkish** (`EN ↔ TR` toggle in the header). New content lands bilingual from the same commit — no catch-up sweeps. Language preference persists in `localStorage`.

## 2. Deliverables

1. **`rust-tutorial.html`** — the tutorial. One self-contained HTML file, inline CSS/JS. External resources via CDN only (Google Fonts, Prism.js from cdnjs). Bilingual EN/TR with runtime toggle.
2. **`fedit/`** — a working, buildable Tauri 2.0 project matching the end state of the tutorial. **Lives in its own GitHub repo** (`https://github.com/jihlenburg/fedit`) and is wired into this repo as a **git submodule**. Each main-track chapter that changes code is a **git tag** inside `fedit/` (`ch01`, `ch03`, …, `ch17`, currently 13 tags).
3. **`docs/architecture.md`** — this file. The authoritative spec.
4. **`README.md`** at repo root — human-facing project front door; clone-with-submodule instructions, short feature summary, link to this doc.
5. **`AGENTS.md`** at repo root — operational guidance for AI coding agents. Submodule workflow, attribution policy, verification commands.
6. **`.githooks/commit-msg`** at repo root (and mirrored inside `fedit/`) — tracked hook that rejects any commit message crediting Claude, Anthropic, or any AI assistant. Activated with `git config core.hooksPath .githooks` after cloning.
7. **`LICENSE`** at repo root and inside `fedit/` — MIT. Both are independently consumable.
8. **`scripts/`** — tutorial-validation helpers: `validate_html.py` (html.parser sweep), `extract_samples.py` (pull sidebar Rust samples into compile-checkable files).

## 3. Stack — verify current versions before writing

Web-search each of the following before generating code. If anything has moved, update this table in place and note the change at the top of the written tutorial.

| Component | Version as of this spec | Notes |
|---|---|---|
| Tauri | **2.0+**, stable since Oct 2, 2024 | `tauri = "2"` in Cargo.toml; `@tauri-apps/api` v2 on the JS side. |
| Rust edition | **2024**, stable since Rust 1.85 (Feb 2025) | `edition = "2024"` in every Cargo.toml. |
| `tauri-plugin-fs` | v2 | File read/write. |
| `tauri-plugin-dialog` | v2.x (MSRV 1.77.2) | Native open/save dialogs. |
| `tauri-plugin-store` | v2 | Persist the recent-files list as JSON. |
| `thiserror` | 1.x or 2.x | Custom error type in ch. 15. |
| `serde` / `serde_json` | 1.x | Already transitive; add explicitly when we derive on our own types. |
| Node | 18+ | Required by `create-tauri-app` and `@tauri-apps/cli`. |
| `@tauri-apps/cli` | v2 | Installed as dev dep. |
| `rand` (if used in Playground samples) | 0.9 API — `rand::rng()` / `rng.random_range(…)` | `gen` is reserved in edition 2024; old `gen_range` is invalid. |

**Tauri-v2 permissions trap.** Every plugin API the frontend calls must be allow-listed in `fedit/src-tauri/capabilities/default.json`. This is the biggest v1→v2 change and the number-one source of silent failures. The tutorial must make this explicit and audit the file whenever a new API call is added. Current allow-list (as of `ch17` / `main`): `core:default`, `dialog:allow-open`, `dialog:allow-save`, `fs:allow-read-text-file`, `fs:allow-write-text-file` (scoped), `store:default`. No more, no less.

## 4. Structure — twin-track spiral

The tutorial runs **two tracks in parallel**, visually distinct, both inside the same HTML document:

### Main track (always moving forward)

A linear sequence of short chapters, each building the next usable state of `fedit`. **Every teaching chapter ends with a visibly different app on screen.** No chapter spends more than 15 minutes of reading time. Momentum is sacred.

### Concept sidebars (opt-in, deep-dive)

For each significant Rust concept, a collapsible "⟶ Rust: &lt;concept&gt;, a closer look" panel attached to the main-track chapter that first needs it. Each sidebar:

- Explains the concept cleanly in isolation (the textbook treatment).
- Includes one or two minimal standalone examples with **"Run in Playground"** buttons.
- Can be skipped without losing the thread of the main track.
- Is linked from the place in the main track where the concept appears.
- Ends with a "⟵ back to the main track" cue.
- Carries a **"See also"** footer linking to related sidebars (added Wave C).

Sidebars default to **collapsed** so the main track reads as a compact path. A reader who skips every sidebar still finishes with a working editor and the applied knowledge. Expansion state is persisted per-sidebar in `localStorage` so a returning reader finds things as they left them.

### Why this shape

For the target audience specifically:

- **Momentum over completeness.** A running app at chapter 1 beats twelve chapters of theory.
- **Agency over linearity.** The "should I read more?" decision happens every sidebar. That decision is energizing for this audience in a way that being *told* to read more is not.
- **Dual reinforcement without fragmentation.** Each concept is seen twice — applied in the main track, isolated in the sidebar — but the applied use is primary, so the "aha" lands on a real problem.
- **The Playground never goes away.** Sidebars keep the zero-setup escape hatch available throughout.

## 5. Main-track chapter plan

Each main-track teaching chapter follows this rhythm, marked with small visual chips:

1. **Where we are** — one sentence recap + a small SVG mockup of the current `fedit` state.
2. **What we're adding** — one-sentence goal (rendered via the `.tldr` component).
3. **Do this** — the minimal diff (5–20 lines typically) with filename tabs and copy buttons.
4. **Run it** — the literal command (`npm run tauri dev`) and what to expect on screen.
5. **What just happened** — the Rust concept, named out loud, with a link to the sidebar for a deeper treatment.
6. **Try breaking it** — one compiler-error exercise. "Remove the `&` on line 14. Read the error. What's Rust telling you?"

### Shipped chapters (0–20)

0. **Install** — rustup, Node 18+, system deps per OS (webkit2gtk Linux, WebView2 Windows, Xcode CLT macOS). *No chapter structure; just a checklist.*
1. **A window in five minutes** — `npm create tauri-app@latest fedit -- --template vanilla`, `cd fedit`, `npm install`, `npm run tauri dev`. Tour the generated layout. **Sidebar link: crates, packages, editions.**
2. **Make it yours** — change the window title, the h1, the greet button text. All frontend, zero Rust.
2b. **Beautify fedit (optional CSS primer)** — six short CSS moves that turn the naked window into something you'd screenshot. CSS custom properties, flexbox, focus rings, one-attribute dark mode. **Sidebars: CSS variables; CSS themes.** Zero Rust. Doesn't count toward the Rust progress counter.
3. **Your first Rust change** — modify `greet` to return a custom message. Introduce `fn`, `&str`, `String`, `format!`. **Sidebar: `String` vs `&str`.**
4. **A new command** — add `echo(msg: String) -> String`. Wire a text input. **Sidebar: ownership and move semantics.**
5. **Read a hardcoded file** — `std::fs::read_to_string`, `Result`, `.map_err(|e| e.to_string())`, `?`. **Sidebar: `Result` and `?`.**
6. **🎉 Checkpoint — your app reads files.** Two-sentence celebration + screenshot. **Quiz covering chapters 3–5.**
7. **Open-file dialog** — add `tauri-plugin-dialog`, register it, allow-list `dialog:allow-open`, handle cancellation via `Option`. **Sidebars: `Option`; Tauri permissions model.**
8. **Display and edit** — load the file into a `<textarea>`. Mostly frontend. **Sidebar: how serde carries data across the IPC boundary.**
9. **Write a file** — `fs::write` with `&str` and `&Path`. Deliberate borrow-checker trip. **Sidebar: references and borrowing.**
10. **🎉 Checkpoint — you have a working editor.** Open, edit, save. **Quiz covering chapters 7–9.**
11. **Remember the current file** — `tauri::State<Mutex<AppState>>`. **Sidebars: shared mutable state / `Mutex`; async intro; channels; `Send` + `Sync`; smart pointers; lifetimes.**
12. **Dirty tracking** — `is_dirty: bool` on state, blocks window close when true. Methods on a struct, `&mut self`. **Sidebars: methods / `self`; testing; doctests.**
13. **Save vs Save As** — `match` on `Option<PathBuf>`. **Sidebars: `match` and pattern matching; pattern-matching depth.**
14. **🎉 Checkpoint — your editor feels real.** **Quiz covering chapters 11–13.**
15. **A real error type** — replace `Result<_, String>` with a `FeditError` enum via `thiserror`. `From<std::io::Error>`. **Sidebars: enums with data; `macro_rules!` primer; `From` / `Into` / `TryFrom`; `anyhow` vs `thiserror`.**
16. **Recent files** — `Vec<PathBuf>` persisted via `tauri-plugin-store`. `#[derive(Serialize, Deserialize)]`. **Sidebars: `Vec` and iterators; traits and derive; collections beyond `Vec`; closures; generics.**
17. **Keyboard shortcuts and the native menu** — `Ctrl/Cmd+O`, `Ctrl/Cmd+S`, `Ctrl/Cmd+Shift+S`, `Ctrl/Cmd+N`. `MenuBuilder`. **Sidebar: idioms.**
18. **🎉 Checkpoint — you built a real app.** **Quiz covering chapters 15–17.**
19. **Bundle and ship** — `npm run tauri build`. Code signing notes. Windows WebView2 runtime options. GitHub Actions workflow sketch. **Sidebar: `cfg` and feature flags.**
20. **Where next** — The Rust Book, Rustlings, `tokio`, deeper serde, `egui` / Leptos / Dioxus, the Tauri plugin ecosystem. **Sidebar: `unsafe` primer.**

That's 20 main-track chapters plus the ch2b CSS interlude. Four are checkpoints (6, 10, 14, 18); two are install/outro (0, 20). Net **14 chapters that teach Rust** — matches the `TEACHING` set in the JS. Target total main-track reading time: 2.5–3 hours, in 10–15 minute bites.

### Wave B roadmap (ch21–26, planned)

Aim: make `fedit` a *good* editor, not just a *working* one. Each chapter introduces ≤1 new concept, each adds a real git tag in `fedit/`.

| Ch | Title | Feature | New concept | Tag |
|----|-------|---------|-------------|-----|
| 21 | Line numbers that scroll in sync | Gutter tracking scroll position | DOM-bound state, `enumerate`, `split('\n').count()` | `ch21` |
| 22 | Find and replace | Modal, regex, replace-all | `regex` crate, trait objects | `ch22` |
| 23 | Tabs — more than one file | `Vec<OpenFile>`, per-tab dirty | `Vec<T>` mutation, `Option<usize>`, `swap_remove` | `ch23` |
| 24 | Settings that persist | Font size, theme — plugin-store | `#[serde(default)]`, `Default`, `Deref` | `ch24` |
| 25 | Command palette (Ctrl+Shift+P) | Fuzzy-search all commands | closures as strategies (`Box<dyn Fn()>`) | `ch25` |
| 26 | 🎉 Checkpoint — what you built in ch21–25 | Quiz + celebration | — | — |

When a Wave B chapter lands in code + tutorial, **update this section's status column** and bump the `ch17` reference in Section 12 / capabilities trap accordingly.

## 6. Concept sidebar inventory

Collapsible `<details>` panels keyed by `id="sidebar-*"`. The JS (`rust-tutorial.html`) auto-binds open-state persistence to any element whose id starts with `sidebar-`. Sidebars default to collapsed on first load.

**Currently shipped — 34 sidebars.** Organised below by arc. Every sidebar carries at least one runnable Playground example (`code[data-playground]` + `.playground-btn`) and a "See also" footer linking to related sidebars.

### Arc 1 — First window, first Rust (ch1–ch6)

1. **`sidebar-crates`** — crates, packages, and editions *(ch1)*
2. **`sidebar-cargo-toolkit`** — the Cargo toolkit: `check`, `fmt`, `clippy`, `doc` *(ch1)*
3. **`sidebar-css-variables`** — CSS custom properties for theming *(ch2b)*
4. **`sidebar-css-themes`** — one-attribute light/dark theme swap *(ch2b)*
5. **`sidebar-string-str`** — `String` vs `&str` *(ch3)*
6. **`sidebar-ownership`** — ownership and move semantics *(ch4)*
7. **`sidebar-result`** — `Result` and the `?` operator *(ch5)*

### Arc 2 — Real file I/O and the permissions model (ch7–ch10)

8. **`sidebar-permissions`** — Tauri v2 permissions model *(ch7)*
9. **`sidebar-option`** — `Option<T>` *(ch7)*
10. **`sidebar-serde`** — how serde carries data across IPC *(ch8)*
11. **`sidebar-borrow`** — references and borrowing *(ch9)*

### Arc 3 — State and methods (ch11–ch14)

12. **`sidebar-mutex`** — shared mutable state: `Mutex`, interior mutability *(ch11)*
13. **`sidebar-lifetimes`** — lifetimes you'll actually meet *(ch11)*
14. **`sidebar-smart-ptrs`** — `Box`, `Rc`, `Arc` *(ch11)*
15. **`sidebar-send-sync`** — `Send` and `Sync` marker traits *(ch11)*
16. **`sidebar-async-intro`** — `async` / `.await` orientation *(ch11)*
17. **`sidebar-channels`** — `std::sync::mpsc` and beyond *(ch11)*
18. **`sidebar-methods`** — methods, `self`, `&self`, `&mut self` *(ch12)*
19. **`sidebar-testing`** — `#[test]`, `assert_eq!`, `cargo test` *(ch12)*
20. **`sidebar-doctests`** — doc comments that run as tests *(ch12)*
21. **`sidebar-match`** — `match` and pattern matching *(ch13)*
22. **`sidebar-pattern-depth`** — `if let`, `while let`, `let else`, guards, `@` bindings *(ch13)*

### Arc 4 — Errors, collections, and shipping (ch15–ch20)

23. **`sidebar-enums`** — enums with data and custom errors *(ch15)*
24. **`sidebar-macros`** — `macro_rules!` primer *(ch15)*
25. **`sidebar-from-into`** — `From` / `Into` / `TryFrom` / `TryInto` *(ch15)*
26. **`sidebar-anyhow-vs-thiserror`** — library vs application error strategies *(ch15)*
27. **`sidebar-iter`** — `Vec` and iterators *(ch16)*
28. **`sidebar-traits`** — traits and `derive` *(ch16)*
29. **`sidebar-collections`** — `HashMap`, `HashSet`, `BTreeMap` *(ch16)*
30. **`sidebar-closures`** — `Fn`, `FnMut`, `FnOnce` *(ch16)*
31. **`sidebar-generics`** — generics and trait bounds *(ch16)*
32. **`sidebar-idioms`** — twelve idioms worth knowing *(ch17)*
33. **`sidebar-cfg-features`** — `#[cfg(...)]` and Cargo features *(ch19)*
34. **`sidebar-unsafe-primer`** — what `unsafe` actually unlocks *(ch20)*

### Sidebar shape

Each sidebar follows the same shape: (1) one-paragraph plain-English definition, (2) one or two Playground examples, (3) one "common gotcha," (4) "See also" footer, (5) "⟵ back to the main track" cue. Everything is bilingual — EN block then TR block, toggled by the header language switch.

**Adding a new sidebar:** update Section 6 (this inventory) *in the same change* that adds the sidebar to `rust-tutorial.html`. AGENTS.md explicitly forbids adding sidebars without updating this section.

## 7. DAVE-aware design principles

These apply across the whole tutorial and inform every structural decision. They are not style notes — they're requirements.

- **Start with something that works, then modify.** The reader never creates a file from a blank page. Chapter 1 scaffolds a running app. Every subsequent chapter modifies code that already runs.
- **Every teaching chapter ends visibly different.** A window opens. A button does something new. A file loads. "You should see…" is non-negotiable.
- **Chapters are short.** Target 10–15 minutes of reading. If a chapter feels long while drafting, split it.
- **Compiler errors are exercises, not failures.** "Delete this `&`. Run `cargo check`. Read the error. Can you fix it?" This turns the borrow checker from antagonist into puzzle-mate.
- **Checkpoints every 3–4 chapters.** Named celebrations of progress with a visible state snapshot. This is where quizzes live — not after every chapter.
- **Progress is visible.** A progress bar, a chapter-done checklist, and a persistent "you are here" marker in the TOC.
- **Skipping is blessed.** Sidebars are opt-in. The tutorial explicitly tells the reader, early, that skipping sidebars is a legitimate way to read it.
- **Badges reward depth.** Each teaching chapter carries an earnable badge (`BADGE_FOR_CH` in the JS). Badges are visual dopamine, not bureaucracy.
- **Momentum beats completeness.** When in doubt, cut.

## 8. Pedagogy principles (content-level)

- **Example before rule.** Every concept is shown working before it is named.
- **Name the confusion.** Before resolving `String` vs `&str`, the Tauri permissions model, ownership, or anything else beginners trip on, say out loud: "If you're coming from JS or Python, this next part feels wrong. That's normal. Here's why it works this way."
- **No premature abstraction.** The first `echo` command returns `String`, not `Result<String, FeditError>`. The custom error type arrives only when the reader has *felt* the pain of stringly-typed errors.
- **Cite the real compiler output.** When a concept is best learned by breaking something, paste the actual compiler error in a code block and read it together.
- **Error-decoder callouts** (`.error-decoder`, Wave C) translate a specific `rustc` error into plain language at its first real appearance.

## 9. Code presentation

- Every code block has a **filename tab** (`src-tauri/src/lib.rs`, `src/main.js`, `src-tauri/Cargo.toml`, `src-tauri/capabilities/default.json`, etc.).
- **Sidebars** use "Run in Playground" buttons. URL format: `https://play.rust-lang.org/?version=stable&mode=debug&edition=2024&code=<URL-ENCODED>`, target `_blank`.
- **Main-track chapters** do not use Playground buttons — that code belongs in `fedit/`. Instead, each chapter ends with the literal terminal command and the expected on-screen result.
- **Edits to existing files** are shown as **diffs** (`-`/`+` prefixes, coloured), not whole files. End of each chapter links to the full file at that git tag in the `fedit` repo on GitHub.
- Every block has a **Copy** button with visual feedback. Fallback to `document.execCommand('copy')` if Clipboard API is unavailable.
- Syntax highlighting: **Prism.js** from cdnjs with `prism-rust`, `prism-toml`, `prism-json`, `prism-javascript`, `prism-bash`, `prism-diff`.
- Inline `<code>` chips inside `.tldr`, `.trap`, `.boss-fight`, `.try-breaking`, `.compare-table`, `.callout`, `p`, and `li` use the cream chip background regardless of any `class="language-*"` Prism class. This is a specificity-boosted CSS override.
- **Compiler-error blocks** get a distinct treatment — monospace, muted red accent, labeled `rustc` in the tab position.

## 10. Visual design

Warm editorial / technical-book aesthetic. Deliberately not "AI-generated dashboard."

- **Typography** (Google Fonts): `Fraunces` display (variable, optical sizing), `IBM Plex Sans` body, `JetBrains Mono` code.
- **Palette (light)**: bg `#FAF4E8`, text `#2A1F1A`, accent `#C8441B`. Dark palette derived with equal character.
- **Dark-mode toggle** persists via `localStorage` wrapped in `try/catch` (incognito throws).
- **Texture**: low-opacity SVG noise overlay on the page background.
- **Drop cap** on each main-track chapter opener via `::first-letter`.
- **Line-height** ≥ 1.65, prose max-width ≈ 65ch.
- **Layout** — desktop: fixed left sidebar with TOC + scrollspy (`IntersectionObserver`). Mobile (≤ 768 px): sidebar collapses to a hamburger.
- **Sidebars** (the pedagogical kind) — distinct background tint, indented slightly, clear "⟶ Rust:" prefix in the summary header.
- **Checkpoint cards** — full-width coloured panel with a celebratory flourish, the chapter range recap, and the quiz inline.
- **Badge strip** in the header shows earned vs pending badges; click for a tooltip explaining what each represents.
- **Print stylesheet** — hide nav and buttons, expand all sidebars, serif body.

## 11. Interactive features

- **Scrollspy TOC** updating via `IntersectionObserver`, with sub-TOC entries for `.toc-sub` anchors.
- **Progress indicator** — dot strip in the header showing how many teaching chapters are complete. Completion stored in `localStorage` (try/catch). Denominator = size of the `TEACHING` set in the JS (14 today; grows with Wave B).
- **"Mark chapter done"** button at the end of each main-track chapter.
- **Collapsible concept sidebars** using `<details>`/`<summary>` with smooth expand. Expansion state saved to `localStorage` per-sidebar.
- **Badges** — one per teaching chapter, wired via `BADGE_FOR_CH`. Rendered in the header strip.
- **Smooth scroll** on TOC clicks.
- **Checkpoint quizzes** — multiple choice, separate radio groups per language (`name="qX"` for EN, `name="qXtr"` for TR) to avoid collisions during language toggles.
- **Copy to clipboard** on every code block with visual feedback.
- **Run in Playground** button on sidebar code blocks only.
- **Dark-mode toggle** and **EN ↔ TR toggle** in the header.

## 12. The `fedit/` repo (submodule)

- Scaffolded with `create-tauri-app`'s **vanilla** template. No React, Svelte, Vue — the tutorial's focus is Rust.
- Frontend kept to three files: `src/index.html`, `src/styles.css`, `src/main.js`.
- **Lives at `https://github.com/jihlenburg/fedit` as its own repo.** In this repo it appears as a git submodule pinned to a specific commit on `main`.
- **Cloning.** Users must `git clone --recursive …` or run `git submodule update --init` after a plain clone. The README covers both.
- **Two-commit chapter rule.** Code changes commit inside `fedit/` (with the chapter tag where applicable); rustic records the new submodule pointer in a follow-up commit. `cd fedit && git commit && git tag chNN && git push && git push --tags && cd .. && git add fedit && git commit -m "Bump fedit submodule to chNN"`.
- **Git tags** in `fedit/`: one per main-track chapter that changes code. Currently **13 tags**: `ch01`, `ch03`, `ch04`, `ch05`, `ch07`, `ch08`, `ch09`, `ch11`, `ch12`, `ch13`, `ch15`, `ch16`, `ch17`. (Chapters 2, 2b, 6, 10, 14, 18, 19, 20 do not tag — 2/2b are frontend tweaks, 6/10/14/18 are checkpoints, 19/20 are outro.) `main` of `fedit` equals `ch17` until Wave B lands.
- **LICENSE**: MIT, mirrored at rustic root and inside `fedit/` so both repos are independently consumable.
- **Commit-msg hook**: tracked at `fedit/.githooks/commit-msg`; activate after cloning with `cd fedit && git config core.hooksPath .githooks`. Rejects any attribution to Claude/Anthropic/AI assistants.
- **`.gitignore`** inside `fedit/`: `/src-tauri/target`, `/node_modules`, `/dist`.
- **`capabilities/default.json`** audited at each chapter that adds a plugin API — no over-granted permissions.

## 13. Acceptance criteria — run before declaring done

1. **HTML validity.** `python3 scripts/validate_html.py rust-tutorial.html` — zero unclosed tags, zero nesting errors.
2. **Sidebar code samples compile.** `python3 scripts/extract_samples.py rust-tutorial.html /tmp/samples && for f in /tmp/samples/*.rs; do rustc --edition 2024 --emit=metadata "$f" -o /dev/null; done`. Samples that use external crates may be validated by inspection.
3. **Main-track code matches the repo.** Every code block in the main track corresponds to a real line range in `fedit/` at the matching git tag. No fabricated snippets.
4. **`fedit` builds.** `cd fedit && cargo check --manifest-path src-tauri/Cargo.toml` must pass. `npm run tauri build --debug` where webview deps are installed.
5. **Every tagged chapter checks out cleanly.** Loop over the 13 tags and `cargo check` each (see AGENTS.md § "Verification before opening a PR").
6. **Permissions audit.** `fedit/src-tauri/capabilities/default.json` lists exactly the plugin permissions used — no more, no less.
7. **Quiz answers correct.** Re-read each of the four checkpoint quizzes in both languages; verify the "correct" option is genuinely correct and explanations are accurate.
8. **Sidebars collapse by default.** On first load, every `<details class="sidebar">` is closed. Expansion state persists across reload.
9. **Bilingual parity.** Every new block ships EN + TR in the same commit. The `EN ↔ TR` toggle swaps every new element; no orphan untranslated nodes.
10. **Playground links work.** Click three random sidebar "Run in Playground" links; they load and run.
11. **Responsive check.** At 375 px width the sidebar collapses; prose stays readable; sidebars still expand usefully.
12. **Dark mode.** Toggles, persists, no contrast failures — check sidebars, chip contrast, and checkpoint cards specifically.
13. **Progress persistence.** Mark three chapters done, reload, confirm they stay marked. Badges render on re-entry.
14. **Report back.** Final HTML size and line count, `fedit` bundle size after `tauri build`, any decisions made that weren't spelled out here.

## 14. Tone

Warm, concrete, unhurried *within* a chapter; brisk *between* them. Short paragraphs. Concrete example before abstract rule. Name the confusion. When the compiler yells, treat it as a rite of passage. Don't apologise for Rust's strictness — sell it. When celebrating a checkpoint, mean it.

## 15. Attribution policy

This repo must not credit Claude, Anthropic, or any AI assistant anywhere visible:

- **No `Co-Authored-By: Claude …` trailers** in commit messages.
- **No `🤖 Generated with …`** footers in commit messages, PR descriptions, or tracked files.
- **No AI attribution** in the tutorial prose, README, LICENSE, or docs.

A `commit-msg` hook at `.githooks/commit-msg` (tracked) rejects banned patterns locally in both the rustic repo and the `fedit/` submodule. Do not bypass with `--no-verify`; strip the offending lines and retry. After cloning, activate with `git config core.hooksPath .githooks` in each repo.

History rewrites that strip accidentally-pushed attribution are expected maintenance, not exceptional — `git filter-repo` with a message callback is the tool.

## 16. Local working notes

During active work, maintain two **untracked** files at the repo root:

- **`todo.md`** — active task list. Add items as they surface; strike or delete when done. Short bullet format is fine.
- **`logbook.md`** — session-by-session log of what changed and why. One heading per session / wave.

Both files are in `.gitignore` and must never be published. They exist so successive agent sessions can pick up context without spelunking the full transcript. If either slips into a commit, stop and remove it (including from git history) before pushing. AGENTS.md enumerates this as a non-negotiable.

## 17. Internationalization (EN ↔ TR)

- **Runtime toggle**, not build-time. One HTML file serves both languages; JS flips `.lang-en` / `.lang-tr` visibility.
- **Sibling-span pattern** for short inline labels: `<span class="lang-en">…</span><span class="lang-tr">…</span>`.
- **Separate block pattern** for paragraphs, code, and quizzes: two sibling `<div class="lang-en">` / `<div class="lang-tr">` blocks. Quizzes additionally suffix radio-group names with `tr` to avoid collisions.
- **Parity is enforced in review**, not by a linter. Every new block ships bilingual in the same commit. No "translations to follow" TODOs.
- **Language preference** is persisted in `localStorage`.
- **Header toggle** is labelled `EN ↔ TR` and sits next to the dark-mode toggle.
