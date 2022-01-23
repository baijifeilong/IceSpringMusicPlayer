# Created by BaiJiFeiLong@gmail.com at 2022/1/23 22:03
import logging

from PySide2 import QtWidgets

import IceSpringControlsPlugin.controlsPluginTranslation as tt
from IceSpringControlsPlugin.controlsWidget import ControlsWidget


class ControlsWidgetConfigWidget(QtWidgets.QWidget):
    def __init__(self, target: ControlsWidget):
        super().__init__()
        self._target = target
        self._widgetConfig = target.getWidgetConfig()
        self._logger = logging.getLogger("controlsWidgetConfig")
        layout = QtWidgets.QFormLayout()
        sizes = [16, 24, 32, 40, 48, 64, 96, 128]
        self._iconSizeLabel = QtWidgets.QLabel(tt.ControlsWidget_IconSize)
        self._iconSizeCombo = QtWidgets.QComboBox()
        self._iconSizeCombo.addItems([str(x) for x in sizes])
        self._iconSizeCombo.setCurrentIndex(sizes.index(self._widgetConfig.iconSize))
        layout.addRow(self._iconSizeLabel, self._iconSizeCombo)
        self._applyButton = QtWidgets.QPushButton(tt.Config_Apply, self)
        self._applyButton.clicked.connect(self._onApply)
        layout.addRow(self._applyButton)
        self.setLayout(layout)

    def _onApply(self) -> None:
        self._logger.info("On apply")
        self._widgetConfig.iconSize = int(self._iconSizeCombo.currentText())
        self._logger.info("> Signal controlsWidget.widgetConfigChanged emitting...")
        self._target.widgetConfigChanged.emit()
        self._logger.info("< Signal controlsWidget.widgetConfigChanged emitted.")
