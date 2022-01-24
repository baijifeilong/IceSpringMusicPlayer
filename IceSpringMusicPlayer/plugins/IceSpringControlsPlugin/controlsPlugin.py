# Created by BaiJiFeiLong@gmail.com at 2022/1/23 20:33
import types
import typing

import IceSpringControlsPlugin.controlsTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class ControlsPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.ControlsPlugin_Name

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringControlsPlugin.controlsWidget import ControlsWidget
        return {
            tt.ControlsWidget_Name: lambda: ControlsWidget()
        }

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True
