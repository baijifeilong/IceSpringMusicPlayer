# Created by BaiJiFeiLong@gmail.com at 2022/1/23 20:33
import types
import typing

import IceSpringControlsPlugin.controlsPluginTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class ControlsPlugin(PluginMixin):
    @classmethod
    def getPluginWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        from IceSpringControlsPlugin.controlsWidget import ControlsWidget
        return [ControlsWidget]

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
