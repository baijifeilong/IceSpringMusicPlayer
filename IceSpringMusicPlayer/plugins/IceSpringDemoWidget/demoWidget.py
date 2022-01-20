# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import logging
import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

import IceSpringDemoWidget.demoTranslation as tt
from IceSpringDemoWidget.demoMasterConfig import DemoMasterConfig
from IceSpringDemoWidget.demoSlaveConfig import DemoSlaveConfig
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.utils.signalUtils import SignalUtils


class DemoWidget(QtWidgets.QWidget, PluginMixin, metaclass=PluginMixin.Meta):
    masterConfigChanged: QtCore.SignalInstance = SignalUtils.createSignal()
    slaveConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    _masterConfig: DemoMasterConfig
    _slaveConfig: DemoSlaveConfig

    def __init__(self, parent: QtWidgets.QWidget, slaveConfig: DemoSlaveConfig = None):
        super().__init__(parent)
        self._logger = logging.getLogger("demoWidget")
        self._app = App.instance()
        self._masterConfig = gg(self.getMasterConfig())
        self._slaveConfig = slaveConfig or self.getSlaveConfigType().getDefaultInstance()
        self._prefixButton = QtWidgets.QPushButton(self)
        self._suffixButton = QtWidgets.QPushButton(self)
        self._artistButton = QtWidgets.QPushButton(self)
        self._prefixButton.setText(tt.Demo_Prefix + self._masterConfig.prefix)
        self._suffixButton.setText(tt.Demo_Suffix + self._slaveConfig.suffix)
        self._artistButton.setText(tt.Music_Artist)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(self._prefixButton)
        self.layout().addWidget(self._suffixButton)
        self.layout().addWidget(self._artistButton)
        self._prefixButton.clicked.connect(self._onPrefixButtonClicked)
        self._suffixButton.clicked.connect(self._onSuffixButtonClicked)
        self.masterConfigChanged.connect(self._onMasterConfigChanged)
        self.slaveConfigChanged.connect(self._onSlaveConfigChanged)
        self._app.languageChanged.connect(self.onLanguageChanged)

    def onLanguageChanged(self, language: str) -> None:
        self._logger.info("On language changed: %s", language)
        self._prefixButton.setText(tt.Demo_Prefix + self._masterConfig.prefix)
        self._suffixButton.setText(tt.Demo_Suffix + self._slaveConfig.suffix)
        self._artistButton.setText(tt.Music_Artist)

    def _onPrefixButtonClicked(self) -> None:
        self._logger.info("On prefix button clicked")
        self._masterConfig.prefix = "Prefix" + str(int(self._masterConfig.prefix[len("Prefix"):]) + 1)
        self._logger.info("> Signal masterConfigChanged emitting...")
        self.masterConfigChanged.emit()
        self._logger.info("< Signal masterConfigChanged emitted.")

    def _onSuffixButtonClicked(self) -> None:
        self._logger.info("On suffix button clicked")
        self._slaveConfig.suffix = "Suffix" + str(int(self._slaveConfig.suffix[len("Suffix"):]) + 1)
        self._logger.info("> Signal slaveConfigChanged emitting...")
        self.slaveConfigChanged.emit()
        self._logger.info("> Signal slaveConfigChanged emitted...")

    def _onMasterConfigChanged(self) -> None:
        self._logger.info("On global config changed")
        self._prefixButton.setText(self._masterConfig.prefix)

    def _onSlaveConfigChanged(self) -> None:
        self._logger.info("On local config changed")
        self._suffixButton.setText(self._slaveConfig.suffix)

    @classmethod
    def getReplaceableWidgets(cls) -> typing.List[PluginMixin.ReplaceableWidget]:
        from IceSpringDemoWidget.demoConfigWidget import DemoConfigWidget
        return super().getReplaceableWidgets() + [
            PluginMixin.ReplaceableWidget("Demo Config Widget", lambda parent: DemoConfigWidget(parent))]

    @classmethod
    def getMasterConfigType(cls) -> typing.Type[JsonSupport]:
        return DemoMasterConfig

    @classmethod
    def getSlaveConfigType(cls) -> typing.Type[JsonSupport]:
        return DemoSlaveConfig

    @classmethod
    def getMasterConfig(cls) -> JsonSupport:
        return super().getMasterConfig()

    def getSlaveConfig(self) -> JsonSupport:
        return self._slaveConfig

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt
