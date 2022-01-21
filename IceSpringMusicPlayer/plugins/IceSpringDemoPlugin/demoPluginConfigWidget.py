# Created by BaiJiFeiLong@gmail.com at 2022/1/20 12:55
import logging

from IceSpringRealOptional.typingUtils import unused
from PySide2 import QtWidgets

from IceSpringDemoPlugin.demoPlugin import DemoPlugin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class DemoPluginConfigWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent: QtWidgets.QWidget, config) -> None:
        unused(config)
        super().__init__(parent)
        self._logger = logging.getLogger("demoMasterWidget")
        self._pluginConfig = DemoPlugin.getPluginConfig()
        layout = QtWidgets.QFormLayout(self)
        self.setLayout(layout)
        increaseButton = QtWidgets.QPushButton("Do Increase", self)
        decreaseButton = QtWidgets.QPushButton("Do Decrease", self)
        self._prefixLabel = QtWidgets.QLabel(f"Prefix: {self._pluginConfig.prefix}")
        layout.addRow("Increase Prefix", increaseButton)
        layout.addRow("Decrease Prefix", decreaseButton)
        layout.addRow("Prefix Now", self._prefixLabel)
        self.layout().addWidget(QtWidgets.QLabel("DemoPluginConfigWidget", self))
        increaseButton.clicked.connect(self._onIncreaseButtonClicked)
        decreaseButton.clicked.connect(self._onDecreaseButtonClicked)
        DemoPlugin.pluginConfigChanged.connect(self._onPluginConfigChanged)

    def _onIncreaseButtonClicked(self):
        self._pluginConfig.prefix = "Prefix" + str(int(self._pluginConfig.prefix[len("Prefix"):]) + 1)
        self._logger.info("> Signal DemoPlugin.pluginConfigChanged emitting...")
        DemoPlugin.pluginConfigChanged.emit()
        self._logger.info("< Signal DemoPlugin.pluginConfigChanged emitted.")

    def _onDecreaseButtonClicked(self):
        self._pluginConfig.prefix = "Prefix" + str(int(self._pluginConfig.prefix[len("Prefix"):]) - 1)
        self._logger.info("> Signal DemoPlugin.pluginConfigChanged emitting...")
        DemoPlugin.pluginConfigChanged.emit()
        self._logger.info("< Signal DemoPlugin.pluginConfigChanged emitted.")

    def _onPluginConfigChanged(self):
        self._prefixLabel.setText(f"Prefix: {self._pluginConfig.prefix}")
