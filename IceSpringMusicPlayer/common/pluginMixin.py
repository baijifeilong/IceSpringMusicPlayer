# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import types
import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.stringUtils import StringUtils


class PluginMixin(object):
    @classmethod
    def getPluginName(cls) -> Text:
        return Text.of(StringUtils.camelToTitle(cls.__name__))

    @classmethod
    def getPluginVersion(cls) -> str:
        return "0.0.1"

    @classmethod
    def getPluginDescription(cls) -> Text:
        return tt.Plugins_ThisIs.format(cls.getPluginName())

    @classmethod
    def getPluginMenus(cls) -> typing.List[typing.Union[QtWidgets.QAction, QtWidgets.QMenu]]:
        return []

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        return dict()

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return JsonSupport

    @classmethod
    def getPluginConfig(cls) -> JsonSupport:
        from IceSpringMusicPlayer.app import App
        plugins = App.instance().getConfig().plugins
        for plugin in plugins:
            if plugin.clazz == cls:
                return plugin.config
        raise RuntimeError("Impossible")

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt

    @classmethod
    def isSystemPlugin(cls) -> bool:
        from IceSpringMusicPlayer.common.systemPluginMixin import SystemPluginMixin
        return issubclass(cls, SystemPluginMixin)
