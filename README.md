# Runway

macOS-Menubar-App. Zeigt den Kontext-Füllstand aller aktiven Claude-Code-Sessions (● / 🟡 / 🔴 + Prozent) und benachrichtigt pro Session bei Schwellen-Überschreitung (60% / 80%).

**Status:** V1.2.0 seit 2026-07-05 (Session-Anzahl in der Menubar). Davor: V1.1.1 (eigenes Sneaker-Icon, 2026-07-05), V1.1 „Runway" (2026-07-04), token-tracker (V1, AI Makers Club Week 002 Submission, 2026-05-15). Releases sind git-getaggt.

**Doku & Projektkontext:** `1-Projects/Runway/` im Obsidian-Vault — enthält PRD, CLAUDE.md (inkl. Entscheidungs-Log), AMC-Brief-Referenz.

**Repository:** GitHub `volkermaxmeyer/runway` (privat) — https://github.com/volkermaxmeyer/runway

## Installation / Betrieb

- App: `/Applications/Runway.app` (Menubar-only, kein Dock-Icon)
- Autostart: Login Item (Systemeinstellungen → Anmeldeobjekte). Kein LaunchAgent — der frühere lief parallel zum Login Item und erzeugte ein doppeltes Menubar-Icon (entfernt 2026-07-05)
- Menubar zeigt die **vollste** aktive Session, bei mehreren Sessions mit Anzahl (z.B. „🟡 72% · 3" — Max, keine Summe); Klick öffnet Dropdown mit allen aktiven Sessions (Projektname, %, absolute Tokens)

## Entwicklung

```bash
cd ~/tools/runway
./venv/bin/python runway.py          # direkt starten (ohne App-Bundle)
./venv/bin/python make_icon.py       # icon.icns neu erzeugen
./venv/bin/python setup.py py2app    # App-Bundle bauen → dist/Runway.app
pkill -x Runway; ditto dist/Runway.app /Applications/Runway.app
open /Applications/Runway.app
```

Release: Version in `setup.py` anheben, bauen, installieren, committen, Tag `vX.Y.Z` pushen.

## Funktionsweise

- Liest `~/.claude/projects/**/*.jsonl` (Claude Code Session-Logs), Poll alle 15s
- Aktiv = Log-Datei in den letzten 10 Minuten geschrieben; Subagenten-Logs werden übersprungen
- Kontext = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` der letzten Assistant-Zeile
- Kontextfenster pro Modell: Opus/Sonnet/Fable/Mythos → 1M, Haiku → 200K, unbekannt → 200K (konservativ)
- Projektname stammt aus dem `cwd`-Feld im Session-Log
- Notifications bei 60% (gelb) und 80% (rot), pro Session einzeln, einmal pro Schwellen-Übergang
- Sessions ohne Aktivität seit 10 Minuten verschwinden automatisch aus Menubar und Dropdown
- **Erste Inbetriebnahme:** Bei der ersten Warnung fragt macOS nach Mitteilungs-Erlaubnis für Runway — erlauben, sonst kommen Warnungen nicht durch

## Tech

- `rumps` (macOS Menubar), `py2app` (App-Bundle), `pillow` (Icon-Generierung)
- Liest nur Datei-Anfang (cwd) und -Ende (letzte usage) statt ganzer Logs — bleibt auch bei großen Sessions sparsam
- Single-file: `runway.py`
