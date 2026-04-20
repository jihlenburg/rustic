# Rust + Tauri 2.0 tutorial — architectural document

This document is the authoritative specification. The companion short prompt points here. If anything in the short prompt conflicts with this file, **this file wins**.

---

## 1. Overview

**Goal.** Teach a beginner enough Rust to ship a small, real, native desktop app: a minimal **text-file editor built on Tauri 2.0** (code-named `fedit`). The tutorial is designed for an audience with short attention spans and a preference for learning by doing — **ADHD-aware pedagogy is a first-class constraint**, not a nice-to-have. Readers start building on chapter 1 and have a running window within 10 minutes.

**Audience.** Someone who has written a little JavaScript or Python. No C/C++, no prior Rust. Comfortable on the command line. Likely to bail the moment something feels like homework.

**Non-goals.** Not a reference. No deep async, no lifetimes beyond the minimum, no unsafe Rust, no macro-writing, no advanced trait bounds, no frontend-framework content, no mobile.

## 2. Deliverables

1. **`rust-tutorial.html`** — the tutorial. One self-contained HTML file, inline CSS/JS. External resources via CDN only (Google Fonts, Prism.js from cdnjs).
2. **`fedit/`** — a working, buildable Tauri 2.0 project matching the end state of the tutorial. Each main-track chapter that changes code is a **git tag** (`ch01`, `ch02`, …).
3. **`README.md`** at repo root — one paragraph, how to open the tutorial, how to run `fedit`.

## 3. Stack — verify current versions before writing

Web-search each of the following before generating code. If anything has moved, update this table in place and note the change at the top of the written tutorial.

| Component | Version as of this spec | Notes |
|---|---|---|
| Tauri | **2.0+**, stable since Oct 2, 2024 | `tauri = "2"` in Cargo.toml; `@tauri-apps/api` v2 on the JS side. |
| Rust edition | **2024**, stable since Rust 1.85 (Feb 2025) | `edition = "2024"` in every Cargo.toml. |
| `tauri-plugin-fs` | v2 | File read/write. |
| `tauri-plugin-dialog` | v2.x (MSRV 1.77.2) | Native open/save dialogs. |
| `tauri-plugin-store` | v2 | Persist the recent-files list as JSON. |
| `thiserror` | 1.x or 2.x | Custom error type in ch. 12. |
| `serde` / `serde_json` | 1.x | Already transitive; add explicitly when we derive on our own types. |
| Node | 18+ | Required by `create-tauri-app` and `@tauri-apps/cli`. |
| `@tauri-apps/cli` | v2 | Installed as dev dep. |

**Tauri-v2 permissions trap.** Every plugin API the frontend calls must be allow-listed in `src-tauri/capabilities/default.json`. This is the biggest v1→v2 change and the number-one source of silent failures. The tutorial must make this explicit and audit the file whenever a new API call is added.

## 4. Structure — twin-track spiral

The tutorial runs **two tracks in parallel**, visually distinct, both inside the same HTML document:

### Main track (always moving forward)

A linear sequence of short chapters, each building the next usable state of `fedit`. **Every chapter ends with a visibly different app on screen.** No chapter spends more than 15 minutes of reading time. Momentum is sacred.

### Concept sidebars (opt-in, deep-dive)

For each significant Rust concept, a collapsible "⟶ Rust: &lt;concept&gt;, a closer look" panel attached to the main-track chapter that first needs it. Each sidebar:

- Explains the concept cleanly in isolation (the textbook treatment).
- Includes one or two minimal standalone examples with **"Run in Playground"** buttons.
- Can be skipped without losing the thread of the main track.
- Is linked from the place in the main track where the concept appears.
- Ends with "⟵ back to the main track" that returns the reader to exactly where they were.

Sidebars default to **collapsed** so the main track reads as a compact path. A reader who skips every sidebar still finishes with a working editor and the applied knowledge. A reader who opens every sidebar gets an additional ~2 hours of Rust-the-language content and the cleanest possible mental model.

### Why this shape

For the target audience specifically:

- **Momentum over completeness.** A running app at chapter 1 beats twelve chapters of theory.
- **Agency over linearity.** The "should I read more?" decision happens every sidebar. That decision is energizing for this audience in a way that being *told* to read more is not.
- **Dual reinforcement without fragmentation.** Each concept is seen twice — applied in the main track, isolated in the sidebar — but the applied use is primary, so the "aha" lands on a real problem.
- **The Playground never goes away.** Sidebars keep the zero-setup escape hatch available throughout, not just in a prefatory Part 1.

## 5. Main-track chapter plan

Each main-track chapter follows this rhythm. Call out the sections in the tutorial with small visual markers:

