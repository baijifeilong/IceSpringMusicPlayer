# Created by BaiJiFeiLong@gmail.com at 2022/1/16 8:24
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.utils.fontUtils import FontUtils
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils


class ConfigDialog(QtWidgets.QDialog):
    _logger: logging.Logger
    _app: App
    _config: Config
    _applicationFontButton: QtWidgets.QPushButton
    _applicationFontPreviewLabel: QtWidgets.QLabel

    def __init__(self):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self._logger = logging.getLogger("configDialog")
        self._app = App.instance()
        self._config = App.instance().getConfig()
        self._applicationFontLabel = QtWidgets.QLabel(tt.Config_ApplicationFont)
        self._applicationFontButton = QtWidgets.QPushButton()
        self._applicationFontButton.setText(FontUtils.digestFont(self._config.applicationFont))
        self._applicationFontPreviewLabel = QtWidgets.QLabel(tt.Config_QuickBrownFox)
        self._applicationFontPreviewLabel.setFont(self._config.applicationFont)
        applicationFontLayout = QtWidgets.QVBoxLayout()
        applicationFontLayout.addWidget(self._applicationFontButton)
        applicationFontLayout.addWidget(self._applicationFontPreviewLabel)
        self._buttonBox = WidgetUtils.createButtonBox(ok=True, cancel=True, apply=True)
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 2)
        mainLayout.addWidget(self._applicationFontLabel)
        mainLayout.addLayout(applicationFontLayout, mainLayout.rowCount() - 1, mainLayout.columnCount() - 1)
        mainLayout.addWidget(WidgetUtils.createExpandingSpacer(), mainLayout.rowCount(), 0, 1, 2)
        mainLayout.addWidget(self._buttonBox, mainLayout.rowCount(), 0, 1, 2)
        self._applicationFontButton.clicked.connect(self._onApplicationFontButtonClicked)
        self._buttonBox.clicked.connect(self._onButtonBoxClicked)
        self.setLayout(mainLayout)
        self.resize(854, 480)

    def _onButtonBoxClicked(self, button: QtWidgets.QPushButton) -> None:
        role = self._buttonBox.buttonRole(button)
        if role in [QtWidgets.QDialogButtonBox.ApplyRole, QtWidgets.QDialogButtonBox.AcceptRole]:
            self._config.applicationFont = self._applicationFontPreviewLabel.font()
            self._logger.info("> Signal app.pluginConfigChanged emitting...")
            self._app.configChanged.emit()
            self._logger.info("< Signal app.pluginConfigChanged emitted.")
        if role in [QtWidgets.QDialogButtonBox.AcceptRole, QtWidgets.QDialogButtonBox.RejectRole]:
            self.close()

    def _onApplicationFontButtonClicked(self) -> None:
        self._logger.info("On application font button clicked.")
        _, font = QtWidgets.QFontDialog.getFont(self._applicationFontPreviewLabel.font(), self)
        self._applicationFontButton.setText(FontUtils.digestFont(font))
        self._applicationFontPreviewLabel.setFont(font)
