#
# AutoMediaMover - detectie film / serial.
#
# Modul fara dependente de Deluge, ca sa poata fi testat independent.
#
import os
import re

DEFAULT_VIDEO_EXTENSIONS = (
    'mkv,mp4,avi,m4v,mov,wmv,mpg,mpeg,ts,m2ts,webm,flv,vob,divx,xvid,3gp'
)

MOVIE = 'movie'
TV = 'tv'
UNKNOWN = 'unknown'

_SEP = r'[ ._\-]'

# Tipare ce indica un episod individual (folosite si pe numele fisierelor).
EPISODE_PATTERNS = [
    # S01E02, S01.E02, S01 E02, S01E02E03, s1e2
    re.compile(r'(?i)(?<![a-z0-9])S(?P<season>\d{1,2})' + _SEP + r'?E(?P<episode>\d{1,3})'),
    # 1x02, 01x02  (nu se potriveste pe 1920x1080 datorita lookbehind-ului)
    re.compile(r'(?i)(?<![a-z0-9])(?P<season>\d{1,2})x(?P<episode>\d{2,3})(?![a-z0-9])'),
    # Episode 5, Ep 05, Ep.05, Episodul 5
    re.compile(r'(?i)(?<![a-z0-9])(?:Episode|Episodul|Episod|Ep)' + _SEP + r'*(?P<episode>\d{1,3})(?![0-9])'),
    # Emisiuni zilnice: Show.2023.05.12
    re.compile(
        r'(?<![0-9])(?P<season>(?:19|20)\d{2})' + _SEP
        + r'(?:0[1-9]|1[0-2])' + _SEP + r'(?:0[1-9]|[12]\d|3[01])(?![0-9])'
    ),
]

# Tipare ce indica un pachet de sezon(e) (doar pe numele torrentului).
SEASON_PATTERNS = [
    # S01-S03, S01-03  -> mai multe sezoane, fara subfolder de sezon
    re.compile(
        r'(?i)(?<![a-z0-9])S(?P<season>\d{1,2})' + _SEP + r'*(?:-|to|' + _SEP + r')'
        + _SEP + r'*S?(?P<season_end>\d{1,2})(?![a-z0-9])'
    ),
    # S01
    re.compile(r'(?i)(?<![a-z0-9])S(?P<season>\d{1,2})(?![a-z0-9])'),
    # Season 1, Sezonul 2, Saison 3, Staffel 4, Temporada 5, Stagione 6
    re.compile(
        r'(?i)(?<![a-z0-9])(?:Season|Seasons|Sezonul|Sezonu|Sezon|Saison|Staffel|Temporada|Stagione)'
        + _SEP + r'*(?P<season>\d{1,2})(?:' + _SEP + r'*(?:-|to)' + _SEP + r'*(?P<season_end>\d{1,2}))?(?![0-9])'
    ),
    # Complete Series, Mini-Series, Integrala, TV Series
    re.compile(
        r'(?i)(?<![a-z0-9])(?:Complete' + _SEP + r'Series|The' + _SEP + r'Complete'
        + _SEP + r'Series|Mini' + _SEP + r'?Series|TV' + _SEP + r'Series|Integrala|Serialul)(?![a-z0-9])'
    ),
]

# Etichete de calitate / release dupa care se termina titlul unui film.
_QUALITY_RE = re.compile(
    r'(?i)(?<![a-z0-9])(?:2160p|1080p|1080i|720p|576p|480p|4k|uhd|hdr10?|dv|'
    r'bluray|blu-ray|brrip|bdrip|bdremux|remux|web-?dl|web-?rip|web|hdrip|dvdrip|'
    r'dvdscr|dvd|hdtv|pdtv|cam|ts|telesync|x264|x265|h\.?264|h\.?265|hevc|avc|xvid|'
    r'divx|aac|ac3|dts|ddp?5\.1|atmos|proper|repack|extended|unrated|remastered|'
    r'directors' + _SEP + r'?cut|imax|multi|dual|subbed|dubbed|limited|internal)(?![a-z0-9])'
)
_YEAR_RE = re.compile(r'(?<![0-9])[\(\[]?((?:19|20)\d{2})[\)\]]?(?![0-9])')
_LEADING_TAGS_RE = re.compile(r'^\s*(?:\[[^\]]*\]|\([^\)]*\)|\{[^\}]*\})\s*')
_LEADING_SITE_RE = re.compile(r'(?i)^\s*(?:www\.)?[a-z0-9\-]+\.(?:com|org|net|to|me|cc|ro|info|io|xyz)\s*[-–:]+\s*')
_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}


