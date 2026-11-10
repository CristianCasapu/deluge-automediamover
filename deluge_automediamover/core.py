#
# AutoMediaMover - partea de core (ruleaza in daemonul deluged).
#
import logging
import os

import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

from . import detector

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'enabled': True,
    'movies_path': '',
    'tv_path': '',
    'season_subfolder': True,
    'season_format': 'Season {season:02d}',
    'movie_subfolder': False,
    'strip_year_from_show': False,
    'video_extensions': detector.DEFAULT_VIDEO_EXTENSIONS,
}


def _same_path(a, b):
    try:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
    except Exception:
        return False


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager('automediamover.conf', DEFAULT_PREFS)
        component.get('EventManager').register_event_handler(
            'TorrentFinishedEvent', self._on_torrent_finished
        )

    def disable(self):
        component.get('EventManager').deregister_event_handler(
            'TorrentFinishedEvent', self._on_torrent_finished
        )
        self.config.save()

    def update(self):
        pass

    # ------------------------------------------------------------------ events
    def _on_torrent_finished(self, torrent_id):
        if not self.config['enabled']:
            return
        try:
            self._process(torrent_id)
        except Exception:
            log.exception('AutoMediaMover: error processing torrent %s', torrent_id)

    # ------------------------------------------------------------------ logic
    def _detect(self, name, files):
        return detector.detect(
            name,
            files,
            video_extensions=self.config['video_extensions'],
            strip_year_from_show=self.config['strip_year_from_show'],
        )

    def _destination(self, detection):
        return detector.build_destination(
            detection,
            self.config['movies_path'].strip(),
            self.config['tv_path'].strip(),
            season_subfolder=self.config['season_subfolder'],
            season_format=self.config['season_format'] or 'Season {season:02d}',
            movie_subfolder=self.config['movie_subfolder'],
        )

    def _process(self, torrent_id):
        torrent = component.get('TorrentManager')[torrent_id]
        status = torrent.get_status(['name', 'files', 'save_path', 'is_finished'])
        name = status['name']
        detection = self._detect(name, status.get('files') or [])
        dest = self._destination(detection)
        log.info('AutoMediaMover: "%s" detected as %s', name, detection)

        if not dest:
            return {'torrent_id': torrent_id, 'name': name, 'moved': False,
                    'detection': detection.to_dict(), 'message': 'no destination (unknown type or path not set)'}
        if _same_path(status['save_path'], dest):
            return {'torrent_id': torrent_id, 'name': name, 'moved': False,
                    'detection': detection.to_dict(), 'destination': dest, 'message': 'already in place'}

        try:
            if not os.path.isdir(dest):
                os.makedirs(dest)
        except OSError as ex:
            log.error('AutoMediaMover: cannot create "%s": %s', dest, ex)
            return {'torrent_id': torrent_id, 'name': name, 'moved': False,
                    'detection': detection.to_dict(), 'destination': dest, 'message': str(ex)}

        ok = torrent.move_storage(dest)
        log.info('AutoMediaMover: moving "%s" -> "%s" (%s)', name, dest, 'ok' if ok else 'failed')
        return {'torrent_id': torrent_id, 'name': name, 'moved': bool(ok),
                'detection': detection.to_dict(), 'destination': dest,
                'message': 'moving' if ok else 'move_storage failed'}

    # ------------------------------------------------------------------ RPC
    @export
    def set_config(self, config):
        """Sets the config dictionary."""
        for key in config:
            if key in DEFAULT_PREFS:
                self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config

    @export
    def test_name(self, name):
        """Preview: what would happen with a torrent / file named `name`."""
        detection = self._detect(name, None)
        result = detection.to_dict()
        result['destination'] = self._destination(detection)
        return result

    @export
    def process_torrents(self, torrent_ids):
        """Manually process the given torrents (only finished ones)."""
        results = []
        tm = component.get('TorrentManager')
        for torrent_id in torrent_ids:
            if torrent_id not in tm.torrents:
                continue
            if not tm[torrent_id].get_status(['is_finished'])['is_finished']:
                continue
            try:
                results.append(self._process(torrent_id))
            except Exception as ex:
                log.exception('AutoMediaMover: error processing %s', torrent_id)
                results.append({'torrent_id': torrent_id, 'moved': False, 'message': str(ex)})
        return results

    @export
    def process_all_completed(self):
        """Process every finished torrent in the session."""
        return self.process_torrents(list(component.get('TorrentManager').torrents.keys()))
