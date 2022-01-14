# Created by BaiJiFeiLong@gmail.com at 2022/1/13 9:49

from PySide2.QtCore import QObject


class Config(QObject):
    _miniMode: bool
    _zoom: float

    def __init__(self):
        super().__init__()
        self._miniMode = True
        self._zoom = 0.75

    def getMiniMode(self) -> bool:
        return self._miniMode

    def getZoom(self) -> float:
        return self._zoom
