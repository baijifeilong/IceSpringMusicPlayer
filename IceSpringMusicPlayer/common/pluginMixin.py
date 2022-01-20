# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01

from __future__ import annotations

import abc
import typing

from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PluginMeta(type(QtCore.QObject), abc.ABCMeta):
    pass


class PluginMixin(ReplaceableMixin, metaclass=PluginMeta):
    @classmethod
    def id(cls) -> str:
        return cls.__name__

    @classmethod
    def name(cls) -> Text:
        return Text.of(cls.id())

    @classmethod
    def replaceableWidgets(cls: typing.Type[typing.Union[PluginMixin, QtWidgets.QWidget]]) \
            -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        return {
            cls.name(): lambda parent: cls(parent)
        }
