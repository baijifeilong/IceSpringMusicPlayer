# Created by BaiJiFeiLong@gmail.com at 2022/1/20 12:55
import logging

from PySide2 import QtWidgets

from IceSpringDemoWidget.demoWidget import DemoWidget
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class DemoMasterWidget(QtWidgets.QWidget, ReplaceableMixin):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger("demoMasterWidget")
        self._masterConfig = DemoWidget.getMasterConfig()
        layout = QtWidgets.QFormLayout(self)
        self.setLayout(layout)
        increaseButton = QtWidgets.QPushButton("Do Increase", self)
        decreaseButton = QtWidgets.QPushButton("Do Decrease", self)
        self._prefixLabel = QtWidgets.QLabel(f"Prefix: {self._masterConfig.prefix}")
        layout.addRow("Increase Prefix", increaseButton)
        layout.addRow("Decrease Prefix", decreaseButton)
        layout.addRow("Prefix Now", self._prefixLabel)
        self.layout().addWidget(QtWidgets.QLabel("DemoMasterWidget", self))
        increaseButton.clicked.connect(self._onIncreaseButtonClicked)
        decreaseButton.clicked.connect(self._onDecreaseButtonClicked)
        DemoWidget.masterConfigChanged.connect(self._onMasterConfigChanged)

    def _onIncreaseButtonClicked(self):
        self._masterConfig.prefix = "Prefix" + str(int(self._masterConfig.prefix[len("Prefix"):]) + 1)
        self._logger.info("> Signal DemoWidget.masterConfigChanged emitting...")
        DemoWidget.masterConfigChanged.emit()
        self._logger.info("< Signal DemoWidget.masterConfigChanged emitted.")

    def _onDecreaseButtonClicked(self):
        self._masterConfig.prefix = "Prefix" + str(int(self._masterConfig.prefix[len("Prefix"):]) - 1)
        self._logger.info("> Signal DemoWidget.masterConfigChanged emitting...")
        DemoWidget.masterConfigChanged.emit()
        self._logger.info("< Signal DemoWidget.masterConfigChanged emitted.")

    def _onMasterConfigChanged(self):
        self._prefixLabel.setText(f"Prefix: {self._masterConfig.prefix}")
