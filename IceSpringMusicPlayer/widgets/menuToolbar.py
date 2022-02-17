# Created by BaiJiFeiLong@gmail.com at 2022/2/15 13:31
from __future__ import annotations

import logging
import typing

from IceSpringRealOptional.just import Just
from PySide2 import QtGui, QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.toolbarMixin import ToolbarMixin
from IceSpringMusicPlayer.common.widgetMixin import WidgetMixin
from IceSpringMusicPlayer.enums.playbackMode import PlaybackMode
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.utils.signalUtils import SignalUtils
from IceSpringMusicPlayer.windows.configDialog import ConfigDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class MenuToolbar(QtWidgets.QToolBar, ToolbarMixin, WidgetMixin):
    @classmethod
    def getToolbarTitle(cls) -> Text:
        return tt.Toolbar_Menu

    def __init__(self, parent: MainWindow):
        super().__init__()
        self._logger = logging.getLogger("menuToolbar")
        self._app = App.instance()
        self._config = self._app.getConfig()
        self._mainWindow = parent
        self._player = App.instance().getPlayer()
        self._playlistService = App.instance().getPlaylistService()
        self._configService = App.instance().getConfigService()
        self._pluginService = App.instance().getPluginService()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._app.languageChanged.connect(self._refreshView)
        self._player.stateChanged.connect(self._refreshPlaybackMenu)
        self._player.playbackModeChanged.connect(self._refreshPlaybackMenu)
        self._pluginService.pluginsInserted.connect(self._refreshMenus)
        self._pluginService.pluginsRemoved.connect(self._refreshMenus)
        self._pluginService.pluginEnabled.connect(self._refreshMenus)
        self._pluginService.pluginDisabled.connect(self._refreshMenus)
        self._mainWindow.layoutEditingChanged.connect(self._onLayoutEditingChanged)

    def _onLayoutEditingChanged(self, editing: bool):
        self._logger.info("On layout editing changed: %s", editing)
        self._layoutEditingAction.blockSignals(True)
        self._layoutEditingAction.setChecked(editing)
        self._layoutEditingAction.blockSignals(False)

    def _setupView(self):
        self.setStyleSheet("QToolButton::menu-indicator { image: none }")
        self.installEventFilter(StatusTipFilter(self))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#F9F9F9"))
        for menu in self._setupMenus():
            menu.setPalette(palette)
            button = QtWidgets.QToolButton()
            button.setMenu(menu)
            button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            button.sizeHint = SignalUtils.gcSlot(button,
                lambda self: Just.of(QtWidgets.QToolButton.sizeHint(self)).apply(
                    lambda x: x.setWidth(round(x.width() * 0.8))).value())
            menu.mouseMoveEvent = SignalUtils.gcSlot(menu,
                lambda self, event, slot=self._onMouseMove: slot(self, event))
            menu.setProperty("__button", button)
            self.addWidget(button)

    def _refreshView(self):
        self._refreshMenus()
        for button in self.findChildren(QtWidgets.QToolButton):
            if button.menu() is not None:
                button.setText(button.menu().title())

    @staticmethod
    def _onMouseMove(menu: QtWidgets.QMenu, event: QtGui.QMouseEvent):
        button = menu.property("__button")
        toolbar = button.parentWidget()
        hover = toolbar.childAt(toolbar.mapFromGlobal(QtGui.QCursor.pos()))
        if isinstance(hover, QtWidgets.QToolButton) and hover != button:
            menu.close()
            hover.showMenu()
        else:
            return QtWidgets.QMenu.mouseMoveEvent(menu, event)

    @staticmethod
    def _onMouseMoveX(self, menu: QtWidgets.QMenu, event: QtGui.QMouseEvent, button: QtWidgets.QToolButton):
        hover = self.childAt(self.mapFromGlobal(QtGui.QCursor.pos()))
        if isinstance(hover, QtWidgets.QToolButton) and hover != button:
            menu.close()
            hover.showMenu()
        else:
            return QtWidgets.QMenu.mouseMoveEvent(menu, event)

    # noinspection DuplicatedCode
    def _setupMenus(self):
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
        app = self._app
        mainWindow = self._mainWindow
        playlistService = self._playlistService
        configService = self._configService
        config = self._config

        self._addFilesAction = QtWidgets.QAction()
        self._addFilesAction.triggered.connect(self._playlistService.addMusicsFromFileDialog)
        self._addFolderAction = QtWidgets.QAction()
        self._addFolderAction.triggered.connect(self._playlistService.addMusicsFromFolderDialog)
        self._configAction = QtWidgets.QAction()
        self._configAction.triggered.connect(lambda: ConfigDialog().exec_())
        self._fileMenu = QtWidgets.QMenu()
        self._fileMenu.addAction(self._addFilesAction)
        self._fileMenu.addAction(self._addFolderAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._configAction)

        self._selectAllAction = QtWidgets.QAction()
        self._selectAllAction.triggered.connect(self._player.selectAllMusics)
        self._removeSelectionAction = QtWidgets.QAction()
        self._removeSelectionAction.triggered.connect(self._player.removeSelectedMusics)
        self._editMenu = QtWidgets.QMenu()
        self._editMenu.addAction(self._selectAllAction)
        self._editMenu.addAction(self._removeSelectionAction)

        self._sortByArtistAction = QtWidgets.QAction()
        self._sortByArtistAction.triggered.connect(
            lambda *args, player=self._player: player.sortMusics(key=lambda x: x.artist))
        self._sortByTitleAction = QtWidgets.QAction()
        self._sortByTitleAction.triggered.connect(
            lambda *args, player=self._player: player.sortMusics(key=lambda x: x.title))
        self._sortByMenu = QtWidgets.QMenu()
        self._sortByMenu.addAction(self._sortByArtistAction)
        self._sortByMenu.addAction(self._sortByTitleAction)

        self._playlistManagerAction = QtWidgets.QAction()
        self._playlistManagerAction.triggered.connect(
            lambda: DialogUtils.execWidget(PlaylistManagerWidget(), withOk=True))
        self._resetToolbarsAction = QtWidgets.QAction()
        self._resetToolbarsAction.triggered.connect(self._mainWindow.resetToolbars)
        self._resetLayoutAction = QtWidgets.QAction()
        self._resetLayoutAction.triggered.connect(
            lambda: mainWindow.changeLayout(configService.getDefaultLayout()))
        self._layoutEditingAction = QtWidgets.QAction()
        self._layoutEditingAction.setCheckable(True)
        self._layoutEditingAction.setChecked(self._mainWindow.getLayoutEditing())
        self._layoutEditingAction.triggered.connect(self._mainWindow.toggleLayoutEditing)
        self._viewMenu = QtWidgets.QMenu()
        self._viewMenu.addMenu(self._sortByMenu)
        self._viewMenu.addSeparator()
        self._viewMenu.addAction(self._playlistManagerAction)
        self._viewMenu.addSeparator()
        self._viewMenu.addAction(self._resetToolbarsAction)
        self._viewMenu.addAction(self._resetLayoutAction)
        self._viewMenu.addSeparator()
        self._viewMenu.addAction(self._layoutEditingAction)

        self._playbackModeMenu = QtWidgets.QMenu()
        for mode in PlaybackMode:
            action = QtWidgets.QAction(self._playbackModeMenu)
            action.setCheckable(True)
            action.triggered.connect(lambda *args, player=self._player, mode=mode: player.setPlaybackMode(mode))
            action.setData(mode)
            self._playbackModeMenu.addAction(action)
        self._playPauseAction = QtWidgets.QAction()
        self._playPauseAction.triggered.connect(self._player.togglePlayPause)
        self._stopAction = QtWidgets.QAction()
        self._stopAction.triggered.connect(self._player.stop)
        self._previousAction = QtWidgets.QAction()
        self._previousAction.triggered.connect(self._player.playPrevious)
        self._nextAction = QtWidgets.QAction()
        self._nextAction.triggered.connect(self._player.playNext)
        self._playbackMenu = QtWidgets.QMenu()
        self._playbackMenu.addAction(self._playPauseAction)
        self._playbackMenu.addAction(self._stopAction)
        self._playbackMenu.addAction(self._previousAction)
        self._playbackMenu.addAction(self._nextAction)
        self._playbackMenu.addSeparator()
        self._playbackMenu.addMenu(self._playbackModeMenu)

        self._pluginsMenu = QtWidgets.QMenu()

        self._englishAction = QtWidgets.QAction()
        self._englishAction.triggered.connect(lambda: app.changeLanguage("en_US"))
        self._chineseAction = QtWidgets.QAction()
        self._chineseAction.triggered.connect(lambda: app.changeLanguage("zh_CN"))
        self._languageMenu = QtWidgets.QMenu()
        self._languageMenu.addAction(self._englishAction)
        self._languageMenu.addAction(self._chineseAction)

        self._oneKeyAddAction = QtWidgets.QAction()
        self._oneKeyAddAction.triggered.connect(lambda: playlistService.addMusicsFromFolder("~/Music"))
        self._loadTestDataAction = QtWidgets.QAction()
        self._loadTestDataAction.triggered.connect(lambda: playlistService.loadTestData())
        self._toggleLanguageAction = QtWidgets.QAction()
        self._toggleLanguageAction.triggered.connect(
            lambda: app.changeLanguage("zh_CN" if config.language == "en_US" else "en_US"))
        self._testMenu = QtWidgets.QMenu()
        self._testMenu.addAction(self._oneKeyAddAction)
        self._testMenu.addAction(self._loadTestDataAction)
        self._testMenu.addAction(self._toggleLanguageAction)

        self._aboutAction = QtWidgets.QAction()
        self._aboutAction.triggered.connect(self.gcSlot(lambda self: QtWidgets.QMessageBox.about(
            self.parentWidget(), tt.HelpMenu_AboutTitle, tt.HelpMenu_AboutText)))
        self._helpMenu = QtWidgets.QMenu()
        self._helpMenu.addMenu(self._languageMenu)
        self._helpMenu.addMenu(self._testMenu)
        self._helpMenu.addAction(self._aboutAction)

        return [self._fileMenu, self._editMenu, self._viewMenu, self._playbackMenu, self._pluginsMenu, self._helpMenu]

    # noinspection DuplicatedCode
    def _refreshPlaybackMenu(self):
        playing = self._player.getState().isPlaying()
        self._playPauseAction.setText(tt.PlaybackMenu_Pause if playing else tt.PlaybackMenu_Play)
        self._stopAction.setText(tt.PlaybackMenu_Stop)
        self._previousAction.setText(tt.PlaybackMenu_Previous)
        self._nextAction.setText(tt.PlaybackMenu_Next)
        self._playbackModeMenu.setTitle(tt.PlaybackModeMenu)
        modeDict = {
            PlaybackMode.LOOP: tt.PlaybackModeMenu_Loop,
            PlaybackMode.RANDOM: tt.PlaybackModeMenu_Random,
            PlaybackMode.REPEAT: tt.PlaybackModeMenu_Repeat,
        }
        for action in self._playbackModeMenu.actions():
            action.setText(modeDict[action.data()])
            action.setChecked(self._player.getPlaybackMode() == action.data())

    # noinspection DuplicatedCode
    def _refreshMenus(self):
        self._fileMenu.setTitle(tt.FileMenu)
        self._addFilesAction.setText(tt.FileMenu_AddFiles)
        self._addFolderAction.setText(tt.FileMenu_AddFolder)
        self._configAction.setText(tt.FileMenu_Config)

        self._editMenu.setTitle(tt.EditMenu)
        self._selectAllAction.setText(tt.EditMenu_SelectAll)
        self._removeSelectionAction.setText(tt.EditMenu_RemoveSelection)

        self._viewMenu.setTitle(tt.ViewMenu)
        self._playlistManagerAction.setText(tt.ViewMenu_PlaylistManager)
        self._resetToolbarsAction.setText(tt.LayoutMenu_ResetToolbars)
        self._resetLayoutAction.setText(tt.LayoutMenu_ResetLayout)
        self._layoutEditingAction.setText(tt.Toolbar_Editing)
        self._sortByMenu.setTitle(tt.SortByMenu)
        self._sortByArtistAction.setText(tt.SortByMenu_Artist)
        self._sortByTitleAction.setText(tt.SortByMenu_Title)

        self._playbackMenu.setTitle(tt.PlaybackMenu)
        self._refreshPlaybackMenu()

        self._pluginsMenu.setTitle(tt.PluginsMenu)
        self._setupPluginsMenu()

        self._languageMenu.setTitle(tt.LanguageMenu)
        self._englishAction.setText(tt.LanguageMenu_English)
        self._chineseAction.setText(tt.LanguageMenu_Chinese)

        self._testMenu.setTitle(tt.TestMenu)
        self._oneKeyAddAction.setText(tt.TestMenu_OneKeyAdd)
        self._loadTestDataAction.setText(tt.TestMenu_LoadTestData)
        self._toggleLanguageAction.setText(tt.TestMenu_ToggleLanguage)

        self._helpMenu.setTitle(tt.HelpMenu)
        self._aboutAction.setText(tt.HelpMenu_About)

    def _setupPluginsMenu(self):
        self._pluginsMenu.clear()
        self._pluginsMenu.setTitle(tt.PluginsMenu)
        for plugin in self._config.plugins:
            items = plugin.clazz.getPluginMenus()
            if not plugin.disabled:
                menu = self._pluginsMenu.addMenu(plugin.clazz.getPluginName())
                menu.addAction(tt.PluginsMenu_AboutPlugin,
                    lambda plugin=plugin: QtWidgets.QMessageBox.about(QtWidgets.QApplication.activeWindow(),
                        tt.PluginsMenu_AboutPlugin, plugin.clazz.getPluginDescription()))
                for item in items:
                    item.setParent(menu)
                    if isinstance(item, QtWidgets.QMenu):
                        menu.addMenu(item)
                    else:
                        assert isinstance(item, QtWidgets.QAction)
                        menu.addAction(item)


class StatusTipFilter(QtCore.QObject):
    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if isinstance(event, QtGui.QStatusTipEvent):
            return True
        return super().eventFilter(watched, event)
