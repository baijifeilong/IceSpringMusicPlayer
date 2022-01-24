# Created by BaiJiFeiLong@gmail.com at 2022/1/24 17:09
import types
import typing

from PySide2 import QtWidgets

import IceSpringPlaylistPlugin.playlistTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils


class PlaylistPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.PlaylistPlugin_Name

    @classmethod
    def getPluginMenus(cls) -> typing.List[typing.Union[QtWidgets.QAction, QtWidgets.QMenu]]:
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
        action = QtWidgets.QAction(tt.PlaylistManagerWidget_Name)
        action.triggered.connect(lambda: DialogUtils.execWidget(PlaylistManagerWidget(), withOk=True))
        return [action]

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringPlaylistPlugin.playlistWidget import PlaylistWidget
        from IceSpringPlaylistPlugin.playlistManagerWidget import PlaylistManagerWidget
        return {
            tt.PlaylistWidget_Name: lambda: PlaylistWidget(),
            tt.PlaylistManagerWidget_Name: lambda: PlaylistManagerWidget()
        }

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
