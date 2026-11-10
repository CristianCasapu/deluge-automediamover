/**
 * AutoMediaMover - pagina de preferinte in interfata web (deluge-web).
 */
Ext.ns('Deluge.ux.preferences');

Deluge.ux.preferences.AutoMediaMoverPage = Ext.extend(Ext.Panel, {
    title: _('AutoMediaMover'),
    header: false,
    layout: 'fit',
    border: false,
    autoScroll: true,

    initComponent: function () {
        Deluge.ux.preferences.AutoMediaMoverPage.superclass.initComponent.call(this);

        this.form = this.add({
            xtype: 'form',
            layout: 'form',
            border: false,
            autoHeight: true,
            autoScroll: true,
        });

        // --- General
        var fs = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('General'),
            autoHeight: true,
            labelAlign: 'top',
            defaultType: 'textfield',
        });
        this.enabled = fs.add({
            xtype: 'checkbox',
            name: 'enabled',
            height: 22,
            hideLabel: true,
            boxLabel: _('Automatically move finished torrents'),
        });
        this.movies_path = fs.add({
            fieldLabel: _('Movies folder (path on the daemon machine)'),
            labelSeparator: '',
            name: 'movies_path',
            width: '97%',
        });
        this.tv_path = fs.add({
            fieldLabel: _('TV series folder (path on the daemon machine)'),
            labelSeparator: '',
            name: 'tv_path',
            width: '97%',
        });

        // --- Seriale
        fs = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('TV series'),
            autoHeight: true,
            labelAlign: 'top',
            defaultType: 'textfield',
        });
        this.season_subfolder = fs.add({
            xtype: 'checkbox',
            name: 'season_subfolder',
            height: 22,
            hideLabel: true,
            boxLabel: _('Create season sub-folder for single episodes (full seasons keep their own folder)'),
        });
        this.season_format = fs.add({
            fieldLabel: _('Season folder format (e.g. "Season {season:02d}" or "Sezonul {season}")'),
            labelSeparator: '',
            name: 'season_format',
            width: '97%',
        });
        this.strip_year = fs.add({
            xtype: 'checkbox',
            name: 'strip_year_from_show',
            height: 22,
            hideLabel: true,
            boxLabel: _('Remove year from series name'),
        });

        // --- Filme
        fs = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Movies'),
            autoHeight: true,
            labelAlign: 'top',
        });
        this.movie_subfolder = fs.add({
            xtype: 'checkbox',
            name: 'movie_subfolder',
            height: 22,
            hideLabel: true,
            boxLabel: _('Create "Title (Year)" sub-folder for each movie'),
        });

        // --- Avansat
        fs = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Advanced'),
            autoHeight: true,
            labelAlign: 'top',
            defaultType: 'textfield',
        });
        this.video_extensions = fs.add({
            fieldLabel: _('Video extensions (comma separated)'),
            labelSeparator: '',
            name: 'video_extensions',
            width: '97%',
        });
        this.test_name = fs.add({
            fieldLabel: _('Test a name'),
            labelSeparator: '',
            name: 'test_name',
            width: '97%',
            emptyText: 'The.Office.S03E05.720p.mkv',
            enableKeyEvents: true,
            listeners: {
                specialkey: function (field, e) {
                    if (e.getKey() == e.ENTER) this.onTest();
                },
                scope: this,
            },
        });
        fs.add({
            xtype: 'container',
            layout: 'hbox',
            border: false,
            height: 30,
            items: [
                {
                    xtype: 'button',
                    text: _('Test'),
                    handler: this.onTest,
                    scope: this,
                },
                { xtype: 'spacer', width: 8 },
                {
                    xtype: 'button',
                    text: _('Process all completed torrents now'),
                    handler: this.onProcessAll,
                    scope: this,
                },
            ],
        });
        this.result = fs.add({
            xtype: 'label',
            html: '',
            style: 'display:block; padding-top:6px; white-space:pre-wrap;',
        });

        this.on('show', this.updateConfig, this);
    },

    getConfig: function () {
        return {
            enabled: this.enabled.getValue(),
            movies_path: this.movies_path.getValue().trim(),
            tv_path: this.tv_path.getValue().trim(),
            season_subfolder: this.season_subfolder.getValue(),
            season_format: this.season_format.getValue().trim() || 'Season {season:02d}',
            strip_year_from_show: this.strip_year.getValue(),
            movie_subfolder: this.movie_subfolder.getValue(),
            video_extensions: this.video_extensions.getValue().trim(),
        };
    },

    setResult: function (text) {
        this.result.setText(Ext.util.Format.htmlEncode(text).replace(/\n/g, '<br/>'), false);
    },

    onTest: function () {
        var name = this.test_name.getValue().trim();
        if (!name) return;
        deluge.client.automediamover.set_config(this.getConfig(), {
            success: function () {
                deluge.client.automediamover.test_name(name, {
                    success: function (r) {
                        var txt;
                        if (r.kind == 'tv') {
                            txt = _('TV series') + ' (' + (r.is_pack ? _('full season') : _('episode')) + '): "' +
                                r.title + '", ' + _('season') + ': ' +
                                (r.season === null ? '-' : r.season);
                        } else if (r.kind == 'movie') {
                            txt = _('Movie') + ': "' + r.title + '"' + (r.year ? ' (' + r.year + ')' : '');
                        } else {
                            txt = _('Unknown (not a video) - will not be moved');
                        }
                        txt += '\n' + _('Destination') + ': ' + (r.destination || _('- (folder not set)'));
                        this.setResult(txt);
                    },
                    scope: this,
                });
            },
            scope: this,
        });
    },

    onProcessAll: function () {
        deluge.client.automediamover.set_config(this.getConfig(), {
            success: function () {
                deluge.client.automediamover.process_all_completed({
                    success: function (results) {
                        var moved = 0;
                        Ext.each(results, function (r) {
                            if (r.moved) moved++;
                        });
                        this.setResult(moved + ' ' + _('torrent(s) moved out of') + ' ' +
                            results.length + ' ' + _('finished.'));
                    },
                    scope: this,
                });
            },
            scope: this,
        });
    },

    onApply: function () {
        deluge.client.automediamover.set_config(this.getConfig());
    },

    onOk: function () {
        this.onApply();
    },

    updateConfig: function () {
        deluge.client.automediamover.get_config({
            success: function (config) {
                this.enabled.setValue(config['enabled']);
                this.movies_path.setValue(config['movies_path']);
                this.tv_path.setValue(config['tv_path']);
                this.season_subfolder.setValue(config['season_subfolder']);
                this.season_format.setValue(config['season_format']);
                this.strip_year.setValue(config['strip_year_from_show']);
                this.movie_subfolder.setValue(config['movie_subfolder']);
                this.video_extensions.setValue(config['video_extensions']);
            },
            scope: this,
        });
    },
});

Deluge.plugins.AutoMediaMoverPlugin = Ext.extend(Deluge.Plugin, {
    name: 'AutoMediaMover',

    onDisable: function () {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function () {
        this.prefsPage = deluge.preferences.addPage(
            new Deluge.ux.preferences.AutoMediaMoverPage()
        );
    },
});

Deluge.registerPlugin('AutoMediaMover', Deluge.plugins.AutoMediaMoverPlugin);
