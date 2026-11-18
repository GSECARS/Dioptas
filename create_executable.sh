#!/usr/bin/env bash
set -e
rm -rf build dist
export UV_PROJECT_ENVIRONMENT=.venv
uv venv
uv sync
uv pip install --python .venv pyinstaller
FABIO_PATH=$(uv run python -c "import fabio, os; print(os.path.dirname(fabio.__file__))")
cp fabio/eigerimage.py "$FABIO_PATH/eigerimage.py"
cp fabio/app/eiger2crysalis.py "$FABIO_PATH/app/eiger2crysalis.py"
uv run --no-sync pyinstaller Dioptas.spec -y

VERSION=$(uv run python -c "from dioptas import __version__; print(__version__)")
DMG_STAGING="/tmp/Dioptas_${VERSION}_dmg"
rm -rf "$DMG_STAGING"
mkdir "$DMG_STAGING"
cp -r "dist/Dioptas_${VERSION}.app" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"
hdiutil create -volname "Dioptas ${VERSION}" \
  -srcfolder "$DMG_STAGING" \
  -ov -format UDZO \
  "dist/Dioptas_Mac64_${VERSION}.dmg"
rm -rf "$DMG_STAGING"
