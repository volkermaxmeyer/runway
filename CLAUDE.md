# Runway — project context

macOS menubar app: shows the context fill level of all active Claude Code sessions (● / 🟡 / 🔴 + percent), warns per session at 60% / 80%. A single-user tool, deliberately kept simple — no over-engineering.

## Structure

- `runway.py` — the whole app (single file, rumps)
- `setup.py` — py2app configuration for the app bundle
- `make_icon.py` — generates `icon.icns` from `icon_source.png` (sneaker motif, via pillow)
- Installed at `/Applications/Runway.app`, autostart via Login Item (System Settings → Login Items). An earlier LaunchAgent was removed on 2026-07-05 (it ran in parallel with the Login Item → duplicate menubar icon).

## Build & deploy

```bash
./venv/bin/python runway.py                                  # dev: run directly
./venv/bin/python setup.py py2app                            # build bundle → dist/Runway.app
pkill -x Runway; ditto dist/Runway.app /Applications/Runway.app
touch /Applications/Runway.app                               # required: ditto keeps the bundle date, so macOS caches the old icon
open /Applications/Runway.app                                # restart
```

`build/` and `dist/` are throwaway artifacts (in .gitignore).

## Maintenance

- **When new Claude models ship:** check/extend `CONTEXT_WINDOWS` in `runway.py`. Unknown models fall back conservatively to 200K (the displayed percent is then too high — noticeable, but harmless).
- The calculation was validated against `/context` on 2026-07-04 (< 1 percentage point deviation).

## Versioning

- V1 was called "token-tracker" (AI Makers Club, Week 002); since V1.1 (2026-07-04) it's "Runway". Releases are git-tagged (`vX.Y.Z`). After changes, commit and push.
