# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:31
import typing

from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.common.systemPluginMixin import SystemPluginMixin


class PluginManagerPlugin(SystemPluginMixin):

    @classmethod
    def getPluginWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        from IceSpringPluginManagerPlugin.pluginManagerWidget import PluginManagerWidget
        return [PluginManagerWidget]
