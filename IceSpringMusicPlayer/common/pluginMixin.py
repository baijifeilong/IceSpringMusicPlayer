# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import abc
import dataclasses
import types
import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PluginMixin(ReplaceableMixin, metaclass=abc.ABCMeta):
    class Meta(type(QtCore.QObject), abc.ABCMeta):
        pass

    @dataclasses.dataclass
    class ReplaceableWidget(object):
        title: str
        maker: typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]

    @classmethod
    def getReplaceableWidgets(cls) -> typing.List[PluginMixin.ReplaceableWidget]:
        return [cls.ReplaceableWidget(cls.__name__, lambda parent: gg(cls)(parent))]

    @classmethod
    def getPluginName(cls) -> Text:
        return Text.of(cls.__name__)

    @classmethod
    def getPluginDescription(cls) -> Text:
        return Text.of(f"This is {cls.getPluginName()}")

    @classmethod
    def getPluginActions(cls, parentMenu: QtWidgets.QMenu, parentWidget: QtWidgets.QWidget):
        action = QtWidgets.QAction(tt.Menu_Plugins_AboutPlugin, parentMenu)
        action.triggered.connect(
            lambda: QtWidgets.QMessageBox.information(parentWidget, action.text(), cls.getPluginDescription()))
        return [action]

    @classmethod
    def getMasterConfigType(cls) -> typing.Type[JsonSupport]:
        return NoConfig

    @classmethod
    def getSlaveConfigType(cls) -> typing.Type[JsonSupport]:
        return NoConfig

    @classmethod
    def getMasterConfig(cls) -> JsonSupport:
        return App.instance().getConfig().plugins[".".join((cls.__module__, cls.__name__))]

    def getSlaveConfig(self) -> JsonSupport:
        return self.getSlaveConfigType().getDefaultInstance()

    @classmethod
    def getTranslationModule(cls) -> types.ModuleType:
        return tt


class NoConfig(JsonSupport):
    @classmethod
    def pythonToJson(cls, obj: typing.Any) -> typing.Any:
        return super().pythonToJson(obj)

    @classmethod
    def jsonToPython(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        return super().jsonToPython(pairs)

    @classmethod
    def getDefaultInstance(cls) -> JsonSupport:
        return super().getDefaultInstance()
