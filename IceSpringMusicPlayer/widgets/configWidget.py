# Created by BaiJiFeiLong@gmail.com at 2022/1/16 8:24
import logging
import typing

from PySide2 import QtWidgets, QtGui

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.common.replaceableMixin import ReplaceableMixin


class ConfigWidget(QtWidgets.QFrame, ReplaceableMixin):
    _logger: logging.Logger
    _app: App
    _config: Config
    _applicationFontButton: QtWidgets.QPushButton
    _applicationFontPreviewLabel: QtWidgets.QLabel
    _lyricFontButton: QtWidgets.QPushButton
    _lyricFontPreviewLabel: QtWidgets.QLabel

    @staticmethod
    def _getQuickBrownFox() -> str:
        return "The quick brown fox jumps over the lazy dog.\n天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。"

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

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        self._logger = logging.getLogger("configsWidget")
        self._app = App.instance()
        self._config = App.instance().getConfig()
        layout = QtWidgets.QFormLayout(self)
        self.setLayout(layout)

        self._applicationFontButton = QtWidgets.QPushButton(self)
        self._applicationFontButton.setText(self._digestFont(self._config.applicationFont))
        self._applicationFontButton.clicked.connect(self._onApplicationFontButtonClicked)
        self._applicationFontPreviewLabel = QtWidgets.QLabel(self._getQuickBrownFox(), self)
        self._applicationFontPreviewLabel.setFont(self._config.applicationFont)
        self._applicationFontLabel = QtWidgets.QLabel(tt.Config_ApplicationFont, self)
        layout.addRow(self._applicationFontLabel, self._applicationFontButton)
        layout.addWidget(self._applicationFontPreviewLabel)

        self._lyricFontButton = QtWidgets.QPushButton(self)
        self._lyricFontButton.setText(self._digestFont(self._config.lyricFont))
        self._lyricFontButton.clicked.connect(self._onLyricFontButtonClicked)
        self._lyricFontPreviewLabel = QtWidgets.QLabel(self._getQuickBrownFox(), self)
        self._lyricFontPreviewLabel.setFont(self._config.lyricFont)
        self._lyricFontLabel = QtWidgets.QLabel(tt.Config_LyricFont, self)
        layout.addRow(self._lyricFontLabel, self._lyricFontButton)
        layout.addWidget(self._lyricFontPreviewLabel)

        sizes = [16, 24, 32, 40, 48, 64, 96, 128]
        self._iconSizeLabel = QtWidgets.QLabel(tt.Config_IconSize, self)
        self._iconSizeCombo = QtWidgets.QComboBox(self)
        self._iconSizeCombo.addItems([str(x) for x in sizes])
        self._iconSizeCombo.setCurrentIndex(sizes.index(self._config.iconSize))
        layout.addRow(self._iconSizeLabel, self._iconSizeCombo)

        self._applyButton = QtWidgets.QPushButton(tt.Config_Apply, self)
        self._applyButton.clicked.connect(self._onApply)
        layout.addRow(self._applyButton)
        self._app.languageChanged.connect(self._onLanguageChanged)

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        self._applicationFontLabel.setText(tt.Config_ApplicationFont)
        self._lyricFontLabel.setText(tt.Config_LyricFont)
        self._iconSizeLabel.setText(tt.Config_IconSize)
        self._applyButton.setText(tt.Config_Apply)

    def _onApplicationFontButtonClicked(self) -> None:
        self._logger.info("On application font button clicked.")
        ok, font = QtWidgets.QFontDialog.getFont(self._applicationFontPreviewLabel.font(), self)
        if not ok:
            self._logger.info("Operation canceled, return")
            return
        self._applicationFontButton.setText(self._digestFont(font))
        self._applicationFontPreviewLabel.setFont(font)

    def _onLyricFontButtonClicked(self) -> None:
        self._logger.info("On lyric font button clicked.")
        ok, font = QtWidgets.QFontDialog.getFont(self._lyricFontPreviewLabel.font(), self)
        if not ok:
            self._logger.info("Operation canceled, return")
            return
        self._lyricFontButton.setText(self._digestFont(font))
        self._lyricFontPreviewLabel.setFont(font)

    def _onApply(self) -> None:
        self._logger.info("On apply")
        self._config.applicationFont = self._applicationFontPreviewLabel.font()
        self._config.lyricFont = self._lyricFontPreviewLabel.font()
        self._config.iconSize = int(self._iconSizeCombo.currentText())
        self._logger.info("> Signal app.pluginConfigChanged emitting...")
        self._app.configChanged.emit()
        self._logger.info("< Signal app.pluginConfigChanged emitted.")
