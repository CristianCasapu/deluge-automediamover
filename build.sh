#!/usr/bin/env sh
# Construieste egg-ul pluginului pe Linux (nu necesita setuptools).
# Tag-ul trebuie sa fie versiunea Python folosita de Deluge; detectata automat daca Deluge e instalat.
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
TARGET="${1:-$($PY -c 'import sys; print("%d.%d" % sys.version_info[:2])')}"
$PY build_egg.py --py "$TARGET" ${INSTALL:+--install}
echo "Copiaza dist/*.egg in ~/.config/deluge/plugins/ (sau ruleaza: INSTALL=1 ./build.sh)"
