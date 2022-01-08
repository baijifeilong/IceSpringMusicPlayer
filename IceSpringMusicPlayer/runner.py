# Created by BaiJiFeiLong@gmail.com at 2022-01-03 12:55:48

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.utils.logUtils import LogUtils


def run() -> None:
    LogUtils.initLogging()
    App().exec_()
