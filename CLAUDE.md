# Runway — Projekt-Kontext

macOS-Menubar-App: zeigt den Kontext-Füllstand aller aktiven Claude-Code-Sessions (● / 🟡 / 🔴 + Prozent), warnt pro Session bei 60%/80%. Single-User-Tool für Volkers Mac, bewusst einfach gehalten — kein Over-Engineering.

## Struktur

- `runway.py` — die komplette App (single-file, rumps)
- `setup.py` — py2app-Konfiguration fürs App-Bundle
- `make_icon.py` — erzeugt `icon.icns` aus `icon_source.png` (Sneaker-Motiv, via pillow)
- Installiert: `/Applications/Runway.app`, Autostart via Login Item (Systemeinstellungen → Anmeldeobjekte). Der frühere LaunchAgent wurde 2026-07-05 entfernt (lief parallel zum Login Item → doppeltes Menubar-Icon).

## Bauen & Deployen

```bash
./venv/bin/python runway.py                                  # Entwicklung: direkt starten
./venv/bin/python setup.py py2app                            # Bundle bauen → dist/Runway.app
pkill -x Runway; ditto dist/Runway.app /Applications/Runway.app
open /Applications/Runway.app                                # neu starten
```

`build/` und `dist/` sind Wegwerf-Artefakte (in .gitignore).

## Wartung

- **Bei neuen Claude-Modellen:** `CONTEXT_WINDOWS` in `runway.py` prüfen/ergänzen. Unbekannte Modelle fallen konservativ auf 200K zurück (Anzeige dann zu hoch — auffällig, aber ungefährlich).
- Berechnung wurde 2026-07-04 gegen `/context` validiert (< 1 Prozentpunkt Abweichung).

## Doku & Versionierung

- PRD, Projekt-Historie und Entscheidungs-Log: Obsidian-Vault `1-Projects/Runway/`. V1 hieß "token-tracker" (AI Makers Club Week 002), seit V1.1 (2026-07-04) "Runway".
- Git-Repo mit Remote **GitHub `volkermaxmeyer/runway` (privat)**. Nach Änderungen committen und pushen.
