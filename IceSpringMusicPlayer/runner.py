# Created by BaiJiFeiLong@gmail.com at 2022-01-03 12:55:48
__import__("os").environ.update(dict(
    QT_API="PySide2".lower(),
    QT_MULTIMEDIA_PREFERRED_PLUGINS='DirectShow'.lower()
))

import sys

import numpy as np
from IceSpringPathLib import Path


def run() -> None:
    from IceSpringMusicPlayer.utils.logUtils import LogUtils
    from IceSpringMusicPlayer.utils.pydubUtils import PydubUtils
    np.seterr(divide="ignore")
    LogUtils.initLogging()
    PydubUtils.patchPydub()
    sys.path.append(str(Path(__file__).parent / "plugins"))
    from IceSpringMusicPlayer.app import App
    App().exec_()
