# Created by BaiJiFeiLong@gmail.com at 2022/2/22 15:14
import taglib
from IceSpringPathLib import Path
from PySide2 import QtMultimedia, QtCore


class PatchedMediaPlayer(QtMultimedia.QMediaPlayer):
    durationChanged: QtCore.SignalInstance = QtCore.Signal(int)
    positionChanged: QtCore.SignalInstance = QtCore.Signal(int)

    def __init__(self):
        super().__init__()
        self._realDuration = 0
        self._lastFakePosition = 0
        self._bugRate = 0.0
        super().durationChanged.connect(self._onSuperDurationChanged)
        super().positionChanged.connect(self._onSuperPositionChanged)

    def _onSuperDurationChanged(self, duration: int):
        self._bugRate = duration / self._realDuration
        self.durationChanged.emit(self._realDuration)

    def _onSuperPositionChanged(self):
        self.positionChanged.emit(self.position())

    def setMedia(self, media: QtMultimedia.QMediaContent, stream: QtCore.QIODevice = None, realDuration=None) -> None:
        self.blockSignals(True)
        super().setMedia(media, stream)
        self.blockSignals(False)
        self._realDuration = realDuration
        self._lastFakePosition = 0
        self._bugRate = 0.0
        if realDuration is None:
            filename = media.canonicalUrl().toLocalFile()
            file = taglib.File(filename)
            bitrate = file.bitrate
            file.close()
            self._realDuration = Path(filename).stat().st_size * 8 // bitrate

    def setPosition(self, position: int) -> None:
        assert self._bugRate != 0 or position == 0
        fakePosition = int(position * self._bugRate)
        super().setPosition(int(position * self._bugRate))
        self._lastFakePosition = fakePosition

    def duration(self) -> int:
        return self._realDuration

    def position(self) -> int:
        elapsed = super().position() - self._lastFakePosition
        lastPosition = 0 if self._lastFakePosition == 0 else int(self._lastFakePosition / self._bugRate)
        realPosition = lastPosition + elapsed
        realPosition = max(realPosition, 0)
        realPosition = min(realPosition, self._realDuration)
        return realPosition
