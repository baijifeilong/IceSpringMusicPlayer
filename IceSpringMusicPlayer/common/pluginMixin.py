# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import abc
import typing

from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PluginMixin(ReplaceableMixin, metaclass=abc.ABCMeta):
    class Meta(type(QtCore.QObject), abc.ABCMeta):
        pass

    @classmethod
    def getReplaceableWidgets(cls: typing.Type[typing.Union[PluginMixin, QtWidgets.QWidget]]) \
            -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        return {cls.__name__: lambda parent: cls(parent)}

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
