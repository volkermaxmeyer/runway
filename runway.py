#!/usr/bin/env python3
import json
import os
import glob
import time
from pathlib import Path

import rumps

PROJECTS_DIR = Path.home() / ".claude" / "projects"
POLL_INTERVAL = 15
ACTIVE_WINDOW_SECONDS = 600  # Session gilt als aktiv, wenn Log < 10 Min alt

THRESHOLD_YELLOW = 60
THRESHOLD_RED = 80

DEFAULT_CONTEXT_WINDOW = 200_000
CONTEXT_WINDOWS = [
    ("haiku", 200_000),
    ("opus", 1_000_000),
    ("sonnet", 1_000_000),
    ("fable", 1_000_000),
    ("mythos", 1_000_000),
]

HEAD_BYTES = 65_536   # Dateianfang: hier steht cwd/isSidechain
TAIL_BYTES = 262_144  # Dateiende: hier steht die letzte usage-Zeile


def context_window_for(model):
    name = (model or "").lower()
    for key, window in CONTEXT_WINDOWS:
        if key in name:
            return window
    return DEFAULT_CONTEXT_WINDOW


def parse_lines(chunk):
    for line in chunk.splitlines():
        try:
            yield json.loads(line)
        except Exception:
            continue


def read_session(path):
    """Liest Projektname, Modell und letzte usage einer Session-Datei."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(HEAD_BYTES)
        if size > HEAD_BYTES + TAIL_BYTES:
            f.seek(size - TAIL_BYTES)
            tail = f.read()
            tail = tail[tail.find(b"\n") + 1:]
        else:
            f.seek(0)
            tail = f.read()

    cwd = None
    for data in parse_lines(head.decode("utf-8", errors="replace")):
        if data.get("isSidechain"):
            return None
        if cwd is None and data.get("cwd"):
            cwd = data["cwd"]
    if cwd is None:
        return None

    usage = None
    model = None
    for data in parse_lines(tail.decode("utf-8", errors="replace")):
        msg = data.get("message")
        if isinstance(msg, dict) and msg.get("usage"):
            usage = msg["usage"]
            model = msg.get("model", "")
    if not usage:
        return None

    total = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    window = context_window_for(model)
    pct = min(int(total / window * 100), 100)
    return {
        "path": path,
        "project": Path(cwd).name or cwd,
        "pct": pct,
        "total": total,
        "window": window,
    }


def find_active_sessions():
    cutoff = time.time() - ACTIVE_WINDOW_SECONDS
    sessions = []
    for path in glob.glob(str(PROJECTS_DIR / "**" / "*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(path) < cutoff:
                continue
            session = read_session(path)
        except OSError:
            continue
        if session:
            sessions.append(session)
    sessions.sort(key=lambda s: s["pct"], reverse=True)
    return sessions


def icon_for(pct):
    if pct >= THRESHOLD_RED:
        return "🔴"
    if pct >= THRESHOLD_YELLOW:
        return "🟡"
    return "●"


def fmt(n):
    return f"{n:,}".replace(",", ".")


class Runway(rumps.App):
    def __init__(self):
        super().__init__("● --", quit_button=None)
        self._thresholds = {}  # session-path -> zuletzt gemeldete Schwelle

    @rumps.timer(POLL_INTERVAL)
    def update(self, _):
        sessions = find_active_sessions()

        if not sessions:
            self.title = "● --"
            self._rebuild_menu([rumps.MenuItem("Keine aktive Session")])
            return

        top = sessions[0]
        self.title = f"{icon_for(top['pct'])} {top['pct']}%"

        items = []
        for s in sessions:
            label = (
                f"{icon_for(s['pct'])} {s['project']} — {s['pct']}% "
                f"({fmt(s['total'])} / {fmt(s['window'])})"
            )
            items.append(rumps.MenuItem(label))
        self._rebuild_menu(items)
        self._notify(sessions)

    def _rebuild_menu(self, items):
        self.menu.clear()
        for item in items:
            self.menu.add(item)
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit Runway", callback=rumps.quit_application))

    def _notify(self, sessions):
        active_paths = {s["path"] for s in sessions}
        for path in list(self._thresholds):
            if path not in active_paths:
                del self._thresholds[path]

        for s in sessions:
            last = self._thresholds.get(s["path"])
            if s["pct"] >= THRESHOLD_RED and last != THRESHOLD_RED:
                self._thresholds[s["path"]] = THRESHOLD_RED
                rumps.notification(
                    "Runway", s["project"],
                    f"Kontext bei {s['pct']}% — /clear empfohlen", sound=False,
                )
            elif THRESHOLD_YELLOW <= s["pct"] < THRESHOLD_RED and last is None:
                self._thresholds[s["path"]] = THRESHOLD_YELLOW
                rumps.notification(
                    "Runway", s["project"], f"Kontext bei {s['pct']}%", sound=False,
                )
            elif s["pct"] < THRESHOLD_YELLOW and last is not None:
                del self._thresholds[s["path"]]


if __name__ == "__main__":
    Runway().run()
