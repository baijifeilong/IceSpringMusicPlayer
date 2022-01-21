# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.emptyPluginWidget import EmptyPluginWidget
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget


class PluginMixin(object):
    @classmethod
    def getPluginName(cls) -> Text:
        return Text.of(cls.__name__)

    @classmethod
    def getPluginDescription(cls) -> Text:
        return Text.of(f"This is {cls.getPluginName()}")

    @classmethod
    def getPluginWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        return [EmptyPluginWidget]

    @classmethod
    def getPluginMainMenu(cls, parentMenu: QtWidgets.QMenu, parentWidget: QtWidgets.QWidget) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(cls.getPluginName(), parentMenu)
        menu.addAction(tt.Menu_Plugins_AboutPlugin,
            lambda: QtWidgets.QMessageBox.information(parentWidget, tt.Menu_Plugins_AboutPlugin,
                cls.getPluginDescription()))
        return menu

    @classmethod
    def getPluginLayoutMenu(cls, parentMenu: QtWidgets.QMenu, maskWidget: MaskWidget) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(cls.getPluginName(), parentMenu)
        for clazz in cls.getPluginWidgetClasses():
            menu.addAction(f"Replace By {clazz.getWidgetName()}",
                lambda clazz=clazz: maskWidget.doReplace(lambda: gg(clazz)(None, None)))
        return menu

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return JsonSupport

    @classmethod
    def getPluginConfig(cls) -> JsonSupport:
        return App.instance().getConfig().plugins[".".join((cls.__module__, cls.__name__))]

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt
