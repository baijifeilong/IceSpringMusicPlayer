# Created by BaiJiFeiLong@gmail.com at 2022/1/16 8:24
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.replacerMixin import ReplacerMixin
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.utils.fontUtils import FontUtils


class ConfigWidget(QtWidgets.QFrame, ReplacerMixin):
    _logger: logging.Logger
    _app: App
    _config: Config
    _applicationFontButton: QtWidgets.QPushButton
    _applicationFontPreviewLabel: QtWidgets.QLabel
    _lyricFontButton: QtWidgets.QPushButton
    _lyricFontPreviewLabel: QtWidgets.QLabel

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("configsWidget")
        self._app = App.instance()
        self._config = App.instance().getConfig()
        layout = QtWidgets.QFormLayout(self)
        self.setLayout(layout)

        self._applicationFontButton = QtWidgets.QPushButton(self)
        self._applicationFontButton.setText(FontUtils.digestFont(self._config.applicationFont))
        self._applicationFontButton.clicked.connect(self._onApplicationFontButtonClicked)
        self._applicationFontPreviewLabel = QtWidgets.QLabel(tt.Config_QuickBrownFox, self)
        self._applicationFontPreviewLabel.setFont(self._config.applicationFont)
        self._applicationFontLabel = QtWidgets.QLabel(tt.Config_ApplicationFont, self)
        layout.addRow(self._applicationFontLabel, self._applicationFontButton)
        layout.addWidget(self._applicationFontPreviewLabel)

        self._lyricFontButton = QtWidgets.QPushButton(self)
        self._lyricFontButton.setText(FontUtils.digestFont(self._config.lyricFont))
        self._lyricFontButton.clicked.connect(self._onLyricFontButtonClicked)
        self._lyricFontPreviewLabel = QtWidgets.QLabel(tt.Config_QuickBrownFox, self)
        self._lyricFontPreviewLabel.setFont(self._config.lyricFont)
        self._lyricFontLabel = QtWidgets.QLabel(tt.Config_LyricFont, self)
        layout.addRow(self._lyricFontLabel, self._lyricFontButton)
        layout.addWidget(self._lyricFontPreviewLabel)

        self._applyButton = QtWidgets.QPushButton(tt.Config_Apply, self)
        self._applyButton.clicked.connect(self._onApply)
        layout.addRow(self._applyButton)
        self._app.languageChanged.connect(self._onLanguageChanged)

    def _onLanguageChanged(self, language: str):
        self._logger.info("On language changed: %s", language)
        self._applicationFontLabel.setText(tt.Config_ApplicationFont)
        self._applicationFontPreviewLabel.setText(tt.Config_QuickBrownFox)
        self._lyricFontLabel.setText(tt.Config_LyricFont)
        self._applyButton.setText(tt.Config_Apply)

    def _onApplicationFontButtonClicked(self) -> None:
        self._logger.info("On application font button clicked.")
        ok, font = QtWidgets.QFontDialog.getFont(self._applicationFontPreviewLabel.font(), self)
        if not ok:
            self._logger.info("Operation canceled, return")
            return
        self._applicationFontButton.setText(FontUtils.digestFont(font))
        self._applicationFontPreviewLabel.setFont(font)

    def _onLyricFontButtonClicked(self) -> None:
        self._logger.info("On lyric font button clicked.")
        ok, font = QtWidgets.QFontDialog.getFont(self._lyricFontPreviewLabel.font(), self)
        if not ok:
            self._logger.info("Operation canceled, return")
            return
        self._lyricFontButton.setText(FontUtils.digestFont(font))
        self._lyricFontPreviewLabel.setFont(font)

    def _onApply(self) -> None:
        self._logger.info("On apply")
        self._config.applicationFont = self._applicationFontPreviewLabel.font()
        self._config.lyricFont = self._lyricFontPreviewLabel.font()
        self._logger.info("> Signal app.pluginConfigChanged emitting...")
        self._app.configChanged.emit()
        self._logger.info("< Signal app.pluginConfigChanged emitted.")
