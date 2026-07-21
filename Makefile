# Runway — bauen & installieren
# Single source of truth: runway.py (Version in setup.py). Alles andere ist abgeleitet.

VENV := ./venv/bin
APP  := dist/Runway.app
DEST := /Applications/Runway.app

.PHONY: install build run test icon clean

# Bauen + nach /Applications deployen + neu starten. Der eine Befehl, der Drift verhindert.
install: build
	-pkill -x Runway
	ditto $(APP) $(DEST)
	touch $(DEST)               # ditto behält altes Bundle-Datum → sonst cached macOS das alte Icon
	open $(DEST)
	@echo "✓ Runway installiert → $(DEST)"

build: clean
	$(VENV)/python setup.py py2app

run:                            # ohne Bundle direkt starten (Menü zeigt dann 'dev')
	$(VENV)/python runway.py

test:                           # Regressionsnetz — setzt `pip install -r requirements-dev.txt` voraus
	$(VENV)/pytest -q

icon:
	$(VENV)/python make_icon.py

clean:
	rm -rf build dist
