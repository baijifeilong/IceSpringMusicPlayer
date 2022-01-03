__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

from iceSpringMusicPlayer.app import App
from iceSpringMusicPlayer.utils import LogUtils


def run() -> None:
    LogUtils.initLogging()
    App().exec_()
