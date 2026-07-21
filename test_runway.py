"""Regressionsnetz für die Kernlogik von runway.py.

Charakterisiert das beabsichtigte Verhalten der GUI-freien Funktionen. Die
Außenwelt (laufende Prozesse, PROJECTS_DIR) wird per Monkeypatch ersetzt —
runway.py bleibt unangetastet.
"""

import json
import os
import time

import pytest

import runway


# --- context_window_for ---

@pytest.mark.parametrize("model,expected", [
    ("claude-opus-4-8", 1_000_000),
    ("claude-sonnet-5", 1_000_000),
    ("claude-fable-5", 1_000_000),
    ("some-mythos-model", 1_000_000),
    ("claude-haiku-4-5", 200_000),
    ("unknown-model", 200_000),
    ("", 200_000),
    (None, 200_000),
])
def test_context_window_for(model, expected):
    assert runway.context_window_for(model) == expected


# --- fmt ---

@pytest.mark.parametrize("n,expected", [
    (1_234_567, "1.234.567"),
    (1_000_000, "1.000.000"),
    (500, "500"),
    (0, "0"),
])
def test_fmt(n, expected):
    assert runway.fmt(n) == expected


# --- Helfer ---

def make_session(cwd="/Users/test/project", usage=None,
                 model="claude-opus-4-8", sidechain=False):
    """Baut minimalen JSONL-Inhalt: Kopfzeile (cwd/isSidechain) + usage-Zeile."""
    head = {}
    if sidechain:
        head["isSidechain"] = True
    if cwd is not None:
        head["cwd"] = cwd
    lines = [json.dumps(head)]
    if usage is not None:
        lines.append(json.dumps({"message": {"usage": usage, "model": model}}))
    return "\n".join(lines) + "\n"


def write_active(directory, name, cwd, total, mtime):
    p = directory / name
    p.write_text(make_session(cwd=cwd, usage={"input_tokens": total}))
    os.utime(p, (mtime, mtime))
    return p


# --- read_session ---

def test_read_session_normal(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(make_session(
        cwd="/Users/test/project",
        usage={"input_tokens": 300_000,
               "cache_creation_input_tokens": 100_000,
               "cache_read_input_tokens": 100_000},
        model="claude-opus-4-8"))
    s = runway.read_session(str(p))
    assert s["project"] == "project"
    assert s["project_cwd"] == "/Users/test/project"
    assert s["total"] == 500_000
    assert s["window"] == 1_000_000
    assert s["pct"] == 50


def test_read_session_sums_missing_token_fields(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(make_session(usage={"input_tokens": 200_000}))  # andere Felder fehlen
    assert runway.read_session(str(p))["total"] == 200_000


def test_read_session_sidechain_returns_none(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(make_session(cwd="/x", usage={"input_tokens": 1}, sidechain=True))
    assert runway.read_session(str(p)) is None


def test_read_session_no_usage_returns_none(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(make_session(cwd="/x", usage=None))
    assert runway.read_session(str(p)) is None


def test_read_session_no_cwd_returns_none(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text(
        json.dumps({"foo": "bar"}) + "\n"
        + json.dumps({"message": {"usage": {"input_tokens": 1}, "model": "opus"}}) + "\n")
    assert runway.read_session(str(p)) is None


def test_read_session_head_tail_split(tmp_path, monkeypatch):
    # Byte-Fenster künstlich verkleinern, damit ein winziges Fixture den
    # Head/Tail-Schnitt (size > HEAD+TAIL) auslöst.
    monkeypatch.setattr(runway, "HEAD_BYTES", 60)
    monkeypatch.setattr(runway, "TAIL_BYTES", 120)
    head_line = json.dumps({"cwd": "/big/proj"})            # < 60 Bytes → ganz im Head
    filler = "#" * 400                                       # ungültiges JSON → übersprungen
    tail_line = json.dumps({"message": {"usage": {"input_tokens": 250_000},
                                        "model": "claude-opus-4-8"}})
    p = tmp_path / "big.jsonl"
    p.write_text(head_line + "\n" + filler + "\n" + tail_line + "\n")
    assert p.stat().st_size > 60 + 120
    s = runway.read_session(str(p))
    assert s["project_cwd"] == "/big/proj"
    assert s["total"] == 250_000


# --- find_active_sessions ---

def test_find_active_no_running_processes(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: set())
    write_active(tmp_path, "a.jsonl", "/proj/a", 500_000, time.time())
    assert runway.find_active_sessions() == []


def test_find_active_includes_matching_cwd(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: {"/proj/a"})
    write_active(tmp_path, "a.jsonl", "/proj/a", 500_000, time.time())
    result = runway.find_active_sessions()
    assert len(result) == 1
    assert result[0]["project"] == "a"


def test_find_active_excludes_nonmatching_cwd(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: {"/proj/other"})
    write_active(tmp_path, "a.jsonl", "/proj/a", 500_000, time.time())
    assert runway.find_active_sessions() == []


def test_find_active_dedups_by_cwd_keeps_newest(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: {"/proj/a"})
    now = time.time()
    write_active(tmp_path, "old.jsonl", "/proj/a", 100_000, now - 100)
    write_active(tmp_path, "new.jsonl", "/proj/a", 200_000, now - 10)
    result = runway.find_active_sessions()
    assert len(result) == 1
    assert result[0]["total"] == 200_000


def test_find_active_excludes_files_older_than_scan_window(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: {"/proj/a"})
    old = time.time() - runway.SCAN_WINDOW_SECONDS - 3600
    write_active(tmp_path, "a.jsonl", "/proj/a", 500_000, old)
    assert runway.find_active_sessions() == []


def test_find_active_sorts_by_pct_desc(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, "PROJECTS_DIR", tmp_path)
    monkeypatch.setattr(runway, "running_claude_cwds", lambda: {"/proj/a", "/proj/b"})
    now = time.time()
    write_active(tmp_path, "a.jsonl", "/proj/a", 800_000, now)   # 80 %
    write_active(tmp_path, "b.jsonl", "/proj/b", 200_000, now)   # 20 %
    result = runway.find_active_sessions()
    assert [s["project"] for s in result] == ["a", "b"]
