#!/usr/bin/env bash
set -e
rm -rf build dist
uv sync
uv pip install pyinstaller
FABIO_PATH=$(uv run python -c "import fabio, os; print(os.path.dirname(fabio.__file__))")
cp fabio/eigerimage.py "$FABIO_PATH/eigerimage.py"
cp fabio/app/eiger2crysalis.py "$FABIO_PATH/app/eiger2crysalis.py"
uv run --no-sync pyinstaller Dioptas.spec -y
