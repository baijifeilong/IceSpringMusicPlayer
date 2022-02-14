# Created by BaiJiFeiLong@gmail.com at 2022/1/24 15:49
import logging

from PySide2 import QtWidgets

import IceSpringLyricsPlugin.lyricsTranslation as tt
from IceSpringLyricsPlugin.lyricsWidget import LyricsWidget
from IceSpringMusicPlayer.controls.humanLabel import HumanLabel
from IceSpringMusicPlayer.utils.fontUtils import FontUtils
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils


class LyricsWidgetConfigDialog(QtWidgets.QDialog):
    def __init__(self, target: LyricsWidget):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self._target = target
        self._logger = logging.getLogger("lyricsWidgetConfig")
        self._widgetConfig = self._target.getWidgetConfig()
        self._lyricsFontButton = QtWidgets.QPushButton()
        self._lyricsFontPreviewLabel = HumanLabel()
        self._lyricsFontPreviewLabel.setFont(self._widgetConfig.font)
        lyricsFontLayout = QtWidgets.QVBoxLayout()
        lyricsFontLayout.addWidget(self._lyricsFontButton)
        lyricsFontLayout.addWidget(self._lyricsFontPreviewLabel)
        scrollPolicies = dict(AUTO="Auto", ON="Always On", OFF="Always Off")
        self._horizontalPolicyComboBox = QtWidgets.QComboBox()
        for k, v in scrollPolicies.items():
            self._horizontalPolicyComboBox.addItem(v, k)
        self._horizontalPolicyComboBox.setCurrentText(scrollPolicies[self._widgetConfig.horizontalScrollBarPolicy])
        self._verticalPolicyComboBox = QtWidgets.QComboBox()
        for k, v in scrollPolicies.items():
            self._verticalPolicyComboBox.addItem(v, k)
        self._verticalPolicyComboBox.setCurrentText(scrollPolicies[self._widgetConfig.verticalScrollBarPolicy])
        self._buttonBox = WidgetUtils.createButtonBox(ok=True, cancel=True, apply=True)
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 2)
        mainLayout.addWidget(QtWidgets.QLabel(tt.LyricsWidget_Font))
        mainLayout.addLayout(lyricsFontLayout, mainLayout.rowCount() - 1, mainLayout.columnCount() - 1)
        mainLayout.addWidget(QtWidgets.QLabel(tt.LyricsWidget_HorizontalScrollBarPolicy))
        mainLayout.addWidget(self._horizontalPolicyComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.LyricsWidget_VerticalScrollBarPolicy))
        mainLayout.addWidget(self._verticalPolicyComboBox)
        mainLayout.addWidget(WidgetUtils.createExpandingSpacer(), mainLayout.rowCount(), 0, 1, 2)
        mainLayout.addWidget(self._buttonBox, mainLayout.rowCount(), 0, 1, 2)
        self.setLayout(mainLayout)
        self.resize(854, 480)
        self._refreshView()
        self._lyricsFontButton.clicked.connect(self._onLyricFontButtonClicked)
        self._buttonBox.clicked.connect(self._onButtonBoxClicked)

    def _onButtonBoxClicked(self, button: QtWidgets.QPushButton) -> None:
        self._logger.info("On button box clicked")
        role = self._buttonBox.buttonRole(button)
        if role in [QtWidgets.QDialogButtonBox.ApplyRole, QtWidgets.QDialogButtonBox.AcceptRole]:
            self._widgetConfig.font = self._lyricsFontPreviewLabel.font()
            self._widgetConfig.horizontalScrollBarPolicy = self._horizontalPolicyComboBox.currentData()
            self._widgetConfig.verticalScrollBarPolicy = self._verticalPolicyComboBox.currentData()
            self._target.widgetConfigChanged.emit()
        if role in [QtWidgets.QDialogButtonBox.AcceptRole, QtWidgets.QDialogButtonBox.RejectRole]:
            self.close()

    def _refreshView(self):
        self._lyricsFontButton.setText(FontUtils.digestFont(self._widgetConfig.font))
        self._lyricsFontPreviewLabel.setText(tt.Config_QuickBrownFox)

    def _onLyricFontButtonClicked(self) -> None:
        self._logger.info("On lyric font button clicked.")
        _, font = QtWidgets.QFontDialog.getFont(self._lyricsFontPreviewLabel.font(), self)
        self._lyricsFontButton.setText(FontUtils.digestFont(font))
        self._lyricsFontPreviewLabel.setFont(font)