class Detection(object):
    """Rezultatul detectiei."""

    def __init__(self, kind, title=None, season=None, year=None, reason='', is_pack=False):
        self.kind = kind
        # True = sezon intreg / mai multe episoade, False = un singur episod
        self.is_pack = is_pack
        self.title = title
        self.season = season
        self.year = year
        self.reason = reason

    def to_dict(self):
        return {
            'kind': self.kind,
            'title': self.title,
            'season': self.season,
            'year': self.year,
            'reason': self.reason,
            'is_pack': self.is_pack,
        }

    def __repr__(self):
        return 'Detection(%r)' % self.to_dict()


def parse_extensions(value):
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r'[,;\s]+', value or '')
    return {e.strip().lower().lstrip('.') for e in items if e.strip()}


def is_video(path, extensions):
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    return ext in extensions


def _is_sample(path):
    parts = re.split(r'[\\/]', path.lower())
    return any(
        p in ('sample', 'samples', 'extras', 'featurettes') or re.search(r'(?<![a-z])sample(?![a-z])', p)
        for p in parts
    )


def sanitize_name(name):
    """Face un nume valid de folder atat pe Windows cat si pe Linux."""
    name = _INVALID_CHARS_RE.sub(' ', name or '')
    name = re.sub(r'\s+', ' ', name).strip().rstrip('. ')
    if name.upper() in _WINDOWS_RESERVED:
        name = '_' + name
    return name[:180]


def _strip_leading_junk(name):
    prev = None
    while prev != name:
        prev = name
        name = _LEADING_TAGS_RE.sub('', name)
        name = _LEADING_SITE_RE.sub('', name)
    return name


