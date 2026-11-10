#
# AutoMediaMover - pagina de preferinte in clientul GTK (deluge-gtk).
#
import logging

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa: E402

import deluge.component as component  # noqa: E402
from deluge.plugins.pluginbase import Gtk3PluginBase  # noqa: E402
from deluge.ui.client import client  # noqa: E402

log = logging.getLogger(__name__)

PAGE_NAME = 'AutoMediaMover'


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.prefs_box = self._build_page()
        component.get('Preferences').add_page(PAGE_NAME, self.prefs_box)
        component.get('PluginManager').register_hook('on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').register_hook('on_show_prefs', self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        component.get('Preferences').remove_page(PAGE_NAME)
        component.get('PluginManager').deregister_hook('on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').deregister_hook('on_show_prefs', self.on_show_prefs)
        del self.prefs_box

    # ------------------------------------------------------------------ UI
    def _path_row(self, grid, row, label):
        lbl = Gtk.Label(label=label, xalign=0)
        entry = Gtk.Entry(hexpand=True)
        browse = Gtk.Button(label='...')
        browse.set_tooltip_text('Browse (only when connected to a local daemon)')
        browse.connect('clicked', self._on_browse, entry)
        grid.attach(lbl, 0, row, 1, 1)
        grid.attach(entry, 1, row, 1, 1)
        grid.attach(browse, 2, row, 1, 1)
        return entry, browse

    def _build_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, border_width=5)

        # --- General
        frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        frame.set_label_widget(Gtk.Label(label='<b>General</b>', use_markup=True))
        grid = Gtk.Grid(row_spacing=5, column_spacing=5, margin=5)
        frame.add(grid)

        self.chk_enabled = Gtk.CheckButton(label='Automatically move finished torrents')
        grid.attach(self.chk_enabled, 0, 0, 3, 1)
        self.entry_movies, self.btn_movies = self._path_row(grid, 1, 'Movies folder:')
        self.entry_tv, self.btn_tv = self._path_row(grid, 2, 'TV series folder:')
        box.pack_start(frame, False, False, 0)

        # --- Seriale
        frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        frame.set_label_widget(Gtk.Label(label='<b>TV series</b>', use_markup=True))
        grid = Gtk.Grid(row_spacing=5, column_spacing=5, margin=5)
        frame.add(grid)
        self.chk_season = Gtk.CheckButton(label='Create season sub-folder')
        grid.attach(self.chk_season, 0, 0, 2, 1)
        grid.attach(Gtk.Label(label='Season folder format:', xalign=0), 0, 1, 1, 1)
        self.entry_season_fmt = Gtk.Entry(hexpand=True)
        self.entry_season_fmt.set_tooltip_text(
            'Python format, e.g. "Season {season:02d}" -> Season 01, "Sezonul {season}" -> Sezonul 1'
        )
        grid.attach(self.entry_season_fmt, 1, 1, 1, 1)
        self.chk_strip_year = Gtk.CheckButton(label='Remove year from series name')
        grid.attach(self.chk_strip_year, 0, 2, 2, 1)
        box.pack_start(frame, False, False, 0)

        # --- Filme
        frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        frame.set_label_widget(Gtk.Label(label='<b>Movies</b>', use_markup=True))
        grid = Gtk.Grid(row_spacing=5, column_spacing=5, margin=5)
        frame.add(grid)
        self.chk_movie_sub = Gtk.CheckButton(label='Create "Title (Year)" sub-folder for each movie')
        grid.attach(self.chk_movie_sub, 0, 0, 2, 1)
        box.pack_start(frame, False, False, 0)

        # --- Avansat
        frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        frame.set_label_widget(Gtk.Label(label='<b>Advanced</b>', use_markup=True))
        grid = Gtk.Grid(row_spacing=5, column_spacing=5, margin=5)
        frame.add(grid)
        grid.attach(Gtk.Label(label='Video extensions:', xalign=0), 0, 0, 1, 1)
        self.entry_ext = Gtk.Entry(hexpand=True)
        grid.attach(self.entry_ext, 1, 0, 2, 1)

        grid.attach(Gtk.Label(label='Test a name:', xalign=0), 0, 1, 1, 1)
        self.entry_test = Gtk.Entry(hexpand=True, placeholder_text='The.Office.S03E05.720p.mkv')
        self.entry_test.connect('activate', self._on_test)
        grid.attach(self.entry_test, 1, 1, 1, 1)
        btn_test = Gtk.Button(label='Test')
        btn_test.connect('clicked', self._on_test)
        grid.attach(btn_test, 2, 1, 1, 1)
        self.lbl_test = Gtk.Label(xalign=0, selectable=True, wrap=True)
        grid.attach(self.lbl_test, 0, 2, 3, 1)

        btn_all = Gtk.Button(label='Process all completed torrents now')
        btn_all.connect('clicked', self._on_process_all)
        grid.attach(btn_all, 0, 3, 3, 1)
        box.pack_start(frame, False, False, 0)

        box.show_all()
        return box

    # ------------------------------------------------------------------ handlers
    def _on_browse(self, button, entry):
        dialog = Gtk.FileChooserDialog(
            title='Select folder',
            parent=getattr(component.get('Preferences'), 'pref_dialog', None),
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        if entry.get_text():
            dialog.set_current_folder(entry.get_text())
        if dialog.run() == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        dialog.destroy()

    def _on_test(self, *args):
        name = self.entry_test.get_text().strip()
        if not name:
            return

        def on_result(r):
            if r['kind'] == 'tv':
                txt = 'TV series: "%s", season: %s' % (r['title'], r['season'] if r['season'] is not None else '-')
            elif r['kind'] == 'movie':
                txt = 'Movie: "%s"%s' % (r['title'], ' (%s)' % r['year'] if r['year'] else '')
            else:
                txt = 'Unknown (not a video) - will not be moved'
            txt += '\nDestination: %s' % (r.get('destination') or '- (folder not set)')
            self.lbl_test.set_text(txt)

        # salveaza intai setarile ca testul sa le foloseasca
        client.automediamover.set_config(self._collect()).addCallback(
            lambda _: client.automediamover.test_name(name).addCallback(on_result)
        )

    def _on_process_all(self, *args):
        def on_done(results):
            moved = [r for r in results if r.get('moved')]
            self.lbl_test.set_text('%d torrent(s) moved out of %d finished.' % (len(moved), len(results)))

        client.automediamover.set_config(self._collect()).addCallback(
            lambda _: client.automediamover.process_all_completed().addCallback(on_done)
        )

    def _collect(self):
        return {
            'enabled': self.chk_enabled.get_active(),
            'movies_path': self.entry_movies.get_text().strip(),
            'tv_path': self.entry_tv.get_text().strip(),
            'season_subfolder': self.chk_season.get_active(),
            'season_format': self.entry_season_fmt.get_text().strip() or 'Season {season:02d}',
            'strip_year_from_show': self.chk_strip_year.get_active(),
            'movie_subfolder': self.chk_movie_sub.get_active(),
            'video_extensions': self.entry_ext.get_text().strip(),
        }

    def on_apply_prefs(self):
        log.debug('applying prefs for AutoMediaMover')
        client.automediamover.set_config(self._collect())

    def on_show_prefs(self):
        local = client.is_localhost()
        self.btn_movies.set_visible(local)
        self.btn_tv.set_visible(local)

        def on_get_config(config):
            self.chk_enabled.set_active(config['enabled'])
            self.entry_movies.set_text(config['movies_path'])
            self.entry_tv.set_text(config['tv_path'])
            self.chk_season.set_active(config['season_subfolder'])
            self.entry_season_fmt.set_text(config['season_format'])
            self.chk_strip_year.set_active(config['strip_year_from_show'])
            self.chk_movie_sub.set_active(config['movie_subfolder'])
            self.entry_ext.set_text(config['video_extensions'])

        client.automediamover.get_config().addCallback(on_get_config)
