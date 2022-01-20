# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:01
import abc
import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PluginMixin(object, metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def id(cls) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def name(cls) -> Text:
        pass

    @classmethod
    @abc.abstractmethod
    def replaceableWidgets(cls) -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        pass
