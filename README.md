# Learn Rust by building a Tauri 2 text editor

An interactive tutorial that teaches Rust to a total beginner by having them build a working desktop app — `fedit`, a tiny cross-platform text editor — one chapter, one git tag, one commit at a time.

There's no magic. Each chapter adds between 1 and 50 lines of Rust / JS / JSON, explains exactly why, and lets you reproduce it by running `git checkout chNN` in `fedit/`. You can read the whole thing and never type anything, but you'll get much more out of it if you type.

## Quick start

`fedit/` lives in [its own repo](https://github.com/jihlenburg/fedit) and is wired in here as a git submodule, so clone recursively:

```bash
git clone --recursive https://github.com/jihlenburg/rustic.git
cd rustic
```

Forgot `--recursive`? No harm:

```bash
git submodule update --init --recursive
```

## What's in this repo

| Path | What it is |
|------|-----------|
| [rust-tutorial.html](rust-tutorial.html) | The tutorial itself — one self-contained HTML file. Open it in any browser. Twin-track reading: a main chapter track on the left, collapsible concept sidebars on the right. Bilingual (English ↔ Türkçe, header toggle). Progress, theme, and language are saved to `localStorage`. |
| [fedit/](https://github.com/jihlenburg/fedit) | The Tauri 2 project you're going to build, pinned as a submodule. Per-chapter git tags (`ch01` … `ch25`, skipping frontend-only chapters) let you jump to any chapter's state. |
| [docs/architecture.md](docs/architecture.md) | The design document that drives the tutorial's structure. The authoritative spec — updated in lockstep with the code. Useful if you want to fork and rework it. |

## Start here

1. **Open `rust-tutorial.html` in a browser.** No build step. No server. Just open the file.
2. **Read chapter 0.** It walks you through installing Rust, Node, and the per-OS prerequisites (Windows 10 / 11, macOS, Linux). On Windows 10 the WebView2 runtime story matters — chapter 0 covers it.
3. **When you're ready to start coding**, `cd fedit/` and `npm install`, then `git checkout ch01` to jump to the starting point.

## Run fedit at any chapter

```bash
cd fedit
npm install
git checkout ch05          # or ch10, ch15, ch22, ch25 — any chapter's state
npm run tauri dev
```

Hot-reload is on. Edit `src/main.js` or `src-tauri/src/lib.rs`, save — the app updates.

## Ship fedit

```bash
cd fedit
npm run tauri build
```

Installers land in `src-tauri/target/release/bundle/` — a `.dmg` on macOS, `.msi` + `.exe` on Windows, `.deb` / `.rpm` / `AppImage` on Linux. Chapter 19 covers the Windows WebView2 bundle options and a GitHub Actions workflow for one-tag-one-release.

## What you'll learn

**Rust:** ownership and borrowing, `Option` and `Result`, `?`, `match`, structs and `impl` blocks, enums with data, `Mutex` and shared state, `Vec` and iterators, traits and `#[derive]`, custom error types with `thiserror`, serde, `From` / `Into` conversions, deep pattern matching (guards, `if-let`, `let-else`), `anyhow` vs `thiserror`, channels (`mpsc`), `async` / `.await` (and why Tauri commands can be async), `#[cfg]` attributes and feature flags, doctests, and a guided tour of `unsafe`.

**Tauri 2:** the plugin model, the deny-by-default permissions / capabilities system, `State<T>`, `AppHandle`, `#[tauri::command]`, custom `Serialize` for error shapes, window events, the menu API with `CmdOrCtrl` accelerators, `tauri-plugin-dialog`, `tauri-plugin-store`, scroll-synced UI, the `regex` crate, a tab-model rewrite of `AppState`, hot-applied settings, and a fuzzy-search command palette.

**Good habits along the way:** read compiler errors as help (every chapter has a *try breaking it* exercise, and inline "compile-error decoder" callouts translate rustc into plain English at the spots where you'll first meet E0382 / E0308 / poison errors), prefer narrow permissions to broad ones, treat errors as data, write methods on domain types.

## The shape of the tutorial

Twenty-eight teaching units (chapters 0–26 plus the 2b CSS interlude) in five arcs:

- **0 — Setup.** Per-OS install instructions. WebView2 on Windows 10.
- **1–6 — First window, first Rust, first file read.** Ownership, `String` vs `&str`, `Result` + `?`.
- **2b — Beautify fedit (optional CSS primer).** Six short CSS moves that turn the naked window into something you'd screenshot. Teaches CSS custom properties, flexbox, focus rings, and a one-attribute dark mode. Zero Rust.
- **7–10 — A real file picker and editable buffer.** Plugins, permissions, `Option`, serde, references and borrowing.
- **11–14 — State, methods, and save-as.** `Mutex<AppState>`, `impl`, `match`.
- **15–18 — A proper error type, recent files, a native menu.** `thiserror`, `Vec` + iterators, traits, `MenuBuilder`.
- **19–20 — Ship it.** Bundle, WebView2, CI, where to go next.
- **21–26 — Make it a *good* editor.** A scroll-synced line-number gutter (ch21), find/replace with the `regex` crate (ch22), tabs built on a `Vec<FileBuf>` rewrite of `AppState` (ch23), settings that hot-apply via `tauri-plugin-store` and `#[serde(default)]` (ch24), a fuzzy Ctrl/Cmd+Shift+P command palette (ch25), and a consolidating checkpoint quiz (ch26).

Checkpoints with quizzes at chapters 6, 10, 14, 18, and 26. Every chapter and sidebar is written in both English and Turkish — flip with the `EN ↔ TR` button in the header.

Thirty-four concept sidebars cover the Rust topics the main track only touches — `ownership`, `borrow` / `borrow checker`, `lifetimes`, smart pointers, `Send`/`Sync`, `Mutex` / interior mutability, channels, `async` / `.await`, `From` / `Into`, `thiserror` vs `anyhow`, `cfg` + feature flags, doctests, macros, the `unsafe` primer, and more. Each sidebar ends with a "See also" footer so a reader can hop between related ideas.

## Reference material

Three appendices live after chapter 26, reachable from the header quick-links and the TOC:

- **Glossary** — ~80 alphabetised Rust + Tauri terms, each with a one-line definition and a jump-link back to where it's explained.
- **Troubleshooting** — 18 common compile / runtime / build symptoms grouped by area (Rust compiler errors, Tauri runtime & build, platform-specific), each with Cause / Fix.
- **Cheatsheet** — 10 dense cards (bindings, flow control, structs & enums, traits, ownership, errors, iterators, derives, Tauri command shape, cargo & tooling) — print-stylesheet-safe, pairs two columns on paper.

## Requirements, in short

- **Rust** (stable, via [rustup.rs](https://rustup.rs)) — edition 2024 compatible toolchain.
- **Node.js 20+** and `npm`.
- Platform extras:
  - **Windows 10 / 11:** Visual Studio Build Tools (C++), Edge WebView2 runtime (preinstalled on Windows 11 and recent Windows 10).
  - **macOS:** Xcode command line tools (`xcode-select --install`).
  - **Linux:** `libwebkit2gtk-4.1-dev`, `librsvg2-dev`, `libayatana-appindicator3-dev`, `patchelf`, `build-essential`.

Full step-by-step setup, including common errors, is in chapter 0 of the tutorial.

## Licence

The tutorial text, the architecture document, and the `fedit` source code in this repo are free to use, adapt, and redistribute under the [MIT licence](https://opensource.org/licenses/MIT).
