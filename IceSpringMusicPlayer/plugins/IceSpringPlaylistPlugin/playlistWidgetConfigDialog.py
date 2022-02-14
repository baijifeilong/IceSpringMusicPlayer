# Created by BaiJiFeiLong@gmail.com at 2022/2/14 14:54
import logging

from PySide2 import QtWidgets

import IceSpringPlaylistPlugin.playlistTranslation as tt
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils
from IceSpringPlaylistPlugin.playlistWidget import PlaylistWidget


class PlaylistWidgetConfigDialog(QtWidgets.QDialog):
    def __init__(self, target: PlaylistWidget):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self._target = target
        self._logger = logging.getLogger("playlistWidget")
        self._widgetConfig = target.getWidgetConfig()
        self._buttonBox = WidgetUtils.createButtonBox(ok=True, cancel=True, apply=True)
        self._rowHeightComboBox = QtWidgets.QComboBox()
        self._rowHeightComboBox.addItems(list(map(str, range(1, 101, 1))))
        self._rowHeightComboBox.setCurrentText(str(self._widgetConfig.rowHeight))
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 2)
        mainLayout.addWidget(QtWidgets.QLabel(tt.PlaylistWidget_RowHeight))
        mainLayout.addWidget(self._rowHeightComboBox)
        mainLayout.addWidget(WidgetUtils.createExpandingSpacer(), mainLayout.rowCount(), 0, 1, 2)
        mainLayout.addWidget(self._buttonBox, mainLayout.rowCount(), 0, 1, 2)
        self.setLayout(mainLayout)
        self.resize(854, 480)
        self._buttonBox.clicked.connect(self._onButtonBoxClicked)

    def _onButtonBoxClicked(self, button: QtWidgets.QPushButton) -> None:
        self._logger.info("On button box clicked")
        role = self._buttonBox.buttonRole(button)
        if role in [QtWidgets.QDialogButtonBox.ApplyRole, QtWidgets.QDialogButtonBox.AcceptRole]:
            self._widgetConfig.rowHeight = int(self._rowHeightComboBox.currentText())
            self._target.widgetConfigChanged.emit()
        if role in [QtWidgets.QDialogButtonBox.AcceptRole, QtWidgets.QDialogButtonBox.RejectRole]:
            self.close()
