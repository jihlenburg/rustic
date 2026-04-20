# Learn Rust by building a Tauri 2 text editor

An interactive tutorial that teaches Rust to a total beginner by having them build a working desktop app — `fedit`, a tiny cross-platform text editor — one chapter, one git tag, one commit at a time.

There's no magic. Each chapter adds between 1 and 50 lines of Rust / JS / JSON, explains exactly why, and lets you reproduce it by running `git checkout chNN` in `fedit/`. You can read the whole thing and never type anything, but you'll get much more out of it if you type.

## What's in this repo

| Path | What it is |
|------|-----------|
| [rust-tutorial.html](rust-tutorial.html) | The tutorial itself — one self-contained HTML file. Open it in any browser. Twin-track reading: a main chapter track on the left, collapsible concept sidebars on the right. Bilingual (English ↔ Türkçe, header toggle). Progress, theme, and language are saved to `localStorage`. |
| [fedit/](fedit/) | The Tauri 2 project you're going to build. Seventeen git tags (`ch01` … `ch17`) let you jump to any chapter's state. |
| [rust-tutorial-architecture.md](rust-tutorial-architecture.md) | The design document that drove the tutorial's structure. Useful if you want to fork and rework it. |
| [rust-tutorial-prompt.md](rust-tutorial-prompt.md) | The original authoring prompt — provenance. |

## Start here

1. **Open `rust-tutorial.html` in a browser.** No build step. No server. Just open the file.
2. **Read chapter 0.** It walks you through installing Rust, Node, and the per-OS prerequisites (Windows 10 / 11, macOS, Linux). On Windows 10 the WebView2 runtime story matters — chapter 0 covers it.
3. **When you're ready to start coding**, `cd fedit/` and `npm install`, then `git checkout ch01` to jump to the starting point.

## Run fedit at any chapter

```bash
cd fedit
npm install
git checkout ch05          # or ch10, ch15, ch17 — any chapter's state
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

**Rust:** ownership and borrowing, `Option` and `Result`, `?`, `match`, structs and `impl` blocks, enums with data, `Mutex` and shared state, `Vec` and iterators, traits and `#[derive]`, custom error types with `thiserror`, serde.

**Tauri 2:** the plugin model, the deny-by-default permissions / capabilities system, `State<T>`, `AppHandle`, `#[tauri::command]`, custom `Serialize` for error shapes, window events, the menu API with `CmdOrCtrl` accelerators, `tauri-plugin-dialog`, `tauri-plugin-store`, and how to bundle the final product.

**Good habits along the way:** read compiler errors as help (every chapter has a *try breaking it* exercise), prefer narrow permissions to broad ones, treat errors as data, write methods on domain types.

## The shape of the tutorial

Twenty-one chapters plus one optional CSS interlude, roughly four arcs:

- **0 – Setup.** Per-OS install instructions. WebView2 on Windows 10.
- **1–6 — First window, first Rust, first file read.** Ownership, `String` vs `&str`, `Result` + `?`.
- **2b — Beautify fedit (optional CSS primer).** Six short CSS moves that turn the naked window into something you'd screenshot. Teaches CSS custom properties, flexbox, focus rings, and a one-attribute dark mode. Zero Rust.
- **7–10 — A real file picker and editable buffer.** Plugins, permissions, `Option`, serde, references and borrowing.
- **11–14 — State, methods, and save-as.** `Mutex<AppState>`, `impl`, `match`.
- **15–18 — A proper error type, recent files, a native menu.** `thiserror`, `Vec` + iterators, traits, `MenuBuilder`.
- **19–20 — Ship it.** Bundle, WebView2, CI, where to go next.

Checkpoints with quizzes at chapters 6, 10, 14, and 18. Every chapter and sidebar is written in both English and Turkish — flip with the `EN ↔ TR` button in the header.

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
