# Created by BaiJiFeiLong@gmail.com at 2022/1/20 12:55
import logging

from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtCore

import IceSpringDemoPlugin.demoPluginTranslation as tt
from IceSpringDemoPlugin.demoPlugin import DemoPlugin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class DemoPluginConfigWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent: QtWidgets.QWidget = None, config=None) -> None:
        unused(config)
        super().__init__(parent)
        self._logger = logging.getLogger("demoPluginConfigWidget")
        self._pluginConfig = DemoPlugin.getPluginConfig()
        decreaseButton = QtWidgets.QPushButton("Decrease")
        increaseButton = QtWidgets.QPushButton("Increase")
        self._pluginCounterLabel = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()
        layout.addWidget(decreaseButton, 0, gg(QtCore.Qt.AlignCenter))
        layout.addWidget(self._pluginCounterLabel, 0, gg(QtCore.Qt.AlignCenter))
        layout.addWidget(increaseButton, 0, gg(QtCore.Qt.AlignCenter))
        layout.addStretch()
        self.setLayout(layout)
        increaseButton.clicked.connect(self._onIncreaseButtonClicked)
        decreaseButton.clicked.connect(self._onDecreaseButtonClicked)
        DemoPlugin.pluginConfigChanged.connect(self._onPluginConfigChanged)
        self._refreshWidget()

    def _refreshWidget(self):
        self._pluginCounterLabel.setText(tt.Demo_PluginCounter + str(self._pluginConfig.pluginCounter))

    def _onIncreaseButtonClicked(self):
        self._pluginConfig.pluginCounter += 1
        self._logger.info("> Signal DemoPlugin.pluginConfigChanged emitting...")
        DemoPlugin.pluginConfigChanged.emit()
        self._logger.info("< Signal DemoPlugin.pluginConfigChanged emitted.")

    def _onDecreaseButtonClicked(self):
        self._pluginConfig.pluginCounter -= 1
        self._logger.info("> Signal DemoPlugin.pluginConfigChanged emitting...")
        DemoPlugin.pluginConfigChanged.emit()
        self._logger.info("< Signal DemoPlugin.pluginConfigChanged emitted.")

    def _onPluginConfigChanged(self):
        self._refreshWidget()