1. **Where we are** — one sentence recap + a small SVG mockup of the current `fedit` state.
2. **What we're adding** — one-sentence goal.
3. **Do this** — the minimal diff (5–20 lines typically) with filename tabs and copy buttons.
4. **Run it** — the literal command (`npm run tauri dev`) and what to expect on screen.
5. **What just happened** — the Rust concept, named out loud, with a link to the sidebar for a deeper treatment.
6. **Try breaking it** — one compiler-error exercise. "Remove the `&` on line 14. Read the error. What's Rust telling you?"

---

0. **Install** — rustup, Node 18+, system deps per OS (webkit2gtk Linux, WebView2 Windows, Xcode CLT macOS). Target time-to-complete: under 10 minutes. *No chapter structure; just a checklist.*
1. **A window in five minutes** — `npm create tauri-app@latest fedit -- --template vanilla`, `cd fedit`, `npm install`, `npm run tauri dev`. See the window. Click the greet button. Done. Tour the generated layout at a high level. **Sidebar link: crates, packages, editions.**
2. **Make it yours** — change the window title, the h1, the greet button text. All frontend edits, zero Rust. Intentional breather chapter that reinforces "this is yours now."
3. **Your first Rust change** — modify the existing `greet` command to return a custom message. Introduce `fn`, `&str`, `String`, `format!`. **Sidebar link: `String` vs `&str`.**
4. **A new command** — add `echo(msg: String) -> String`. Wire a text input in the UI. Demonstrates passing data across IPC. **Sidebar link: ownership and move semantics.**
5. **Read a hardcoded file** — `std::fs::read_to_string`, `Result<String, String>`, the `.map_err(|e| e.to_string())` idiom, and the `?` operator. **Sidebar link: Result and the ? operator.**
6. **🎉 Checkpoint — your app reads files.** Two-sentence celebration of progress + a screenshot of the current state. **One quiz here** covering chapters 3–5. Next arc teaser.
7. **Open-file dialog** — add `tauri-plugin-dialog`, register it, allow-list `dialog:allow-open` in `capabilities/default.json`, call `open()` from JS, pass the path to the command. Handle cancellation via `Option`. **Sidebar links: Option; permissions in Tauri v2.**
8. **Display and edit** — load the file into a `<textarea>`. Mostly frontend. **Sidebar link: how serde carries data across the IPC boundary.**
9. **Write a file** — `fs::write` with `&str` and `&Path`. Intentionally move `path` after writing to trigger a compiler error; read the error together; fix with `&`. **Sidebar link: references and borrowing.**
10. **🎉 Checkpoint — you have a working editor.** Open, edit, save. Celebrate. **Quiz covering chapters 7–9.** Next arc teaser: "but it forgets what file you have open."
11. **Remember the current file** — introduce `tauri::State<Mutex<AppState>>`. Walk through why a plain field doesn't compile and the compiler's suggestion to use `Mutex`. **Sidebar link: shared mutable state and interior mutability.**
12. **Dirty tracking** — `is_dirty: bool` on state, updated from the frontend on textarea input, blocks window close when true. Introduces methods on a struct and `&mut self`. **Sidebar link: methods, `self`, `&self`, `&mut self`.**
13. **Save vs Save As** — one command that decides based on whether the current path is `Some`. Save dialog. `match` on `Option`, `if let`. **Sidebar link: match and pattern matching.**
14. **🎉 Checkpoint — your editor feels real.** Quiz covering chapters 11–13. Next arc teaser.
15. **A real error type** — replace `Result<_, String>` with a `FeditError` enum using `thiserror`. `From<std::io::Error>` so `?` bridges automatically. **Sidebar link: enums with data and custom errors.**
16. **Recent files** — `Vec<PathBuf>` in state, persisted via `tauri-plugin-store` as JSON. `#[derive(Serialize, Deserialize)]` on our own type. Iterate with `.iter().take(10)`. **Sidebar links: Vec and iterators; traits and derive.**
17. **Keyboard shortcuts** — `Ctrl/Cmd+O`, `Ctrl/Cmd+S`, `Ctrl/Cmd+Shift+S`, `Ctrl/Cmd+N`. Native menu bar on macOS.
18. **🎉 Checkpoint — you built a real app.** Everything works. Quiz covering chapters 15–17.
19. **Bundle and ship** — `npm run tauri build`. One paragraph on code-signing. Brag about bundle size.
20. **Where next** — The Rust Book, Rustlings, `tokio`, deeper serde, `egui` / Leptos / Dioxus, the Tauri plugin ecosystem.

That's **20 main-track chapters**, four of which are checkpoints and two of which are install/outro. Net **14 chapters that teach**. Target total main-track reading time: 2.5–3 hours, in 10–15 minute bites.

## 6. Concept sidebar inventory

Exactly these sidebars, in the order they are first linked from the main track. Each is a collapsible `<details>` panel (or equivalent) that expands inline and contains its own Playground-runnable examples.

