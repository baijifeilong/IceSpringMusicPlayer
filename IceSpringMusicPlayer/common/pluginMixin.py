# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.emptyJsonSupport import EmptyJsonSupport
from IceSpringMusicPlayer.common.emptyPluginWidget import EmptyPluginWidget
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.widgets.maskWidget import MaskWidget


class PluginMixin(object):
    @classmethod
    def getName(cls) -> Text:
        return Text.of(cls.__name__)

    @classmethod
    def getDescription(cls) -> Text:
        return Text.of(f"This is {cls.getName()}")

    @classmethod
    def getWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        return [EmptyPluginWidget]

    @classmethod
    def getMainMenu(cls, parentMenu: QtWidgets.QMenu, parentWidget: QtWidgets.QWidget) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(cls.getName(), parentMenu)
        menu.addAction(tt.Menu_Plugins_AboutPlugin,
            lambda: QtWidgets.QMessageBox.information(parentWidget, tt.Menu_Plugins_AboutPlugin, cls.getDescription()))
        return menu

    @classmethod
    def getLayoutMenu(cls, parentMenu: QtWidgets.QMenu, maskWidget: MaskWidget) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(cls.getName(), parentMenu)
        for clazz in cls.getWidgetClasses():
            menu.addAction(f"Replace By {clazz.getName()}",
                lambda clazz=clazz: maskWidget.doReplace(lambda: gg(clazz)(None, None)))
        return menu

    @classmethod
    def getPluginConfigClass(cls) -> typing.Type[JsonSupport]:
        return EmptyJsonSupport

    @classmethod
    def getPluginConfig(cls) -> JsonSupport:
        return App.instance().getConfig().plugins[".".join((cls.__module__, cls.__name__))]

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt
