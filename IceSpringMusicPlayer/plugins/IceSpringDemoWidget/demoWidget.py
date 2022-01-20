# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import logging
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringDemoWidget.demoMasterConfig import DemoMasterConfig
from IceSpringDemoWidget.demoSlaveConfig import DemoSlaveConfig
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class DemoWidget(QtWidgets.QWidget, PluginMixin, metaclass=PluginMixin.Meta):
    masterConfigChanged: QtCore.SignalInstance = QtCore.Signal()
    slaveConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    _masterConfig: DemoMasterConfig
    _slaveConfig: DemoSlaveConfig

    def __init__(self, parent: QtWidgets.QWidget, slaveConfig: DemoSlaveConfig = None):
        super().__init__(parent)
        self._logger = logging.getLogger("demoWidget")
        self._masterConfig = gg(self.getMasterConfig())
        self._slaveConfig = slaveConfig or self.getSlaveConfigType().getDefaultInstance()
        self._prefixButton = QtWidgets.QPushButton(self._masterConfig.prefix, self)
        self._suffixButton = QtWidgets.QPushButton(self._slaveConfig.suffix, self)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(self._prefixButton)
        self.layout().addWidget(self._suffixButton)
        self._prefixButton.clicked.connect(self._onPrefixButtonClicked)
        self._suffixButton.clicked.connect(self._onSuffixButtonClicked)
        self.masterConfigChanged.connect(self._onMasterConfigChanged)
        self.slaveConfigChanged.connect(self._onSlaveConfigChanged)

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
    def getReplaceableWidgets(cls: typing.Type[typing.Union[PluginMixin, QtWidgets.QWidget]]) \
            -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        from IceSpringDemoWidget.demoConfigWidget import DemoConfigWidget
        return {
            **super().getReplaceableWidgets(),
            Text.of(en_US="DemoConfigWidget"): lambda parent: DemoConfigWidget(parent)
        }

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
