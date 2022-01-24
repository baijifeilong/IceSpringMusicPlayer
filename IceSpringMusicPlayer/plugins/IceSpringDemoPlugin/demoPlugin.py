# Created by BaiJiFeiLong@gmail.com at 2022/1/21 14:27

import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtCore, QtWidgets

import IceSpringDemoPlugin.demoTranslation as tt
from IceSpringDemoPlugin.demoPluginConfig import DemoPluginConfig
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils
from IceSpringMusicPlayer.utils.signalUtils import SignalUtils


class DemoPlugin(PluginMixin):
    pluginConfigChanged: QtCore.SignalInstance = SignalUtils.createSignal()

    @classmethod
    def getPluginName(cls) -> Text:
        return tt.DemoPlugin_Name

    @classmethod
    def getPluginDescription(cls) -> Text:
        return tt.DemoPlugin_Description

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringDemoPlugin.demoWidget import DemoWidget
        from IceSpringDemoPlugin.demoBetaWidget import DemoBetaWidget
        return {
            tt.DemoWidget_Name: lambda: DemoWidget(),
            tt.DemoBetaWidget_Name: lambda: DemoBetaWidget()
        }

    @classmethod
    def getPluginMenus(cls) -> typing.List[typing.Union[QtWidgets.QAction, QtWidgets.QMenu]]:
        from IceSpringDemoPlugin.demoPluginConfigWidget import DemoPluginConfigWidget
        action = QtWidgets.QAction(tt.DemoPluginMenu_Config)
        action.triggered.connect(lambda: DialogUtils.execWidget(DemoPluginConfigWidget()))
        return [action]

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return DemoPluginConfig

    @classmethod
    def getPluginConfig(cls) -> DemoPluginConfig:
        return gg(super().getPluginConfig())

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
