# Contributing to HyprMod

Thanks for your interest in contributing! HyprMod is a growing project and PRs are welcome.

## Development setup

System dependencies (Debian/Ubuntu names; adapt for your distro):

```
libcairo2-dev libgirepository-2.0-dev libgtk-4-dev libadwaita-1-dev gir1.2-gnomedesktop-4.0
```

Then:

```bash
git clone https://github.com/BlueManCZ/hyprmod.git
cd hyprmod
uv sync
uv run hyprmod
```

Requires Python 3.12+ and a running Hyprland instance for full manual testing.

Use `uv` for everything. Never `pip`, never the system Python.

## Before submitting a PR

Run the same four checks that CI runs:

```bash
uv run ruff check --fix hyprmod/ tests/
uv run ruff format hyprmod/ tests/
uv run pyright hyprmod/ tests/
uv run pytest tests/ -v
```

All four must pass before your PR can be merged. Run them before every push, not just once at the end. Don't lean on CI to catch formatting, lint, or type errors after the fact.

For UI changes, also run `uv run hyprmod` against a live Hyprland and exercise the page you touched. Whole classes of bug (empty dialogs, stale state on first render, exceptions escaping GTK callbacks) only surface at runtime, and the checks above will not catch them. In the PR, say what you verified by hand.

New pure logic under `core/` should ship with tests in `tests/`, following the existing class-based style. GTK page and widget code does not need unit tests.

Add a bullet to `CHANGELOG.md` under `## [Unreleased]` for any user-visible change, referencing the PR or issue number.

Then re-read your own diff with these in mind:

- Dead fields, params, branches, imports, or attributes?
- Duplicated literals that should derive from one source?
- Thin wrappers or one-line delegators?
- Defensive `isinstance` / `try-except` / fallback for cases that can't happen?
- Comments or docstrings that just restate the code?
- Reinvented wheel where stdlib or an existing helper would do?
- Library workarounds that should be upstream changes?
- One page reaching into another's private attributes instead of a public method?

## Code style

- Python 3.12+. **No `from __future__ import ...`.**
- Ruff enforces `E`, `F`, `W`, `I` rules with a line length of 100. Always run with `--fix`.
- Pyright must pass clean. Don't use `assert` for type narrowing; restructure the code instead.
- Imports at the top of the file, not inside functions.
- Match existing patterns for pages, rows, dialogs, widgets; don't invent new ones alongside them.
- Names describe purpose, not implementation or call-stack position.
- Comments only when the *why* is non-obvious. Never restate what the code does.
- No em-dashes (`—`) in prose, commit messages, or UI strings. Use periods, commas, or colons.

## Code quality

Things to avoid:

- **Dead code**: unused fields, params, branches, imports, instance attributes that nothing reads.
- **Duplication**: derive from one canonical source instead of spelling the same list/pair twice.
- **Thin wrappers**: one-line delegators that add no semantic value. Inline them.
- **Defensive code on non-boundary values**: don't `isinstance`-check values you constructed yourself, or guard against states your own code can't produce. Only validate at real boundaries (user input, external APIs).
- **Backwards-compat shims for code being rewritten in the same PR**. Just rewrite it.
- **Workarounds in place of root-cause fixes.**
- **Reaching into another class's internals**: don't read or mutate another page's private attributes (`_owned`, `_external`, …) from outside it. Expose a public method on the owning page (e.g. `AutostartPage.has_command()`) and call that.

## UI conventions

- **Live-apply IPC from UI callbacks**: any `hypr.keyword()` / `hypr.command()` call triggered interactively by a widget (live-apply hooks, dialog Apply buttons) must be wrapped in `try_with_toast(..., catch=HyprlandError)`. If the compositor rejects the command, the exception otherwise escapes the GTK callback and leaves the UI out of sync with no feedback to the user.
- **Initialization order**: pages are built before `_register_state()` runs, so `app_state.get()` returns `None` for options during a page's `__init__` and first `build()`. Don't read live state there and assume it is populated. Hook into state notifications, or rebuild once registration is done (the window calls the page's `_rebuild_list()` after `_register_state()`).

## Commits

- One commit per coherent change. Don't bundle refactor + feature + bugfix.
- Imperative title; body explains the *why* and any trade-offs. Call out behavior changes explicitly.

## Scope

- Check the [Roadmap](README.md#-roadmap) before proposing new features.
- For larger changes, open an issue first so we can discuss the approach.
- System settings (Wi-Fi, Bluetooth, theming, printing, etc.) are out of scope; see [#15](https://github.com/BlueManCZ/hyprmod/issues/15).

## The `hyprland-*` library stack

Parsing, IPC, schema, and state logic live in separate repositories under [BlueManCZ](https://github.com/BlueManCZ):

- [`hyprland-config`](https://github.com/BlueManCZ/hyprland-config) — round-trip parser
- [`hyprland-socket`](https://github.com/BlueManCZ/hyprland-socket) — typed IPC client
- [`hyprland-schema`](https://github.com/BlueManCZ/hyprland-schema) — versioned option catalog
- [`hyprland-state`](https://github.com/BlueManCZ/hyprland-state) — unified high-level API
- [`hyprland-monitors`](https://github.com/BlueManCZ/hyprland-monitors) — scale/geometry/EDID utilities
- [`hyprland-events`](https://github.com/BlueManCZ/hyprland-events) — typed event dispatch

If your change belongs in one of those libraries (parsing, IPC, schema data, etc.), please open the PR in that repository instead.

If you need a new field, behavior, or type from one of them inside hyprmod:

1. Add it upstream first.
2. Bump the pin in `pyproject.toml`.
3. Use it natively here.

**Never** monkey-patch these libraries. That includes mutating their private state, replacing their methods or attributes, and subclassing their types to add fields they don't define. Get behavior changes upstream first.

Don't guess Hyprland's runtime behavior. Assumptions about the Lua or IPC API (what a call accepts, what a namespace contains at load time, when a value is available) must be checked against a running instance (`hyprctl`, `hyprctl eval`) or the Hyprland source, not inferred and then papered over with a workaround.

## Reporting bugs

Open a [GitHub issue](https://github.com/BlueManCZ/hyprmod/issues) and include:

- Hyprland version (`hyprctl version`)
- Steps to reproduce
- Relevant log output, if any
