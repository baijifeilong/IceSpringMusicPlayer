# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import logging
import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore, QtGui

import IceSpringDemoPlugin.demoTranslation as tt
from IceSpringDemoPlugin.demoPlugin import DemoPlugin
from IceSpringDemoPlugin.demoPluginConfig import DemoPluginConfig
from IceSpringDemoPlugin.demoWidgetConfig import DemoWidgetConfig
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils


class DemoWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    _pluginConfig: DemoPluginConfig
    _widgetConfig: DemoWidgetConfig

    def __init__(self, config=None):
        super().__init__()
        self._logger = logging.getLogger("demoWidget")
        self._app = App.instance()
        self._pluginConfig = DemoPlugin.getPluginConfig()
        self._widgetConfig = config or self.getWidgetConfigClass().getDefaultObject()
        self._pluginCounterLabel = QtWidgets.QLabel()
        self._widgetCounterLabel = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()
        layout.addWidget(self._pluginCounterLabel, 0, gg(QtCore.Qt.AlignCenter))
        layout.addWidget(self._widgetCounterLabel, 0, gg(QtCore.Qt.AlignCenter))
        layout.addStretch()
        self.setLayout(layout)
        DemoPlugin.pluginConfigChanged.connect(self._onPluginConfigChanged)
        self.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self._app.languageChanged.connect(self.onLanguageChanged)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)
        self._refreshWidget()

    def _refreshWidget(self):
        self._pluginCounterLabel.setText(tt.DemoWidget_PluginCounter + str(self._pluginConfig.pluginCounter))
        self._widgetCounterLabel.setText(tt.DemoWidget_WidgetCounter + str(self._widgetConfig.widgetCounter))

    def _onCustomContextMenuRequested(self):
        from IceSpringDemoPlugin.demoPluginConfigWidget import DemoPluginConfigWidget
        from IceSpringDemoPlugin.demoWidgetConfigWidget import DemoWidgetConfigWidget
        menu = QtWidgets.QMenu(self)
        menu.addAction("Plugin Config", lambda: DialogUtils.execWidget(DemoPluginConfigWidget(), withOk=True))
        menu.addAction("Widget Config", lambda: DialogUtils.execWidget(DemoWidgetConfigWidget(self), withOk=True))
        menu.exec_(QtGui.QCursor.pos())

    def onLanguageChanged(self, language: str) -> None:
        self._logger.info("On language changed: %s", language)
        self._refreshWidget()

    def _onPluginConfigChanged(self) -> None:
        self._logger.info("On global config changed")
        self._refreshWidget()

    def _onWidgetConfigChanged(self) -> None:
        self._logger.info("On local config changed")
        self._refreshWidget()

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return DemoWidgetConfig

    def getWidgetConfig(self) -> DemoWidgetConfig:
        return self._widgetConfig

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt
