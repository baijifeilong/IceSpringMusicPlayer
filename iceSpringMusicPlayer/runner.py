__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

from iceSpringMusicPlayer.app import App


def run() -> None:
    App().exec_()
