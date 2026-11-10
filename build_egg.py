#!/usr/bin/env python3
"""Construieste egg-ul pluginului fara setuptools (Windows / Linux).

    python build_egg.py               -> dist/AutoMediaMover-1.0-py3.9.egg (pentru Deluge 2.2 Windows)
    python build_egg.py --py 3.12     -> alt tag de Python (trebuie sa fie versiunea Python a lui Deluge)
    python build_egg.py --install     -> copiaza egg-ul si in folderul de pluginuri Deluge al utilizatorului
"""
import argparse
import os
import shutil
import sys
import zipfile

NAME = 'AutoMediaMover'
VERSION = '1.0'
PACKAGE = 'deluge_' + NAME.lower()
SUMMARY = 'Moves finished downloads to a Movies or TV Series/<Show>/ folder automatically'

ROOT = os.path.dirname(os.path.abspath(__file__))

ENTRY_POINTS = """[deluge.plugin.core]
{n} = {p}:CorePlugin

[deluge.plugin.gtk3ui]
{n} = {p}:GtkUIPlugin

[deluge.plugin.web]
{n} = {p}:WebUIPlugin
""".format(n=NAME, p=PACKAGE)

PKG_INFO = """Metadata-Version: 2.1
Name: {n}
Version: {v}
Summary: {s}
Author: CristianCasapu
License: GPLv3
""".format(n=NAME, v=VERSION, s=SUMMARY)


def plugin_dir():
    if os.name == 'nt':
        return os.path.join(os.environ.get('APPDATA', ''), 'deluge', 'plugins')
    base = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.join(base, 'deluge', 'plugins')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--py', default='3.9', help='Python version used by Deluge (default 3.9)')
    ap.add_argument('--install', action='store_true', help='copy egg to the Deluge plugins folder')
    args = ap.parse_args()

    dist = os.path.join(ROOT, 'dist')
    os.makedirs(dist, exist_ok=True)
    egg = os.path.join(dist, '%s-%s-py%s.egg' % (NAME, VERSION, args.py))

    src = os.path.join(ROOT, PACKAGE)
    with zipfile.ZipFile(egg, 'w', zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = [d for d in dirnames if d != '__pycache__']
            for f in sorted(filenames):
                if f.endswith(('.pyc', '.pyo')):
                    continue
                full = os.path.join(dirpath, f)
                arc = os.path.relpath(full, ROOT).replace(os.sep, '/')
                z.write(full, arc)
        z.writestr('EGG-INFO/PKG-INFO', PKG_INFO)
        z.writestr('EGG-INFO/entry_points.txt', ENTRY_POINTS)
        z.writestr('EGG-INFO/top_level.txt', PACKAGE + '\n')
        z.writestr('EGG-INFO/dependency_links.txt', '\n')
        z.writestr('EGG-INFO/not-zip-safe', '\n')
    print('Built:', egg)

    if args.install:
        dest = plugin_dir()
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(egg, dest)
        print('Installed to:', dest, '- restart Deluge and enable the plugin.')


if __name__ == '__main__':
    sys.exit(main())
