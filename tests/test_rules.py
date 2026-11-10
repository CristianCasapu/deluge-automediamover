"""Teste pentru regulile de ignorare.  Rulare:  python tests/test_rules.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deluge_automediamover'))

import rules  # noqa: E402


def test_labels():
    kw = rules.DEFAULT_SKIP_LABELS
    assert rules.matching_label_keyword('radarr', kw) == 'radarr'
    assert rules.matching_label_keyword('tv-sonarr', kw) == 'sonarr'
    assert rules.matching_label_keyword('Radarr-4K', kw) == 'radarr'
    assert rules.matching_label_keyword('movies', kw) is None
    assert rules.matching_label_keyword('', kw) is None
    assert rules.matching_label_keyword(None, kw) is None
    assert rules.matching_label_keyword('sonarr', '') is None  # dezactivat
    assert rules.matching_label_keyword('manual', 'manual; private') == 'manual'


def test_paths_inside():
    base = os.path.abspath('media')
    tv = os.path.join(base, 'TV')
    assert rules.path_is_inside(tv, tv)
    assert rules.path_is_inside(os.path.join(tv, 'Show', 'Season 01'), tv)
    assert rules.path_is_inside(os.path.join(tv, 'Show') + os.sep, tv + os.sep)
    # prefix comun, dar alt folder
    assert not rules.path_is_inside(os.path.join(base, 'TV Shows'), tv)
    assert not rules.path_is_inside(os.path.join(base, 'Downloads'), tv)
    assert not rules.path_is_inside(tv, '')
    assert not rules.path_is_inside('', tv)
    if os.name == 'nt':
        assert rules.path_is_inside(r'd:\media\tv\show', r'D:\Media\TV')


def test_split():
    assert rules.split_paths('D:\\a, b;E:\\c\n/mnt/x') == ['D:\\a, b', 'E:\\c', '/mnt/x']
    assert rules.split_keywords('Radarr, sonarr;  ') == ['radarr', 'sonarr']
    m = os.path.abspath('m')
    assert rules.matching_folder(os.path.join(m, 'x'), ['', os.path.abspath('t'), m]) == m
    assert rules.matching_folder(os.path.abspath('dl'), ['', m]) is None


if __name__ == '__main__':
    failures = 0
    for fn_name, fn in list(globals().items()):
        if fn_name.startswith('test_') and callable(fn):
            try:
                fn()
                print('PASS', fn_name)
            except AssertionError as ex:
                failures += 1
                print('FAIL', fn_name, ex)
    sys.exit(1 if failures else 0)