1. **Rust: crates, packages, and editions** — linked from ch. 1. The Cargo vocabulary you need to read `Cargo.toml`.
2. **Rust: `String` vs `&str`** — linked from ch. 3. The single most common beginner confusion.
3. **Rust: ownership and move semantics** — linked from ch. 4. The big one. Takes longer than other sidebars; that's fine.
4. **Rust: `Result` and the `?` operator** — linked from ch. 5.
5. **Rust: `Option`** — linked from ch. 7.
6. **Tauri: the permissions model** — linked from ch. 7. Not Rust, but critical and easy to get wrong.
7. **Rust: how serde carries data across IPC** — linked from ch. 8. One page. Just enough to recognise the pattern.
8. **Rust: references and borrowing** — linked from ch. 9. The companion piece to the ownership sidebar.
9. **Rust: shared mutable state** — linked from ch. 11. Covers `Mutex`, `Arc`, interior mutability, and why Rust makes you ask for it explicitly.
10. **Rust: methods, `self`, `&self`, `&mut self`** — linked from ch. 12.
11. **Rust: `match` and pattern matching** — linked from ch. 13. Includes `if let`, `while let`.
12. **Rust: enums with data and custom errors** — linked from ch. 15.
13. **Rust: `Vec` and iterators** — linked from ch. 16.
14. **Rust: traits and `derive`** — linked from ch. 16.

Each sidebar follows the same shape: (1) one-paragraph plain-English definition, (2) one or two Playground examples, (3) one "common gotcha," (4) "⟵ back to the main track."

## 7. ADHD-aware design principles

These apply across the whole tutorial and inform every structural decision. They are not style notes — they're requirements.

- **Start with something that works, then modify.** The reader never creates a file from a blank page. Chapter 1 scaffolds a running app. Every subsequent chapter modifies code that already runs.
- **Every chapter ends visibly different.** A window opens. A button does something new. A file loads. "You should see…" is non-negotiable.
- **Chapters are short.** Target 10–15 minutes of reading. If a chapter feels long while drafting, split it.
- **Compiler errors are exercises, not failures.** "Delete this `&`. Run `cargo check`. Read the error. Can you fix it?" This turns the borrow checker from antagonist into puzzle-mate.
- **Checkpoint every 3–4 chapters.** Named celebrations of progress with a visible state snapshot. This is where quizzes live — not after every chapter.
- **Progress is visible.** A progress bar, a chapter-done checklist, or a persistent "you are here" marker in the TOC. Reader can see how far they've come without scrolling.
- **Skipping is blessed.** Sidebars are opt-in. The tutorial explicitly tells the reader, early, that skipping sidebars is a legitimate way to read it.
- **Momentum beats completeness.** When in doubt, cut.

## 8. Pedagogy principles (content-level)

- **Example before rule.** Every concept is shown working before it is named.
- **Name the confusion.** Before resolving `String` vs `&str`, the Tauri permissions model, ownership, or anything else beginners trip on, say out loud: "If you're coming from JS or Python, this next part feels wrong. That's normal. Here's why it works this way."
- **No premature abstraction.** The first `echo` command returns `String`, not `Result<String, FeditError>`. The custom error type arrives only when the reader has *felt* the pain of stringly-typed errors.
- **Cite the real compiler output.** When a concept is best learned by breaking something, paste the actual compiler error in a code block and read it together.

## 9. Code presentation

- Every code block has a **filename tab** (`src-tauri/src/lib.rs`, `src/main.js`, `src-tauri/Cargo.toml`, `src-tauri/capabilities/default.json`, etc.).
- **Sidebars** use "Run in Playground" buttons. URL format: `https://play.rust-lang.org/?version=stable&mode=debug&edition=2024&code=<URL-ENCODED>`, target `_blank`.
- **Main-track chapters** do not use Playground buttons — that code belongs in `fedit/`. Instead, each chapter ends with the literal terminal command and the expected on-screen result.
- **Edits to existing files** are shown as **diffs** (`-`/`+` prefixes, coloured), not whole files. End of each chapter links to the full file at that git tag.
- Every block has a **Copy** button with visual feedback. Fallback to `document.execCommand('copy')` if Clipboard API is unavailable.
- Syntax highlighting: **Prism.js** from cdnjs with `prism-rust`, `prism-toml`, `prism-json`, `prism-javascript`, `prism-bash`, `prism-diff`.
- **Compiler-error blocks** get a distinct treatment — monospace, muted red accent, labeled `rustc` in the tab position.

## 10. Visual design

Warm editorial / technical-book aesthetic. Deliberately not "AI-generated dashboard."

