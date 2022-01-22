# Created by BaiJiFeiLong@gmail.com at 2022-01-03 12:55:48
import logging
import sys

from IceSpringPathLib import Path

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.utils.logUtils import LogUtils


def run() -> None:
    LogUtils.initLogging()
    logging.info("Append plugins folder to sys path")
    sys.path.append(str(Path(__file__).parent / "plugins"))
    App().exec_()
