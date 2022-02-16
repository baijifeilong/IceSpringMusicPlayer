# Created by BaiJiFeiLong@gmail.com at 2022/2/15 13:31
from __future__ import annotations

import logging
import typing

from IceSpringRealOptional.just import Just
from PySide2 import QtGui, QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.toolbarMixin import ToolbarMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.utils.signalUtils import SignalUtils
from IceSpringMusicPlayer.windows.configDialog import ConfigDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class MenuToolbar(QtWidgets.QToolBar, ToolbarMixin):
    @classmethod
    def getToolbarTitle(cls) -> Text:
        return tt.Toolbar_Menu

    def __init__(self, parent: MainWindow):
        super().__init__()
        self._logger = logging.getLogger("menuToolbar")
        self._app = App.instance()
        self._config = self._app.getConfig()
        self._mainWindow = parent
        self._playlistService = App.instance().getPlaylistService()
        self._configService = App.instance().getConfigService()
        self._pluginService = App.instance().getPluginService()
        self._setupView()
        self._refreshView()
        self._setupEvents()

    def _setupEvents(self):
        self._app.languageChanged.connect(self._refreshView)
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
        for menu in self._setupMenus():
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

    def _setupMenus(self):
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
        app = self._app
        mainWindow = self._mainWindow
        playlistService = self._playlistService
        configService = self._configService
        config = self._config

        self._openAction = QtWidgets.QAction()
        self._openAction.triggered.connect(self._playlistService.addMusicsFromFileDialog)
        self._configAction = QtWidgets.QAction()
        self._configAction.triggered.connect(lambda: ConfigDialog().exec_())
        self._fileMenu = QtWidgets.QMenu()
        self._fileMenu.addAction(self._openAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._configAction)

        self._playlistManagerAction = QtWidgets.QAction()
        self._playlistManagerAction.triggered.connect(
            lambda: DialogUtils.execWidget(PlaylistManagerWidget(), withOk=True))
        self._viewMenu = QtWidgets.QMenu()
        self._viewMenu.addAction(self._playlistManagerAction)

        self._resetDefaultLayoutAction = QtWidgets.QAction()
        self._resetDefaultLayoutAction.triggered.connect(
            lambda: mainWindow.changeLayout(configService.getDefaultLayout()))
        self._layoutEditingAction = QtWidgets.QAction()
        self._layoutEditingAction.setCheckable(True)
        self._layoutEditingAction.setChecked(self._mainWindow.getLayoutEditing())
        self._layoutEditingAction.triggered.connect(self._mainWindow.toggleLayoutEditing)
        self._layoutMenu = QtWidgets.QMenu()
        self._layoutMenu.addAction(self._resetDefaultLayoutAction)
        self._layoutMenu.addAction(self._layoutEditingAction)

        self._pluginsMenu = QtWidgets.QMenu()

        self._languageMenu = QtWidgets.QMenu()
        self._englishAction = QtWidgets.QAction()
        self._englishAction.triggered.connect(lambda: app.changeLanguage("en_US"))
        self._chineseAction = QtWidgets.QAction()
        self._chineseAction.triggered.connect(lambda: app.changeLanguage("zh_CN"))
        self._languageMenu.addAction(self._englishAction)
        self._languageMenu.addAction(self._chineseAction)

        self._testMenu = QtWidgets.QMenu()
        self._oneKeyAddAction = QtWidgets.QAction()
        self._oneKeyAddAction.triggered.connect(lambda: playlistService.addMusicsFromFolder("~/Music"))
        self._loadTestDataAction = QtWidgets.QAction()
        self._loadTestDataAction.triggered.connect(lambda: playlistService.loadTestData())
        self._toggleLanguageAction = QtWidgets.QAction()
        self._toggleLanguageAction.triggered.connect(
            lambda: app.changeLanguage("zh_CN" if config.language == "en_US" else "en_US"))
        self._testMenu.addAction(self._oneKeyAddAction)
        self._testMenu.addAction(self._loadTestDataAction)
        self._testMenu.addAction(self._toggleLanguageAction)

        return [self._fileMenu, self._viewMenu, self._layoutMenu, self._pluginsMenu, self._languageMenu, self._testMenu]

    def _refreshMenus(self):
        self._fileMenu.setTitle(tt.FileMenu)
        self._openAction.setText(tt.FileMenu_Open)
        self._configAction.setText(tt.FileMenu_Config)

        self._viewMenu.setTitle(tt.ViewMenu)
        self._playlistManagerAction.setText(tt.ViewMenu_PlaylistManager)
        self._layoutMenu.setTitle(tt.LayoutMenu)
        self._resetDefaultLayoutAction.setText(tt.LayoutMenu_Default)
        self._layoutEditingAction.setText(tt.Toolbar_Editing)

        self._pluginsMenu.setTitle(tt.PluginsMenu)
        self._setupPluginsMenu()

        self._languageMenu.setTitle(tt.LanguageMenu)
        self._englishAction.setText(tt.LanguageMenu_English)
        self._chineseAction.setText(tt.LanguageMenu_Chinese)

        self._testMenu.setTitle(tt.TestMenu)
        self._oneKeyAddAction.setText(tt.TestMenu_OneKeyAdd)
        self._loadTestDataAction.setText(tt.TestMenu_LoadTestData)
        self._toggleLanguageAction.setText(tt.TestMenu_ToggleLanguage)

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
