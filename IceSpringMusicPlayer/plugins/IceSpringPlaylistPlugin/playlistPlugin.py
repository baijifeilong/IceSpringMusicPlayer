# Created by BaiJiFeiLong@gmail.com at 2022/1/24 17:09
import types
import typing

from PySide2 import QtWidgets

import IceSpringPlaylistPlugin.playlistTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class PlaylistPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.PlaylistPlugin_Name

    @classmethod
    def getPluginMenus(cls) -> typing.List[typing.Union[QtWidgets.QAction, QtWidgets.QMenu]]:
        return super().getPluginMenus()

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringPlaylistPlugin.playlistWidget import PlaylistWidget
        return {tt.PlaylistWidget_Name: lambda: PlaylistWidget()}

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
