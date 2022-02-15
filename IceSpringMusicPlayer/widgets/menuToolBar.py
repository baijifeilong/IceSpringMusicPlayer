# Created by BaiJiFeiLong@gmail.com at 2022/2/15 13:31
from __future__ import annotations

import logging
import typing

from PySide2 import QtGui
from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.windows.configDialog import ConfigDialog

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.windows.mainWindow import MainWindow


class MenuToolBar(QtWidgets.QToolBar):
    _menus: typing.List[QtWidgets.QMenu]

    def __init__(self, mainWindow: MainWindow):
        super().__init__()
        self._logger = logging.getLogger("menuToolBar")
        self._app = App.instance()
        self._config = self._app.getConfig()
        self._mainWindow = mainWindow
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
        self.setStyleSheet("QToolButton::menu-indicator { image: none}")
        self._setupMenus()
        for menu in self._menus:
            button = QtWidgets.QToolButton()
            button.setMenu(menu)
            button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            menu.mouseMoveEvent = lambda event, button=button, menu=menu: self._onMouseMove(menu, event, button)
            menu.setProperty("__button", button)
            self.addWidget(button)

    def _refreshView(self):
        self.setWindowTitle("Menu")
        self._refreshMenus()
        for menu in self._menus:
            button: QtWidgets.QToolButton = menu.property("__button")
            button.setText(button.menu().title())

    def _onMouseMove(self, menu: QtWidgets.QMenu, event: QtGui.QMouseEvent, button: QtWidgets.QToolButton):
        hover = self.childAt(self.mapFromGlobal(QtGui.QCursor.pos()))
        if isinstance(hover, QtWidgets.QToolButton) and hover != button:
            menu.close()
            hover.showMenu()
        else:
            return QtWidgets.QMenu.mouseMoveEvent(menu, event)

    def _setupMenus(self):
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
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
            lambda: self._mainWindow.changeLayout(self._configService.getDefaultLayout()))
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
        self._englishAction.triggered.connect(lambda: self._app.changeLanguage("en_US"))
        self._chineseAction = QtWidgets.QAction()
        self._chineseAction.triggered.connect(lambda: self._app.changeLanguage("zh_CN"))
        self._languageMenu.addAction(self._englishAction)
        self._languageMenu.addAction(self._chineseAction)

        self._testMenu = QtWidgets.QMenu()
        self._oneKeyAddAction = QtWidgets.QAction()
        self._oneKeyAddAction.triggered.connect(lambda: self._playlistService.addMusicsFromFolder("~/Music"))
        self._loadTestDataAction = QtWidgets.QAction()
        self._loadTestDataAction.triggered.connect(lambda: self._playlistService.loadTestData())
        self._toggleLanguageAction = QtWidgets.QAction()
        self._toggleLanguageAction.triggered.connect(
            lambda: self._app.changeLanguage("zh_CN" if self._config.language == "en_US" else "en_US"))
        self._testMenu.addAction(self._oneKeyAddAction)
        self._testMenu.addAction(self._loadTestDataAction)
        self._testMenu.addAction(self._toggleLanguageAction)

        self._menus = [self._fileMenu, self._viewMenu, self._layoutMenu, self._pluginsMenu, self._languageMenu,
            self._testMenu]

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