def clean_title(raw, strip_year=False):
    title = raw or ''
    title = _strip_leading_junk(title)
    # punctele / underscore-urile din release-uri devin spatii
    title = re.sub(r'[._]+', ' ', title)
    # elimina tag-uri ramase intre paranteze patrate
    title = re.sub(r'\[[^\]]*\]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip(' -_([{')
    title = title.strip()
    if strip_year is None:
        pass  # lasa anul neatins (ex. "Blade Runner 2049")
    elif strip_year:
        title = re.sub(r'\s*[\(\[]?(?:19|20)\d{2}[\)\]]?$', '', title).strip(' -')
    else:
        # "Doctor Who 2005" -> "Doctor Who (2005)"
        title = re.sub(r'\s+[\(\[]?((?:19|20)\d{2})[\)\]]?$', r' (\1)', title)
    if title and (title.islower() or title.isupper()):
        title = title.title()
    return sanitize_name(title)


def _strip_video_ext(name, extensions):
    base, ext = os.path.splitext(name)
    if ext.lower().lstrip('.') in extensions:
        return base
    return name


def _match_any(patterns, text):
    best = None
    for pattern in patterns:
        m = pattern.search(text)
        if m and (best is None or m.start() < best.start()):
            best = m
    return best


def _season_from_match(m):
    gd = m.groupdict()
    if gd.get('season_end'):
        return None  # pachet cu mai multe sezoane
    season = gd.get('season')
    if season is None:
        return None
    return int(season)


def _tv_from_name(name, strip_year):
    is_season = False
    m = _match_any(EPISODE_PATTERNS, name)
    if not m:
        m = _match_any(SEASON_PATTERNS, name)
        is_season = True
    if not m:
        return None
    title = clean_title(name[: m.start()], strip_year)
    return m, title, is_season


def _movie_title(name, strip_year):
    text = _strip_leading_junk(name)
    year = None
    cut = len(text)
    # ultimul an plauzibil (evita titluri gen "2001 A Space Odyssey 1968")
    years = [y for y in _YEAR_RE.finditer(text) if y.start() > 0]
    if years:
        y = years[-1]
        year = int(y.group(1))
        cut = y.start()
    q = _QUALITY_RE.search(text)
    if q and q.start() > 0 and q.start() < cut:
        cut = q.start()
    title = clean_title(text[:cut], strip_year=None)
    if not title:
        title = clean_title(text, strip_year=None)
    return title, year


def detect(name, files=None, video_extensions=DEFAULT_VIDEO_EXTENSIONS, strip_year_from_show=False):
    """Detecteaza daca un torrent este film sau serial.

    :param name: numele torrentului
    :param files: lista de cai relative (str) sau dict-uri Deluge cu cheia 'path'
    :returns: Detection
    """
    extensions = parse_extensions(video_extensions)
    paths = []
    for f in files or []:
        paths.append(f['path'] if isinstance(f, dict) else f)
    if not paths:
        # fara lista de fisiere (ex. testul din UI): numele e considerat video
        paths = [name if is_video(name, extensions) else name + '.mkv']

    videos = [p for p in paths if is_video(p, extensions) and not _is_sample(p)]
    if not videos:
        videos_with_samples = [p for p in paths if is_video(p, extensions)]
        if not videos_with_samples:
            return Detection(UNKNOWN, reason='no video files')
        videos = videos_with_samples

    base_name = _strip_video_ext(name, extensions)

    episode_files = []
    for p in videos:
        fname = _strip_video_ext(os.path.basename(p.replace('\\', '/')), extensions)
        m = _match_any(EPISODE_PATTERNS, fname)
        if m:
            episode_files.append((p, fname, m))

    # 1. Numele torrentului contine un tipar de serial
    found = _tv_from_name(base_name, strip_year_from_show)
    if found:
        m, title, is_season = found
        season = _season_from_match(m)
        # sezon intreg: tipar de sezon (S01, Season 1, ...) sau mai multe episoade in torrent
        is_pack = is_season or len(episode_files) >= 2
        if not title:
            # ex. "Season 1" -> incearca dintr-un nume de fisier / folder
            title = _title_from_files(videos, extensions, strip_year_from_show)
        if title:
            return Detection(TV, title=title, season=season, is_pack=is_pack,
                             reason='torrent name matches "%s"' % m.group(0))

    # 2. Majoritatea fisierelor video arata ca episoade
    if episode_files and (len(episode_files) >= 2 or len(videos) == 1) and len(episode_files) * 2 >= len(videos):
        p, fname, m = episode_files[0]
        title = clean_title(fname[: m.start()], strip_year_from_show)
        if not title:
            title = clean_title(base_name, strip_year_from_show)
        seasons = {_season_from_match(e[2]) for e in episode_files}
        season = seasons.pop() if len(seasons) == 1 else None
        if title:
            return Detection(TV, title=title, season=season, is_pack=len(episode_files) >= 2,
                             reason='%d episode-like video files' % len(episode_files))

    # 3. Altfel e film
    title, year = _movie_title(base_name, strip_year_from_show)
    return Detection(MOVIE, title=title or sanitize_name(base_name), year=year, reason='video without episode pattern')


def _title_from_files(videos, extensions, strip_year):
    for p in videos:
        parts = [x for x in re.split(r'[\\/]', p) if x]
        for part in parts:
            part = _strip_video_ext(part, extensions)
            found = _tv_from_name(part, strip_year)
            if found and found[1]:
                return found[1]
    return None


def build_destination(detection, movies_path, tv_path, season_subfolder=True,
                      season_format='Season {season:02d}', movie_subfolder=False):
    """Calculeaza folderul destinatie sau None daca nu trebuie mutat."""
    if detection.kind == TV:
        if not tv_path:
            return None
        dest = os.path.join(tv_path, detection.title)
        # folder de sezon doar pentru episoade individuale; un sezon intreg
        # vine deja in propriul folder de torrent -> <Serial>/<folder torrent>/
        if season_subfolder and detection.season is not None and not detection.is_pack:
            try:
                season_dir = season_format.format(season=detection.season)
            except (KeyError, IndexError, ValueError):
                season_dir = 'Season %02d' % detection.season
            season_dir = sanitize_name(season_dir)
            if season_dir:
                dest = os.path.join(dest, season_dir)
        return os.path.normpath(dest)
    if detection.kind == MOVIE:
        if not movies_path:
            return None
        dest = movies_path
        if movie_subfolder and detection.title:
            folder = detection.title
            if detection.year:
                folder = '%s (%d)' % (folder, detection.year)
            dest = os.path.join(dest, sanitize_name(folder))
        return os.path.normpath(dest)
    return None
