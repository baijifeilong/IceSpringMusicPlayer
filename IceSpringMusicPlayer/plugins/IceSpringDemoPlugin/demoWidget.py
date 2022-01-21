# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import logging
import types
import typing

from PySide2 import QtWidgets, QtCore

import IceSpringDemoPlugin.demoPluginTranslation as tt
from IceSpringDemoPlugin.demoPlugin import DemoPlugin
from IceSpringDemoPlugin.demoPluginConfig import DemoPluginConfig
from IceSpringDemoPlugin.demoWidgetConfig import DemoWidgetConfig
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class DemoWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    _pluginConfig: DemoPluginConfig
    _widgetConfig: DemoWidgetConfig

    def __init__(self, parent: QtWidgets.QWidget, config: DemoWidgetConfig = None):
        super().__init__(parent)
        self._logger = logging.getLogger("demoWidget")
        self._app = App.instance()
        self._pluginConfig = DemoPlugin.getPluginConfig()
        self._widgetConfig = config or self.getWidgetConfigClass().getDefaultInstance()
        self._prefixButton = QtWidgets.QPushButton(self)
        self._suffixButton = QtWidgets.QPushButton(self)
        self._artistButton = QtWidgets.QPushButton(self)
        self._prefixButton.setText(tt.Demo_Prefix + self._pluginConfig.prefix)
        self._suffixButton.setText(tt.Demo_Suffix + self._widgetConfig.suffix)
        self._artistButton.setText(tt.Music_Artist)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(self._prefixButton)
        self.layout().addWidget(self._suffixButton)
        self.layout().addWidget(self._artistButton)
        self._prefixButton.clicked.connect(self._onPrefixButtonClicked)
        self._suffixButton.clicked.connect(self._onSuffixButtonClicked)
        DemoPlugin.pluginConfigChanged.connect(self._onPluginConfigChanged)
        self.widgetConfigChanged.connect(self._onSlaveConfigChanged)
        self._app.languageChanged.connect(self.onLanguageChanged)

    def onLanguageChanged(self, language: str) -> None:
        self._logger.info("On language changed: %s", language)
        self._prefixButton.setText(tt.Demo_Prefix + self._pluginConfig.prefix)
        self._suffixButton.setText(tt.Demo_Suffix + self._widgetConfig.suffix)
        self._artistButton.setText(tt.Music_Artist)

    def _onPrefixButtonClicked(self) -> None:
        self._logger.info("On prefix button clicked")
        self._pluginConfig.prefix = "Prefix" + str(int(self._pluginConfig.prefix[len("Prefix"):]) + 1)
        self._logger.info("> Signal DemoPlugin.pluginConfigChanged emitting...")
        DemoPlugin.pluginConfigChanged.emit()
        self._logger.info("< Signal DemoPlugin.pluginConfigChanged emitted.")

    def _onSuffixButtonClicked(self) -> None:
        self._logger.info("On suffix button clicked")
        self._widgetConfig.suffix = "Suffix" + str(int(self._widgetConfig.suffix[len("Suffix"):]) + 1)
        self._logger.info("> Signal widgetConfigChanged emitting...")
        self.widgetConfigChanged.emit()
        self._logger.info("> Signal widgetConfigChanged emitted...")

    def _onPluginConfigChanged(self) -> None:
        self._logger.info("On global config changed")
        self._prefixButton.setText(tt.Demo_Prefix + self._pluginConfig.prefix)

    def _onSlaveConfigChanged(self) -> None:
        self._logger.info("On local config changed")
        self._suffixButton.setText(tt.Demo_Suffix + self._widgetConfig.suffix)

    @classmethod
    def getName(cls) -> Text:
        return tt.DemoWidget_Name

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return DemoWidgetConfig

    def getWidgetConfig(self) -> DemoWidgetConfig:
        return self._widgetConfig

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt
