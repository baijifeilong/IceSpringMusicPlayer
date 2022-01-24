# Created by BaiJiFeiLong@gmail.com at 2022/1/21 21:47
import logging

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

import IceSpringDemoPlugin.demoTranslation as tt
from IceSpringDemoPlugin.demoWidget import DemoWidget


class DemoWidgetConfigWidget(QtWidgets.QWidget):
    def __init__(self, target: DemoWidget) -> None:
        super().__init__()
        self._target = target
        self._logger = logging.getLogger("demoWidgetConfigWidget")
        self._widgetConfig = target.getWidgetConfig()
        increaseButton = QtWidgets.QPushButton("Increase")
        decreaseButton = QtWidgets.QPushButton("Decrease")
        self._widgetCounterLabel = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()
        layout.addWidget(decreaseButton, 0, gg(QtCore.Qt.AlignCenter))
        layout.addWidget(self._widgetCounterLabel, 0, gg(QtCore.Qt.AlignCenter))
        layout.addWidget(increaseButton, 0, gg(QtCore.Qt.AlignCenter))
        layout.addStretch()
        self.setLayout(layout)
        increaseButton.clicked.connect(self._onIncreaseButtonClicked)
        decreaseButton.clicked.connect(self._onDecreaseButtonClicked)
        target.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self._refreshWidget()

    def _refreshWidget(self):
        self._widgetCounterLabel.setText(tt.Demo_WidgetCounter + str(self._widgetConfig.widgetCounter))

    def _onIncreaseButtonClicked(self):
        self._widgetConfig.widgetCounter += 1
        self._logger.info("> Signal demoWidget.widgetConfigChanged emitting...")
        self._target.widgetConfigChanged.emit()
        self._logger.info("< Signal demoWidget.widgetConfigChanged emitted.")

    def _onDecreaseButtonClicked(self):
        self._widgetConfig.widgetCounter -= 1
        self._logger.info("> Signal demoWidget.widgetConfigChanged emitting...")
        self._target.widgetConfigChanged.emit()
        self._logger.info("< Signal demoWidget.widgetConfigChanged emitted.")

    def _onWidgetConfigChanged(self):
        self._refreshWidget()
