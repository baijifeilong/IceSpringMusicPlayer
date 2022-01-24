# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:31
import types
import typing

import IceSpringPluginManagerPlugin.pluginManagerTranslation as tt
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.common.systemPluginMixin import SystemPluginMixin
from IceSpringMusicPlayer.tt import Text


class PluginManagerPlugin(SystemPluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.PluginManagerPlugin_Name

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringPluginManagerPlugin.pluginManagerWidget import PluginManagerWidget
        return {
            tt.PluginManagerWidget_Name: lambda: PluginManagerWidget()
        }

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