- **Typography** (Google Fonts): `Fraunces` display (variable, optical sizing), `IBM Plex Sans` body, `JetBrains Mono` code.
- **Palette (light)**: bg `#FAF4E8`, text `#2A1F1A`, accent `#C8441B`. Derive a dark palette with equal character.
- **Dark-mode toggle** persists via `localStorage` wrapped in `try/catch`.
- **Texture**: low-opacity SVG noise overlay on the page background.
- **Drop cap** on each main-track chapter opener via `::first-letter`.
- **Line-height** ≥ 1.65, prose max-width ≈ 65ch.
- **Layout** — desktop: fixed left sidebar with TOC + scrollspy (`IntersectionObserver`). Mobile (≤ 768 px): sidebar collapses to a hamburger.
- **Sidebars** (the pedagogical kind) — distinct background tint, indented slightly, clear "⟶ Rust:" prefix in the summary header. When expanded, they feel like a margin note blown up, not like inline body text.
- **Checkpoint cards** — full-width coloured panel with a small celebratory flourish, the chapter range recap, and the quiz inline.
- **Print stylesheet** — hide nav and buttons, expand all sidebars, serif body.

## 11. Interactive features

- **Scrollspy TOC** updating via `IntersectionObserver`.
- **Progress indicator** — a persistent bar or dot strip in the header showing how many main-track chapters are complete. Completion stored in `localStorage` (try/catch).
- **"Mark chapter done" button** at the end of each main-track chapter.
- **Collapsible concept sidebars** using `<details>`/`<summary>` with smooth expand. Expansion state saved to `localStorage` per-sidebar so a returning reader finds things as they left them.
- **Smooth scroll** on TOC clicks.
- **Checkpoint quizzes** — multiple choice. "Check answer" reveals correct option plus a one-sentence explanation for each option.
- **Copy to clipboard** on every code block with visual feedback.
- **Run in Playground** button on sidebar code blocks only.
- **Dark-mode toggle** in the header.

## 12. The `fedit/` repo

- Scaffolded with `create-tauri-app`'s **vanilla** template. No React, Svelte, Vue — the tutorial's focus is Rust.
- Frontend kept to three files: `src/index.html`, `src/styles.css`, `src/main.js`. Styling tuned to match the tutorial palette so screenshots are coherent.
- **Git tags**: one per main-track chapter that changes code. `ch01`, `ch02`, `ch03`, `ch04`, `ch05`, `ch07`, `ch08`, `ch09`, `ch11`, `ch12`, `ch13`, `ch15`, `ch16`, `ch17`. (Chapters 2, 6, 10, 14, 18, 19, 20 do not tag — 2 is frontend tweaks that can merge into ch. 3, 6/10/14/18 are checkpoints, 19/20 are outro.) `main` equals `ch17`.
- `README.md`: project name, one-paragraph description, how to run, link to the tutorial.
- `.gitignore`: `/src-tauri/target`, `/node_modules`, `/dist`.
- `capabilities/default.json` audited at each chapter that adds a plugin API — no over-granted permissions.

## 13. Acceptance criteria — run before declaring done

1. **HTML validity.** Parse `rust-tutorial.html` with Python's `html.parser`. Zero unclosed tags, zero nesting errors.
2. **Sidebar code samples compile.** Extract every Rust sample from the sidebars into `.rs` files; run `rustc --edition 2024 --emit=metadata <file>` on each. Samples that use external crates can be validated by inspection.
3. **Main-track code matches the repo.** Every code block in the main track corresponds to a real line range in `fedit/` at the matching git tag. No fabricated snippets.
4. **`fedit` builds.** `npm install && npm run tauri build --debug` succeeds on the host platform. At minimum, `cargo check --manifest-path src-tauri/Cargo.toml` must pass.
5. **Permissions audit.** `capabilities/default.json` lists exactly the plugin permissions used — no more, no less. Confirm `dialog:allow-open`, `dialog:allow-save`, `fs:allow-read-text-file`, `fs:allow-write-text-file` are present and correctly scoped.
6. **Quiz answers correct.** Re-read each of the four checkpoint quizzes; verify the "correct" option is genuinely correct and the explanations for wrong options are accurate.
7. **Sidebars collapse by default.** On first load, every `<details>` is closed. Expansion state persists across reload.
8. **Playground links work.** Click three random sidebar links; they should load and run.
9. **Responsive check.** At 375 px width the sidebar collapses; prose stays readable; sidebars still expand usefully.
10. **Dark mode.** Toggles, persists, no contrast failures — check sidebars and checkpoint cards specifically.
11. **Progress persistence.** Mark three chapters done, reload, confirm they stay marked.
12. **Report back.** Final HTML size and line count, `fedit` bundle size after `tauri build`, any decisions made that weren't spelled out here.

## 14. Tone

Warm, concrete, unhurried *within* a chapter; brisk *between* them. Short paragraphs. Concrete example before abstract rule. Name the confusion. When the compiler yells, treat it as a rite of passage. Don't apologise for Rust's strictness — sell it. When celebrating a checkpoint, mean it.
