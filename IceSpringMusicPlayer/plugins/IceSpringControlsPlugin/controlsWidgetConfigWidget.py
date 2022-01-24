# Created by BaiJiFeiLong@gmail.com at 2022/1/23 22:03
import logging

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets

import IceSpringControlsPlugin.controlsTranslation as tt
from IceSpringControlsPlugin.controlsWidget import ControlsWidget
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils


class ControlsWidgetConfigWidget(QtWidgets.QWidget):
    def __init__(self, target: ControlsWidget):
        super().__init__()
        self._target = target
        self._widgetConfig = target.getWidgetConfig()
        self._logger = logging.getLogger("controlsWidgetConfig")
        sizes = [16, 24, 32, 40, 48, 64, 96, 128]
        layout = QtWidgets.QGridLayout()
        self._iconSizeLabel = QtWidgets.QLabel(tt.ControlsWidget_IconSize)
        self._iconSizeCombo = QtWidgets.QComboBox()
        self._iconSizeCombo.addItems([str(x) for x in sizes])
        self._iconSizeCombo.setCurrentIndex(sizes.index(self._widgetConfig.iconSize))
        self._buttonBox = QtWidgets.QDialogButtonBox(gg(QtWidgets.QDialogButtonBox.Ok) | gg(
            QtWidgets.QDialogButtonBox.Cancel) | gg(QtWidgets.QDialogButtonBox.Apply))

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.addWidget(self._iconSizeLabel)
        layout.addWidget(self._iconSizeCombo)
        layout.addWidget(WidgetUtils.createExpandingSpacer(), layout.rowCount(), 0, 1, 2)
        layout.addWidget(self._buttonBox, layout.rowCount(), 0, 1, 2)
        self.setLayout(layout)
        self._buttonBox.clicked.connect(self._onButtonBoxClicked)

    def _onButtonBoxClicked(self, button: QtWidgets.QPushButton):
        role = self._buttonBox.buttonRole(button)
        self._logger.info("On button box clicked: %s", role)
        if role == QtWidgets.QDialogButtonBox.ButtonRole.RejectRole:
            QtWidgets.QApplication.activeModalWidget().close()
        elif role == QtWidgets.QDialogButtonBox.ButtonRole.ApplyRole:
            self._doApply()
        else:
            assert role == QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole
            self._doApply()
            QtWidgets.QApplication.activeModalWidget().close()

    def _doApply(self) -> None:
        self._logger.info("Do apply")
        self._widgetConfig.iconSize = int(self._iconSizeCombo.currentText())
        self._logger.info("> Signal controlsWidget.widgetConfigChanged emitting...")
        self._target.widgetConfigChanged.emit()
        self._logger.info("< Signal controlsWidget.widgetConfigChanged emitted.")
