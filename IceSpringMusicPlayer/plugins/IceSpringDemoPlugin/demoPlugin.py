# Created by BaiJiFeiLong@gmail.com at 2022/1/21 14:27

import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore

import IceSpringDemoPlugin.demoPluginTranslation as tt
from IceSpringDemoPlugin.demoPluginConfig import DemoPluginConfig
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.signalUtils import SignalUtils


class DemoPlugin(PluginMixin):
    pluginConfigChanged: QtCore.SignalInstance = SignalUtils.createSignal()

    @classmethod
    def getWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        from IceSpringDemoPlugin.demoWidget import DemoWidget
        from IceSpringDemoPlugin.demoPluginConfigWidget import DemoPluginConfigWidget
        return [DemoWidget, DemoPluginConfigWidget]

    @classmethod
    def getName(cls) -> Text:
        return tt.Demo_Name

    @classmethod
    def getDescription(cls) -> Text:
        return tt.Demo_Description

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return DemoPluginConfig

    @classmethod
    def getPluginConfig(cls) -> DemoPluginConfig:
        return gg(super().getPluginConfig())

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt
