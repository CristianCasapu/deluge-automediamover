#
# AutoMediaMover - reguli de ignorare (fara dependente de Deluge, testabile).
#
import os
import re

DEFAULT_SKIP_LABELS = 'radarr, sonarr, lidarr, readarr, whisparr'


def split_keywords(value):
    """'radarr, Sonarr;tv-sonarr' -> ['radarr', 'sonarr', 'tv-sonarr']"""
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r'[,;\n]+', value or '')
    return [i.strip().lower() for i in items if i and i.strip()]


def split_paths(value):
    """Cai separate prin ';' sau linie noua (virgula poate aparea in nume de foldere)."""
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r'[;\n]+', value or '')
    return [i.strip() for i in items if i and i.strip()]


def _norm(path):
    path = os.path.expanduser(path.strip())
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def path_is_inside(path, parent):
    """True daca `path` este `parent` sau un subfolder al lui (Windows: fara diferente de majuscule)."""
    if not path or not parent or not parent.strip():
        return False
    try:
        p, root = _norm(path), _norm(parent)
    except (TypeError, ValueError):
        return False
    if p == root:
        return True
    return p.startswith(root.rstrip(os.sep) + os.sep)


def matching_folder(path, folders):
    for folder in folders:
        if path_is_inside(path, folder):
            return folder
    return None


def matching_label_keyword(label, keywords):
    """Returneaza cuvantul cheie gasit in eticheta (ex. 'sonarr' in 'tv-sonarr') sau None."""
    label = (label or '').strip().lower()
    if not label:
        return None
    for kw in split_keywords(keywords):
        if kw in label:
            return kw
    return None
