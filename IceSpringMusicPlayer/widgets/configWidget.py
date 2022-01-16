# Created by BaiJiFeiLong@gmail.com at 2022/1/16 8:24
import logging

from PySide2 import QtWidgets

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.domains.config import Config
from IceSpringMusicPlayer.widgets.replacerMixin import ReplacerMixin


class ConfigWidget(QtWidgets.QFrame, ReplacerMixin):
    _logger: logging.Logger
    _app: App
    _config: Config
    _fontSizeEdit: QtWidgets.QLineEdit
    _lyricsSizeEdit: QtWidgets.QLineEdit

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
        saveButton = QtWidgets.QPushButton("Save", self)
        saveButton.clicked.connect(self._onSave)
        layout.addRow(saveButton)

    def _onSave(self) -> None:
        self._logger.info("On save")
        self._config.fontSize = int(self._fontSizeEdit.text())
        self._config.lyricSize = int(self._lyricsSizeEdit.text())
        self._logger.info("> Signal app.configChanged emitting...")
        self._app.configChanged.emit()
        self._logger.info("< Signal app.configChanged emitted.")
