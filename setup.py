#
# AutoMediaMover - Deluge 2.x plugin
#
# Build:  python setup.py bdist_egg
#
from setuptools import find_packages, setup

__plugin_name__ = 'AutoMediaMover'
__author__ = 'CristianCasapu'
__author_email__ = ''
__version__ = '1.0'
__url__ = 'https://github.com/CristianCasapu/deluge-automediamover'
__license__ = 'GPLv3'
__description__ = 'Moves finished downloads to a Movies or TV Series/<Show>/ folder automatically'
__long_description__ = """
Detects whether a finished torrent is a movie or a TV series episode / season pack
(S01E02, 1x02, Season 1, Sezonul 1, daily shows, ...) and moves it to the configured
Movies folder or to <TV folder>/<Series name>/[Season XX]/.
Works on Windows and Linux, configurable from the GTK UI and the Web UI.
"""
__pkg_data__ = {'deluge_' + __plugin_name__.lower(): ['data/*']}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__,
    packages=find_packages(exclude=['tests']),
    package_data=__pkg_data__,
    zip_safe=False,
    entry_points="""
    [deluge.plugin.core]
    %s = deluge_%s:CorePlugin
    [deluge.plugin.gtk3ui]
    %s = deluge_%s:GtkUIPlugin
    [deluge.plugin.web]
    %s = deluge_%s:WebUIPlugin
    """
    % ((__plugin_name__, __plugin_name__.lower()) * 3),
)
