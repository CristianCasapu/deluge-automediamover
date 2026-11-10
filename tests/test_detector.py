"""Teste pentru detectia film / serial.  Rulare:  python -m pytest tests  (sau python tests/test_detector.py)"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deluge_automediamover'))

import detector  # noqa: E402

TV_CASES = [
    ('The.Office.US.S03E05.720p.HDTV.x264-GRP.mkv', 'The Office US', 3),
    ('Breaking Bad S05E14 1080p BluRay', 'Breaking Bad', 5),
    ('game.of.thrones.s08e03.1080p.web.h264-memento', 'Game Of Thrones', 8),
    ('Friends.1x02.DVDRip.avi', 'Friends', 1),
    ('Stranger Things Season 4 Complete 1080p', 'Stranger Things', 4),
    ('Las Fierbinti Sezonul 12 Integral', 'Las Fierbinti', 12),
    ('The.Wire.S01-S05.COMPLETE.720p', 'The Wire', None),
    ('Chernobyl.S01.1080p.BluRay.x265', 'Chernobyl', 1),
    ('[SubsPlease] Frieren - Episode 12 (1080p)', 'Frieren', None),
    ('The.Daily.Show.2024.03.14.720p.WEB.h264', 'The Daily Show', 2024),
    ('Doctor.Who.2005.S13E01.1080p', 'Doctor Who (2005)', 13),
    ('Band.of.Brothers.Complete.Series.1080p', 'Band of Brothers', None),
]

MOVIE_CASES = [
    ('Inception.2010.1080p.BluRay.x264-SPARKS', 'Inception', 2010),
    ('The Matrix (1999) 2160p UHD BluRay', 'The Matrix', 1999),
    ('Blade.Runner.2049.2017.2160p.WEB-DL.mkv', 'Blade Runner 2049', 2017),
    ('2001.A.Space.Odyssey.1968.1080p.BluRay', '2001 A Space Odyssey', 1968),
    ('Oppenheimer.1080p.WEBRip.x265', 'Oppenheimer', None),
    ('www.TamilBlasters.com - Dune Part Two (2024) 1080p', 'Dune Part Two', 2024),
]


def test_tv():
    for name, title, season in TV_CASES:
        d = detector.detect(name)
        assert d.kind == detector.TV, (name, d)
        assert d.title == title, (name, d)
        assert d.season == season, (name, d)


def test_movies():
    for name, title, year in MOVIE_CASES:
        files = [name if name.endswith('.mkv') else name + '/' + name + '.mkv']
        d = detector.detect(name, files)
        assert d.kind == detector.MOVIE, (name, d)
        assert d.title == title, (name, d)
        assert d.year == year, (name, d)


def test_tv_from_files_only():
    files = [
        'Some Pack/Show Name - 1x01 - Pilot.mkv',
        'Some Pack/Show Name - 1x02 - Second.mkv',
        'Some Pack/Show Name - 1x03 - Third.mkv',
    ]
    d = detector.detect('Some Pack', files)
    assert d.kind == detector.TV and d.title == 'Show Name' and d.season == 1, d


def test_movie_with_sample():
    files = ['Movie.2020.1080p/Movie.2020.1080p.mkv', 'Movie.2020.1080p/Sample/sample-movie.s01e01.mkv']
    d = detector.detect('Movie.2020.1080p', files)
    assert d.kind == detector.MOVIE, d


def test_unknown():
    d = detector.detect('Ubuntu 24.04 ISO', ['ubuntu.iso', 'readme.txt'])
    assert d.kind == detector.UNKNOWN


def test_resolution_not_episode():
    d = detector.detect('Some.Movie.2019.1920x1080.mkv')
    assert d.kind == detector.MOVIE, d


def test_episode_vs_season_pack():
    tv = '/tv'
    # un singur episod -> <Serial>/Season XX/
    d = detector.detect('Chernobyl.S01E02.1080p.mkv', ['Chernobyl.S01E02.1080p.mkv'])
    assert not d.is_pack, d
    assert detector.build_destination(d, '/m', tv) == os.path.normpath('/tv/Chernobyl/Season 01')
    # episod intr-un folder (cu .nfo) -> tot episod
    d = detector.detect('Chernobyl.S01E02.1080p', ['Chernobyl.S01E02.1080p/ep.S01E02.mkv', 'Chernobyl.S01E02.1080p/x.nfo'])
    assert not d.is_pack, d
    # sezon intreg (S01) -> direct in <Serial>/, torrentul isi pastreaza folderul
    files = ['Chernobyl.S01.1080p/Chernobyl.S01E0%d.mkv' % i for i in range(1, 6)]
    d = detector.detect('Chernobyl.S01.1080p', files)
    assert d.is_pack and d.season == 1, d
    assert detector.build_destination(d, '/m', tv) == os.path.normpath('/tv/Chernobyl')
    # "Season 1" / "Sezonul 2" -> sezon intreg
    for name in ('Stranger Things Season 4 1080p', 'Las Fierbinti Sezonul 12'):
        d = detector.detect(name)
        assert d.is_pack, d
    # pachet fara tipar in nume, doar episoade in fisiere -> sezon intreg
    d = detector.detect('Some Pack', ['Some Pack/Show - 1x01.mkv', 'Some Pack/Show - 1x02.mkv'])
    assert d.is_pack, d
    # nume de episod, dar torrentul contine mai multe episoade (S01E01-E10)
    d = detector.detect('Show.S01E01-E03', ['Show.S01E01-E03/Show.S01E01.mkv', 'Show.S01E01-E03/Show.S01E02.mkv'])
    assert d.is_pack, d


def test_destination():
    d = detector.detect('The.Office.US.S03E05.720p.mkv')
    dest = detector.build_destination(d, '/m', '/tv', True, 'Season {season:02d}')
    assert dest == os.path.normpath('/tv/The Office US/Season 03')
    dest = detector.build_destination(d, '/m', '/tv', True, 'Sezonul {season}')
    assert dest == os.path.normpath('/tv/The Office US/Sezonul 3')
    m = detector.detect('Inception.2010.1080p.mkv')
    assert detector.build_destination(m, '/m', '/tv') == os.path.normpath('/m')
    assert detector.build_destination(m, '/m', '/tv', movie_subfolder=True) == os.path.normpath('/m/Inception (2010)')
    assert detector.build_destination(m, '', '/tv') is None


def test_sanitize():
    assert detector.sanitize_name('What If...?: Part 1.') == 'What If... Part 1'
    assert detector.sanitize_name('CON') == '_CON'


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
