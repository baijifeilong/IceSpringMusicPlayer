# Created by BaiJiFeiLong@gmail.com at 2022/1/16 8:24
import logging

from PySide2 import QtWidgets, QtGui

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class ConfigWidget(QtWidgets.QFrame, ReplaceableMixin):
    _logger: logging.Logger
    _app: App
    _config: Config
    _fontSizeEdit: QtWidgets.QLineEdit
    _lyricsSizeEdit: QtWidgets.QLineEdit
    _applicationFontButton: QtWidgets.QPushButton

    @staticmethod
    def _getQuickBrownFox() -> str:
        return "The quick brown fox jumps over the lazy dog.\n天地玄黄，宇宙洪荒。"

    @staticmethod
    def _digestFont(font: QtGui.QFont) -> str:
        features = [font.family()]
        font.bold() and features.append("Bold")
        font.italic() and features.append("Italic")
        font.underline() and features.append("Underline")
        font.strikeOut() and features.append("Strike Out")
        len(features) == 1 and features.append("Regular")
        features.append(f"{font.pointSize()} pt")
        return " ".join(features)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._logger = logging.getLogger("configsWidget")
        self._app = App.instance()
        self._config = App.instance().getConfig()
        layout = QtWidgets.QFormLayout(self)
        self.setLayout(layout)
        self._fontSizeEdit = QtWidgets.QLineEdit(str(self._config.fontSize), self)
        layout.addRow("Font size", self._fontSizeEdit)
        self._lyricsSizeEdit = QtWidgets.QLineEdit(str(self._config.lyricSize), self)
        layout.addRow("Lyrics size", self._lyricsSizeEdit)
        self._applicationFontButton = QtWidgets.QPushButton(self)
        self._applicationFontButton.setText(self._digestFont(self._config.applicationFont))
        self._applicationFontButton.clicked.connect(self._onApplicationFontButtonClicked)
        self._applicationFontPreviewLabel = QtWidgets.QLabel(self._getQuickBrownFox(), self)
        layout.addRow("Application Font", self._applicationFontButton)
        layout.addWidget(self._applicationFontPreviewLabel)
        applyButton = QtWidgets.QPushButton("Apply", self)
        applyButton.clicked.connect(self._onApply)
        layout.addRow(applyButton)

    def _onApplicationFontButtonClicked(self) -> None:
        self._logger.info("On application font button clicked.")
        ok, font = QtWidgets.QFontDialog.getFont(self._applicationFontPreviewLabel.font(), self)
        if not ok:
            self._logger.info("User canceled, return")
            return
        if ok:
            self._applicationFontButton.setText(self._digestFont(font))
            self._applicationFontPreviewLabel.setFont(font)

    def _onApply(self) -> None:
        self._logger.info("On apply")
        self._config.fontSize = int(self._fontSizeEdit.text())
        self._config.lyricSize = int(self._lyricsSizeEdit.text())
        self._config.applicationFont = self._applicationFontPreviewLabel.font()
        self._logger.info("> Signal app.configChanged emitting...")
        self._app.configChanged.emit()
        self._logger.info("< Signal app.configChanged emitted.")
