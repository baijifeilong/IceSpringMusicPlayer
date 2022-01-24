# Created by BaiJiFeiLong@gmail.com at 2022/1/24 10:23
import types
import typing

import IceSpringLyricsPlugin.lyricsTranslation as tt
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class LyricsPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.LyricsPlugin_Name

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringLyricsPlugin.lyricsWidget import LyricsWidget
        return {
            tt.LyricsWidget_Name: lambda: LyricsWidget()
        }

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return super().getPluginConfigClass()

    @classmethod
    def getPluginConfig(cls) -> JsonSupport:
        return super().getPluginConfig()

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True
